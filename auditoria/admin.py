from django.contrib import admin
from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "acao", "modelo_afetado", "objeto_id", "ip")
    list_filter = ("acao", "modelo_afetado")
    search_fields = ("usuario__nome_completo", "descricao")
    ordering = ("-criado_em",)
    readonly_fields = ("usuario", "acao", "modelo_afetado", "objeto_id",
                       "descricao", "ip", "criado_em")
