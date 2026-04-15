from django.contrib import admin
from .models import CategoriaChamado, Chamado, AnexoChamado, AcaoChamado, AnexoAcao


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
