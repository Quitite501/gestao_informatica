from django.db import models
from django.conf import settings


class TipoEquipamento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    aceita_software = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Equipamento"
        verbose_name_plural = "Tipos de Equipamento"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Patrimonio(models.Model):
    STATUS_DISPONIVEL = "disponivel"
    STATUS_EM_USO = "em_uso"
    STATUS_EM_MANUTENCAO = "em_manutencao"
    STATUS_BAIXADO = "baixado"

    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, "Disponivel"),
        (STATUS_EM_USO, "Em uso"),
        (STATUS_EM_MANUTENCAO, "Em manutencao"),
        (STATUS_BAIXADO, "Baixado"),
    ]

    etiqueta = models.CharField(max_length=50, unique=True, verbose_name="Numero da etiqueta")
    numero_serie = models.CharField(max_length=150, blank=True, null=True, verbose_name="Numero de serie")
    tipo = models.ForeignKey(TipoEquipamento, on_delete=models.SET_NULL, null=True, blank=True, related_name="patrimonios", verbose_name="Tipo de equipamento")
    hostname = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hostname")
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descricao")
    setor = models.ForeignKey("usuarios.Setor", on_delete=models.SET_NULL, null=True, blank=True, related_name="patrimonios")
    usuario_atual = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="patrimonios", verbose_name="Usuario atual")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL)
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observacoes")
    nota_fiscal = models.ForeignKey("notas_fiscais.NotaFiscal", on_delete=models.SET_NULL, null=True, blank=True, related_name="patrimonios", verbose_name="Nota fiscal")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="patrimonios_criados", verbose_name="Cadastrado por")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patrimonio"
        verbose_name_plural = "Patrimonios"
        ordering = ["etiqueta"]
        permissions = [
            ("can_manage_patrimonio", "Pode cadastrar e editar patrimonio"),
        ]

    def __str__(self):
        partes = [self.etiqueta]
        if self.hostname:
            partes.append(self.hostname)
        elif self.modelo:
            partes.append(self.modelo)
        elif self.tipo:
            partes.append(str(self.tipo))
        if self.usuario_atual:
            partes.append(f"({self.usuario_atual.nome_completo})")
        return " - ".join(partes) if len(partes) > 1 else self.etiqueta

    def save(self, *args, **kwargs):
        if not self.usuario_atual and self.status == self.STATUS_EM_USO:
            self.status = self.STATUS_DISPONIVEL
        super().save(*args, **kwargs)


class MovimentacaoPatrimonio(models.Model):
    TIPO_ATRIBUICAO = "atribuicao"
    TIPO_DEVOLUCAO = "devolucao"
    TIPO_MANUTENCAO = "manutencao"
    TIPO_RETORNO = "retorno"
    TIPO_BAIXA = "baixa"
    TIPO_TRANSFERENCIA = "transferencia"
    TIPO_OUTRO = "outro"

    TIPO_CHOICES = [
        (TIPO_ATRIBUICAO, "Atribuicao a usuario"),
        (TIPO_DEVOLUCAO, "Devolucao"),
        (TIPO_MANUTENCAO, "Envio para manutencao"),
        (TIPO_RETORNO, "Retorno de manutencao"),
        (TIPO_BAIXA, "Baixa"),
        (TIPO_TRANSFERENCIA, "Transferencia de setor"),
        (TIPO_OUTRO, "Outro"),
    ]

    patrimonio = models.ForeignKey(Patrimonio, on_delete=models.CASCADE, related_name="movimentacoes")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    usuario_anterior = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes_saida")
    setor_anterior = models.ForeignKey("usuarios.Setor", on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes_saida")
    status_anterior = models.CharField(max_length=20, blank=True, null=True)
    usuario_novo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes_entrada")
    setor_novo = models.ForeignKey("usuarios.Setor", on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes_entrada")
    status_novo = models.CharField(max_length=20, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="movimentacoes_registradas")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimentacao"
        verbose_name_plural = "Movimentacoes"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.patrimonio.etiqueta} - {self.get_tipo_display()}"



class ComputadorEspecificacao(models.Model):
    """Especificações técnicas de computadores (workstations/desktops)."""
    patrimonio = models.OneToOneField(
        Patrimonio,
        on_delete=models.CASCADE,
        related_name="especificacao_computador",
        verbose_name="Patrimônio",
    )
    hostname = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Hostname",
        help_text="Nome da máquina na rede",
    )
    ram_gb = models.PositiveIntegerField(
        verbose_name="RAM (GB)",
        null=True,
        blank=True,
    )
    sistema_operacional = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Sistema Operacional",
        help_text="Ex: Windows 11 Pro, Ubuntu 22.04",
    )
    endereco_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP",
    )
    endereco_mac = models.CharField(
        max_length=17,
        null=True,
        blank=True,
        verbose_name="Endereço MAC",
        unique=True,
        help_text="Formato: XX:XX:XX:XX:XX:XX",
    )
    processador = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Processador",
        help_text="Ex: Intel Core i7-12700K, AMD Ryzen 7 5800X",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Especificação de Computador"
        verbose_name_plural = "Especificações de Computador"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Especificação — {self.patrimonio.etiqueta}"
