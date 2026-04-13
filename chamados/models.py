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
        (STATUS_EM_ATENDIMENTO, "Em atendimento"),
        (STATUS_AGUARDANDO, "Aguardando usuario"),
        (STATUS_ENCERRADO, "Encerrado"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Media"),
        ("alta", "Alta"),
        ("critica", "Critica"),
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

    def __str__(self):
        return "Chamado " + str(self.pk) + " - " + self.titulo


class AnexoChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    arquivo = models.FileField(upload_to="chamados/")
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
