"""
Funções centrais de cálculo de SLA por tempo útil de expediente.

Regras:
- Contabiliza apenas minutos dentro do horário de expediente configurado.
- Ignora finais de semana inativos, feriados e dias atípicos sem expediente.
- Considera horários especiais de dias atípicos com expediente.
- Se não houver expediente cadastrado, faz fallback para cálculo por horas corridas.
"""

from datetime import datetime, timedelta, time, date
from typing import Optional, Tuple


def _obter_expediente_do_dia(dia: date) -> Optional[Tuple[time, time]]:
    """
    Retorna (hora_inicio, hora_fim) do expediente para um dia específico.
    Considera feriados/dias atípicos primeiro, depois o expediente padrão.
    Retorna None se não houver expediente naquele dia.
    """
    from chamados.models import FeriadoDiaAtipico, ConfiguracaoExpediente

    # 1. Verificar se existe feriado/dia atípico para esta data
    feriado = FeriadoDiaAtipico.objects.filter(data=dia).first()
    if feriado:
        if not feriado.contabiliza_sla:
            return None  # Dia sem expediente
        if feriado.hora_inicio_especial and feriado.hora_fim_especial:
            return (feriado.hora_inicio_especial, feriado.hora_fim_especial)
        # contabiliza_sla=True mas sem horário especial: usa expediente padrão

    # 2. Consultar expediente padrão do dia da semana
    dia_semana = dia.weekday()  # 0=Segunda ... 6=Domingo
    config = ConfiguracaoExpediente.objects.filter(
        dia_semana=dia_semana, ativo=True
    ).first()

    if config:
        return (config.hora_inicio, config.hora_fim)

    return None  # Sem expediente (ex: fim de semana inativo)


def _tem_expediente_cadastrado() -> bool:
    """Verifica se existe ao menos uma configuração de expediente ativa."""
    from chamados.models import ConfiguracaoExpediente
    return ConfiguracaoExpediente.objects.filter(ativo=True).exists()


def _minutos_uteis_no_dia(dia: date, hora_ini: time, hora_fim: time,
                          exp_ini: time, exp_fim: time) -> int:
    """
    Calcula minutos úteis entre hora_ini e hora_fim,
    limitados ao expediente exp_ini/exp_fim.
    """
    # Interseção dos intervalos
    inicio_efetivo = max(hora_ini, exp_ini)
    fim_efetivo = min(hora_fim, exp_fim)

    if inicio_efetivo >= fim_efetivo:
        return 0

    delta = datetime.combine(dia, fim_efetivo) - datetime.combine(dia, inicio_efetivo)
    return int(delta.total_seconds() // 60)


def calcular_vencimento_sla(data_hora_inicio: datetime, minutos_sla: int) -> datetime:
    """
    Calcula a data/hora de vencimento do SLA considerando apenas tempo útil.

    Se não houver expediente cadastrado, faz fallback para cálculo corrido.

    Args:
        data_hora_inicio: Data e hora de abertura do chamado (timezone-aware).
        minutos_sla: Total de minutos de SLA a contabilizar.

    Returns:
        datetime de vencimento do SLA.
    """
    if not _tem_expediente_cadastrado():
        return data_hora_inicio + timedelta(minutes=minutos_sla)

    minutos_restantes = minutos_sla
    dia_atual = data_hora_inicio.date()
    hora_atual = data_hora_inicio.time()
    tz_info = data_hora_inicio.tzinfo

    # Limite de segurança: 365 dias para evitar loop infinito
    dia_limite = dia_atual + timedelta(days=365)

    while minutos_restantes > 0 and dia_atual <= dia_limite:
        expediente = _obter_expediente_do_dia(dia_atual)

        if expediente:
            exp_ini, exp_fim = expediente

            # No primeiro dia, começar a partir da hora atual
            inicio_no_dia = max(hora_atual, exp_ini)

            if inicio_no_dia < exp_fim:
                minutos_disponiveis = _minutos_uteis_no_dia(
                    dia_atual, inicio_no_dia, exp_fim, exp_ini, exp_fim
                )

                if minutos_restantes <= minutos_disponiveis:
                    # SLA vence neste dia
                    vencimento = datetime.combine(
                        dia_atual, inicio_no_dia
                    ) + timedelta(minutes=minutos_restantes)
                    if tz_info:
                        from django.utils import timezone as tz
                        vencimento = tz.make_aware(
                            vencimento, tz_info
                        ) if tz.is_naive(vencimento) else vencimento.replace(tzinfo=tz_info)
                    return vencimento

                minutos_restantes -= minutos_disponiveis

        # Avançar para o próximo dia, começando no início do expediente
        dia_atual += timedelta(days=1)
        hora_atual = time(0, 0)

    # Fallback: se ultrapassou 365 dias, retorna cálculo corrido
    return data_hora_inicio + timedelta(minutes=minutos_sla)


def calcular_tempo_util(data_hora_inicio: datetime,
                        data_hora_fim: datetime) -> int:
    """
    Calcula o total de minutos úteis entre duas datas.

    Se não houver expediente cadastrado, retorna diferença corrida em minutos.

    Args:
        data_hora_inicio: Data/hora de início.
        data_hora_fim: Data/hora de fim.

    Returns:
        Total de minutos úteis consumidos.
    """
    if not _tem_expediente_cadastrado():
        delta = (data_hora_fim - data_hora_inicio).total_seconds()
        return max(0, int(delta // 60))

    if data_hora_fim <= data_hora_inicio:
        return 0

    total_minutos = 0
    dia_atual = data_hora_inicio.date()
    dia_fim = data_hora_fim.date()

    while dia_atual <= dia_fim:
        expediente = _obter_expediente_do_dia(dia_atual)

        if expediente:
            exp_ini, exp_fim = expediente

            # Determinar janela de cálculo no dia
            if dia_atual == data_hora_inicio.date():
                hora_ini_dia = data_hora_inicio.time()
            else:
                hora_ini_dia = time(0, 0)

            if dia_atual == dia_fim:
                hora_fim_dia = data_hora_fim.time()
            else:
                hora_fim_dia = time(23, 59, 59)

            total_minutos += _minutos_uteis_no_dia(
                dia_atual, hora_ini_dia, hora_fim_dia, exp_ini, exp_fim
            )

        dia_atual += timedelta(days=1)

    return total_minutos
