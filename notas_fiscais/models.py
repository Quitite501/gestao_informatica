from django.db import models
from django.conf import settings


class NotaFiscal(models.Model):
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número")
    fornecedor = models.CharField(max_length=200)
    data_emissao = models.DateField(verbose_name="Data de emissão")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor total")
    arquivo_pdf = models.FileField(upload_to="notas_fiscais/", blank=True, null=True, verbose_name="Arquivo PDF")
    arquivo_xml = models.FileField(upload_to="notas_fiscais/", blank=True, null=True, verbose_name="Arquivo XML")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_fiscais_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ["-data_emissao"]

    def __str__(self):
        return f"NF {self.numero} - {self.fornecedor}"
