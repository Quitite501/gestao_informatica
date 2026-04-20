from datetime import timedelta
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
        (STATUS_EM_ATENDIMENTO, "Em Atendimento"),
        (STATUS_AGUARDANDO, "Aguardando usuário"),
        (STATUS_ENCERRADO, "Encerrado"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("critica", "Crítica"),
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


    # ------------------------------------------------------------------ SLA
    PRAZO_PADRAO_HORAS = {
        "baixa":   72,
        "media":   48,
        "alta":    24,
        "critica":  4,
    }

    def prazo_sla(self):
        """Retorna o datetime de vencimento do SLA ou None se encerrado."""
        if self.status == self.STATUS_ENCERRADO:
            return None
        try:
            config = ConfiguracaoSLA.objects.filter(
                prioridade=self.prioridade,
                categoria=self.categoria,
            ).first() or ConfiguracaoSLA.objects.filter(
                prioridade=self.prioridade,
                categoria__isnull=True,
            ).first()
            horas = config.prazo_horas if config else self.PRAZO_PADRAO_HORAS.get(self.prioridade, 48)
        except Exception:
            horas = self.PRAZO_PADRAO_HORAS.get(self.prioridade, 48)
        return self.criado_em + timedelta(hours=horas)

    def percentual_sla(self):
        """Retorna o percentual do prazo já consumido (0-100). Retorna None se encerrado."""
        from django.utils import timezone as tz
        prazo = self.prazo_sla()
        if prazo is None:
            return None
        total = (prazo - self.criado_em).total_seconds()
        consumido = (tz.now() - self.criado_em).total_seconds()
        if total <= 0:
            return 100
        return min(int((consumido / total) * 100), 100)

    def status_sla(self):
        """
        Retorna a situação atual do SLA:
        encerrado | no_prazo | em_risco | vencido
        """
        if self.status == self.STATUS_ENCERRADO:
            return "encerrado"
        pct = self.percentual_sla()
        if pct is None:
            return "encerrado"
        if pct >= 100:
            return "vencido"
        if pct >= 80:
            return "em_risco"
        return "no_prazo"

    def __str__(self):
        return "Chamado " + str(self.pk) + " - " + self.titulo

    def tem_acoes(self):
        return self.acoes.exists()


class AnexoChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    arquivo = models.FileField(upload_to="chamados/anexos/")
    nome_original = models.CharField(max_length=255, blank=True)
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


class AcaoChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="acoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acoes_chamado",
    )
    descricao = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ação de Atendimento"
        verbose_name_plural = "Ações de Atendimento"
        ordering = ["criado_em"]

    def __str__(self):
        return "Ação " + str(self.pk) + " do Chamado " + str(self.chamado_id)


class AnexoAcao(models.Model):
    acao = models.ForeignKey(
        AcaoChamado,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    arquivo = models.FileField(upload_to="chamados/acoes/")
    nome_original = models.CharField(max_length=255, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo de Ação"
        verbose_name_plural = "Anexos de Ação"
        ordering = ["enviado_em"]

    def __str__(self):
        return "Anexo da Ação " + str(self.acao_id)


class ConfiguracaoSLA(models.Model):
    PRIORIDADE_CHOICES = [
        ("baixa",   "Baixa"),
        ("media",   "Média"),
        ("alta",    "Alta"),
        ("critica", "Crítica"),
    ]

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
    )
    categoria = models.ForeignKey(
        "CategoriaChamado",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="configuracoes_sla",
        help_text="Deixe em branco para aplicar a regra a todas as categorias desta prioridade.",
    )
    prazo_horas = models.PositiveIntegerField(
        help_text="Prazo em horas para atendimento do chamado.",
    )

    class Meta:
        verbose_name = "Configuração de SLA"
        verbose_name_plural = "Configurações de SLA"
        ordering = ["prioridade", "categoria__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["prioridade", "categoria"],
                name="sla_unico_prioridade_categoria",
            )
        ]

    def __str__(self):
        cat = self.categoria.nome if self.categoria else "Todas as categorias"
        return f"SLA {self.get_prioridade_display()} / {cat} — {self.prazo_horas}h"
