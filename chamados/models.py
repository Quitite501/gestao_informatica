from datetime import timedelta
from django.db import models
from django.conf import settings


class CategoriaChamado(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria de Chamado"
        verbose_name_plural = "Categorias de Chamado"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Chamado(models.Model):
    STATUS_ABERTO = "aberto"
    STATUS_EM_ATENDIMENTO = "em_atendimento"
    STATUS_AGUARDANDO = "aguardando_usuario"
    STATUS_ENCERRADO = "encerrado"

    STATUS_CHOICES = [
        (STATUS_ABERTO, "Aberto"),
        (STATUS_EM_ATENDIMENTO, "Em Atendimento"),
        (STATUS_AGUARDANDO, "Aguardando usuário"),
        (STATUS_ENCERRADO, "Encerrado"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("critica", "Crítica"),
    ]

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="chamados_abertos",
    )
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    categoria = models.ForeignKey(
        CategoriaChamado,
        on_delete=models.PROTECT,
        related_name="chamados",
    )
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default="media")
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_atribuidos",
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ABERTO)
    solucao_tecnica = models.TextField(blank=True, null=True)
    encerrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_encerrados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    encerrado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-criado_em"]
        permissions = [
            ("can_manage_chamados", "Pode gerenciar chamados"),
        ]


    # ------------------------------------------------------------------ SLA
    PRAZO_PADRAO_HORAS = {
        "baixa":   72,
        "media":   48,
        "alta":    24,
        "critica":  4,
    }

    def _obter_horas_sla(self):
        """Retorna o prazo em horas do SLA com base na configuracao."""
        try:
            config = ConfiguracaoSLA.objects.filter(
                prioridade=self.prioridade,
                categoria=self.categoria,
            ).first() or ConfiguracaoSLA.objects.filter(
                prioridade=self.prioridade,
                categoria__isnull=True,
            ).first()
            return config.prazo_horas if config else self.PRAZO_PADRAO_HORAS.get(self.prioridade, 48)
        except Exception:
            return self.PRAZO_PADRAO_HORAS.get(self.prioridade, 48)

    def prazo_sla(self):
        """Retorna o datetime de vencimento do SLA ou None se encerrado."""
        if self.status == self.STATUS_ENCERRADO:
            return None
        from chamados.sla_utils import calcular_vencimento_sla
        horas = self._obter_horas_sla()
        return calcular_vencimento_sla(self.criado_em, horas * 60)

    def percentual_sla(self):
        """Retorna o percentual do prazo ja consumido (0-100). Retorna None se encerrado."""
        from django.utils import timezone as tz
        from chamados.sla_utils import calcular_tempo_util
        if self.status == self.STATUS_ENCERRADO:
            return None
        horas = self._obter_horas_sla()
        total_minutos_sla = horas * 60
        minutos_consumidos = calcular_tempo_util(self.criado_em, tz.now())
        if total_minutos_sla <= 0:
            return 100
        return min(int((minutos_consumidos / total_minutos_sla) * 100), 100)

    def status_sla(self):
        """
        Retorna a situacao atual do SLA:
        encerrado | no_prazo | em_risco | vencido
        """
        if self.status == self.STATUS_ENCERRADO:
            return "encerrado"
        pct = self.percentual_sla()
        if pct is None:
            return "encerrado"
        if pct >= 100:
            return "vencido"
        if pct >= 80:
            return "em_risco"
        return "no_prazo"

    def __str__(self):
        return "Chamado " + str(self.pk) + " - " + self.titulo

    def tem_acoes(self):
        return self.acoes.exists()


class AnexoChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    arquivo = models.FileField(upload_to="chamados/anexos/")
    nome_original = models.CharField(max_length=255, blank=True)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo de Chamado"
        verbose_name_plural = "Anexos de Chamado"
        ordering = ["enviado_em"]

    def __str__(self):
        return "Anexo " + str(self.pk) + " do Chamado " + str(self.chamado_id)


class AcaoChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="acoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acoes_chamado",
    )
    descricao = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ação de Atendimento"
        verbose_name_plural = "Ações de Atendimento"
        ordering = ["criado_em"]

    def __str__(self):
        return "Ação " + str(self.pk) + " do Chamado " + str(self.chamado_id)


class AnexoAcao(models.Model):
    acao = models.ForeignKey(
        AcaoChamado,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    arquivo = models.FileField(upload_to="chamados/acoes/")
    nome_original = models.CharField(max_length=255, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo de Ação"
        verbose_name_plural = "Anexos de Ação"
        ordering = ["enviado_em"]

    def __str__(self):
        return "Anexo da Ação " + str(self.acao_id)


class ConfiguracaoSLA(models.Model):
    PRIORIDADE_CHOICES = [
        ("baixa",   "Baixa"),
        ("media",   "Média"),
        ("alta",    "Alta"),
        ("critica", "Crítica"),
    ]

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
    )
    categoria = models.ForeignKey(
        "CategoriaChamado",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="configuracoes_sla",
        help_text="Deixe em branco para aplicar a regra a todas as categorias desta prioridade.",
    )
    prazo_horas = models.PositiveIntegerField(
        help_text="Prazo em horas para atendimento do chamado.",
    )

    class Meta:
        verbose_name = "Configuração de SLA"
        verbose_name_plural = "Configurações de SLA"
        ordering = ["prioridade", "categoria__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["prioridade", "categoria"],
                name="sla_unico_prioridade_categoria",
            )
        ]

    def __str__(self):
        cat = self.categoria.nome if self.categoria else "Todas as categorias"
        return f"SLA {self.get_prioridade_display()} / {cat} — {self.prazo_horas}h"


class ConfiguracaoExpediente(models.Model):
    """Horário padrão de expediente da serventia."""
    DIA_SEMANA_CHOICES = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    dia_semana = models.IntegerField(
        choices=DIA_SEMANA_CHOICES,
        unique=True,
        help_text="Dia da semana (0=Segunda … 6=Domingo).",
    )
    hora_inicio = models.TimeField(
        help_text="Horário de início do expediente.",
    )
    hora_fim = models.TimeField(
        help_text="Horário de fim do expediente.",
    )
    ativo = models.BooleanField(
        default=True,
        help_text="Desmarque para indicar que não há expediente neste dia.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Expediente"
        verbose_name_plural = "Configurações de Expediente"
        ordering = ["dia_semana"]

    def __str__(self):
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.get_dia_semana_display()} — {self.hora_inicio:%H:%M} às {self.hora_fim:%H:%M} ({status})"


class FeriadoDiaAtipico(models.Model):
    TIPO_CHOICES = [
        ("feriado_nacional", "Feriado nacional"),
        ("feriado_estadual", "Feriado estadual"),
        ("feriado_municipal", "Feriado municipal"),
        ("recesso", "Recesso"),
        ("ponto_facultativo", "Ponto facultativo"),
        ("manutencao", "Manutenção interna"),
        ("dia_atipico_sem_expediente", "Dia atípico sem expediente"),
        ("dia_atipico_com_expediente", "Dia atípico com expediente especial"),
    ]

    data = models.DateField(
        unique=True,
        help_text="Data do feriado ou dia atípico.",
    )
    descricao = models.CharField(
        max_length=255,
        help_text="Descrição do feriado ou evento.",
    )
    tipo = models.CharField(
        max_length=40,
        choices=TIPO_CHOICES,
    )
    contabiliza_sla = models.BooleanField(
        default=False,
        help_text="Marque se o SLA deve ser contabilizado neste dia.",
    )
    hora_inicio_especial = models.TimeField(
        null=True,
        blank=True,
        help_text="Horário de início do expediente especial (apenas para dias atípicos com expediente).",
    )
    hora_fim_especial = models.TimeField(
        null=True,
        blank=True,
        help_text="Horário de fim do expediente especial (apenas para dias atípicos com expediente).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feriados_cadastrados",
        help_text="Usuário que cadastrou este registro.",
    )

    class Meta:
        verbose_name = "Feriado / Dia Atípico"
        verbose_name_plural = "Feriados / Dias Atípicos"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.data:%d/%m/%Y} — {self.descricao} ({self.get_tipo_display()})"
