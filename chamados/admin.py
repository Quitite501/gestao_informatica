from django.contrib import admin
from .models import CategoriaChamado, Chamado, AnexoChamado


@admin.register(CategoriaChamado)
class CategoriaChamadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ("pk", "titulo", "solicitante", "categoria", "prioridade", "status", "tecnico", "criado_em")
    list_filter = ("status", "prioridade", "categoria")
    search_fields = ("titulo", "descricao")
    ordering = ("-criado_em",)


@admin.register(AnexoChamado)
class AnexoChamadoAdmin(admin.ModelAdmin):
    list_display = ("pk", "chamado", "enviado_por", "enviado_em")
