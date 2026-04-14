from django.db import models
from django.conf import settings
from django.utils import timezone


class Software(models.Model):
    TIPO_CHOICES = [
        ("perpétua", "Perpétua"),
        ("assinatura", "Assinatura"),
        ("oem", "OEM"),
        ("freeware", "Freeware"),
        ("opensource", "Open Source"),
        ("outro", "Outro"),
    ]

    nome = models.CharField(max_length=150)
    fabricante = models.CharField(max_length=150, blank=True, null=True)
    versao = models.CharField(max_length=50, blank=True, null=True, verbose_name="Versão")
    tipo_licenca = models.CharField(max_length=20, choices=TIPO_CHOICES, default="perpétua", verbose_name="Tipo de licença")
    controlado = models.BooleanField(default=True, verbose_name="Controlado", help_text="Inclui no relatório de conformidade")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Software"
        verbose_name_plural = "Softwares"
        ordering = ["nome"]
        unique_together = [("nome", "versao", "fabricante")]

    def __str__(self):
        if self.versao:
            return f"{self.nome} {self.versao}"
        return self.nome

    @property
    def total_adquirido(self):
        return self.contratos.aggregate(
            total=models.Sum("quantidade_adquirida")
        )["total"] or 0

    @property
    def total_instalado(self):
        return self.instalacoes.filter(ativo=True).count()

    @property
    def saldo(self):
        return self.total_adquirido - self.total_instalado

    @property
    def situacao(self):
        saldo = self.saldo
        if saldo < 0:
            return "faltam"
        elif saldo > 0:
            return "sobram"
        return "ok"


class LicencaContrato(models.Model):
    software = models.ForeignKey(
        Software,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name="Software",
    )
    nota_fiscal = models.ForeignKey(
        "notas_fiscais.NotaFiscal",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="licencas",
        verbose_name="Nota fiscal",
    )
    quantidade_adquirida = models.PositiveIntegerField(verbose_name="Quantidade adquirida")
    chave_licenca = models.TextField(blank=True, null=True, verbose_name="Chave / licença")
    data_aquisicao = models.DateField(verbose_name="Data de aquisição")
    data_vencimento = models.DateField(blank=True, null=True, verbose_name="Data de vencimento")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="licencas_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrato de Licença"
        verbose_name_plural = "Contratos de Licença"
        ordering = ["-data_aquisicao"]

    def __str__(self):
        return f"{self.software} - {self.quantidade_adquirida} licenças"

    @property
    def status_vencimento(self):
        if not self.data_vencimento:
            return "sem_vencimento"
        hoje = timezone.now().date()
        diff = (self.data_vencimento - hoje).days
        if diff < 0:
            return "vencida"
        elif diff <= 30:
            return "vence_em_breve"
        return "ok"


class InstalacaoSoftware(models.Model):
    software = models.ForeignKey(
        Software,
        on_delete=models.PROTECT,
        related_name="instalacoes",
        verbose_name="Software",
    )
    patrimonio = models.ForeignKey(
        "patrimonio.Patrimonio",
        on_delete=models.CASCADE,
        related_name="softwares_instalados",
        verbose_name="Equipamento",
    )
    data_instalacao = models.DateField(blank=True, null=True, verbose_name="Data de instalação")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True, verbose_name="Instalação ativa")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="instalacoes_registradas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Instalação de Software"
        verbose_name_plural = "Instalações de Software"
        ordering = ["software__nome"]
        unique_together = [("software", "patrimonio")]

    def __str__(self):
        return f"{self.software} em {self.patrimonio.etiqueta}"
