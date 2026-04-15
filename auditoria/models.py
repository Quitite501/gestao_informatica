from django.db import models
from django.conf import settings

class RegistroAuditoria(models.Model):
    ACAO_CRIACAO = "criacao"
    ACAO_EDICAO = "edicao"
    ACAO_DESATIVACAO = "desativacao"
    ACAO_ENCERRAMENTO = "encerramento"
    ACAO_REABERTURA = "reabertura"
    ACAO_MOVIMENTACAO = "movimentacao"
    ACAO_LOGIN = "login"
    ACAO_LOGOUT = "logout"
    ACAO_EXCLUSAO = "exclusao"

    ACAO_CHOICES = [
        (ACAO_CRIACAO, "Criação"),
        (ACAO_EDICAO, "Edição"),
        (ACAO_DESATIVACAO, "Desativação"),
        (ACAO_ENCERRAMENTO, "Encerramento"),
        (ACAO_REABERTURA, "Reabertura"),
        (ACAO_MOVIMENTACAO, "Movimentação"),
        (ACAO_LOGIN, "Login"),
        (ACAO_LOGOUT, "Logout"),
        (ACAO_EXCLUSAO, "Exclusão"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="registros_auditoria",
    )
    acao = models.CharField(max_length=30, choices=ACAO_CHOICES)
    modelo_afetado = models.CharField(max_length=100)
    objeto_id = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Auditoria"
        verbose_name_plural = "Registros de Auditoria"
        ordering = ["-criado_em"]

    def __str__(self):
        usuario_str = self.usuario.nome_completo if self.usuario else "Sistema"
        return f"{self.get_acao_display()} em {self.modelo_afetado} por {usuario_str}"
