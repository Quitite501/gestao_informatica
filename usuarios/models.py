#from django.db import models
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Setor(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    email = models.EmailField("e-mail", unique=True)
    nome_completo = models.CharField(max_length=255)
    login_rede = models.CharField(max_length=150, unique=True)
    ramal = models.CharField(max_length=20, blank=True, null=True)
    cargo = models.CharField(max_length=120, blank=True, null=True)
    setor = models.ForeignKey(
        Setor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "nome_completo", "login_rede"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo

    def save(self, *args, **kwargs):
        self.is_active = self.ativo
        super().save(*args, **kwargs)
