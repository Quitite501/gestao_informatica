from django.urls import path
from . import views

urlpatterns = [
    path("relatorios/chamados/", views.relatorio_chamados, name="relatorio_chamados"),
    path("relatorios/patrimonio/", views.relatorio_patrimonio, name="relatorio_patrimonio"),
    path("relatorios/usuarios/", views.relatorio_usuarios, name="relatorio_usuarios"),
    path("relatorios/notas-fiscais/", views.relatorio_notas_fiscais, name="relatorio_notas_fiscais"),
]
