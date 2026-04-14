from django.contrib import admin
from .models import NotaFiscal


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ("numero", "fornecedor", "data_emissao", "valor_total", "criado_em")
    search_fields = ("numero", "fornecedor")
    list_filter = ("data_emissao",)
    ordering = ("-data_emissao",)
