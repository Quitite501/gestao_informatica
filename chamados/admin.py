from django.contrib import admin
from .models import ConfiguracaoSLA,  CategoriaChamado, Chamado, AnexoChamado, AcaoChamado, AnexoAcao


@admin.register(CategoriaChamado)
class CategoriaChamadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ("pk", "titulo", "solicitante", "categoria",
                    "prioridade", "status", "tecnico", "criado_em")
    list_filter = ("status", "prioridade", "categoria")
    search_fields = ("titulo", "descricao")
    ordering = ("-criado_em",)


@admin.register(AnexoChamado)
class AnexoChamadoAdmin(admin.ModelAdmin):
    list_display = ("pk", "chamado", "nome_original", "enviado_por", "enviado_em")


@admin.register(AcaoChamado)
class AcaoChamadoAdmin(admin.ModelAdmin):
    list_display = ("pk", "chamado", "autor", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("descricao",)


@admin.register(AnexoAcao)
class AnexoAcaoAdmin(admin.ModelAdmin):
    list_display = ("pk", "acao", "nome_original", "enviado_em")


@admin.register(ConfiguracaoSLA)
class ConfiguracaoSLAAdmin(admin.ModelAdmin):
    list_display  = ("prioridade", "categoria", "prazo_horas")
    list_filter   = ("prioridade",)
    ordering      = ("prioridade", "categoria__nome")


from .models import ConfiguracaoExpediente, FeriadoDiaAtipico, HistoricoRecalculoSLA


@admin.register(ConfiguracaoExpediente)
class ConfiguracaoExpedienteAdmin(admin.ModelAdmin):
    list_display = ("dia_semana", "hora_inicio", "hora_fim", "ativo")
    list_filter = ("ativo",)
    ordering = ("dia_semana",)


@admin.register(FeriadoDiaAtipico)
class FeriadoDiaAtipicoAdmin(admin.ModelAdmin):
    list_display = ("data", "descricao", "tipo", "contabiliza_sla", "criado_por")
    list_filter = ("tipo", "contabiliza_sla")
    search_fields = ("descricao",)
    ordering = ("-data",)


@admin.register(HistoricoRecalculoSLA)
class HistoricoRecalculoSLAAdmin(admin.ModelAdmin):
    list_display = ("chamado", "vencimento_anterior", "vencimento_novo", "data_impactada", "motivo", "recalculado_em")
    list_filter = ("motivo",)
    search_fields = ("chamado__titulo",)
    ordering = ("-recalculado_em",)
