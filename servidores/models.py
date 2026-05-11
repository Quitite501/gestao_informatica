from django.db import models
from django.conf import settings


class Servidor(models.Model):
    TIPO_CHOICES = [
        ('fisico', 'Físico'),
        ('virtual', 'Virtual'),
        ('cloud', 'Cloud'),
    ]
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('manutencao', 'Em manutenção'),
    ]

    nome = models.CharField(max_length=100)
    hostname = models.CharField(max_length=100, blank=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    sistema_operacional = models.CharField(max_length=100, blank=True)
    funcao = models.CharField(max_length=200, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='virtual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    localizacao = models.CharField(max_length=200, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servidor'
        verbose_name_plural = 'Servidores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def total_chamados(self):
        return self.chamados.count()

    def chamados_abertos(self):
        return self.chamados.exclude(status='encerrado').count()


class MudancaServidor(models.Model):
    TIPO_CHOICES = [
        ('configuracao', 'Configuração'),
        ('atualizacao', 'Atualização de sistema'),
        ('instalacao', 'Instalação de software'),
        ('manutencao', 'Manutenção'),
        ('seguranca', 'Correção de segurança'),
        ('hardware', 'Troca de hardware'),
        ('outro', 'Outro'),
    ]
    ORIGEM_CHOICES = [
        ('manual', 'Registro manual'),
        ('chamado', 'Via chamado'),
    ]

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='mudancas')
    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='configuracao')
    descricao = models.TextField()
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='manual')
    chamado = models.ForeignKey(
        'chamados.Chamado',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='mudancas_servidor'
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mudancas_servidor'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mudança'
        verbose_name_plural = 'Mudanças'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.servidor.nome} — {self.titulo}'
