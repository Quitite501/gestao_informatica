from django.contrib import admin
from .models import Software, LicencaContrato, InstalacaoSoftware


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ("nome", "fabricante", "versao", "tipo_licenca", "controlado", "ativo")
    search_fields = ("nome", "fabricante")
    list_filter = ("controlado", "ativo", "tipo_licenca")
    ordering = ("nome",)


@admin.register(LicencaContrato)
class LicencaContratoAdmin(admin.ModelAdmin):
    list_display = ("software", "quantidade_adquirida", "data_aquisicao", "data_vencimento", "criado_em")
    search_fields = ("software__nome",)
    list_filter = ("software",)
    ordering = ("-data_aquisicao",)


@admin.register(InstalacaoSoftware)
class InstalacaoSoftwareAdmin(admin.ModelAdmin):
    list_display = ("software", "patrimonio", "data_instalacao", "ativo", "criado_em")
    search_fields = ("software__nome", "patrimonio__etiqueta")
    list_filter = ("ativo", "software")
    ordering = ("software__nome",)
