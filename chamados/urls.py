from django.urls import path
from . import views

urlpatterns = [
    path("chamados/", views.chamado_lista, name="chamado_lista"),
    path("chamados/novo/", views.chamado_novo, name="chamado_novo"),
    path("chamados/excluir/", views.chamado_excluir_multiplos, name="chamado_excluir_multiplos"),
    path("chamados/<int:pk>/", views.chamado_detalhe, name="chamado_detalhe"),
    path("chamados/<int:pk>/atender/", views.chamado_atender, name="chamado_atender"),
    path("chamados/<int:pk>/acao/", views.chamado_registrar_acao, name="chamado_registrar_acao"),
    path("chamados/<int:pk>/encerrar/", views.chamado_encerrar, name="chamado_encerrar"),
    path("chamados/<int:pk>/reabrir/", views.chamado_reabrir, name="chamado_reabrir"),
    path("chamados/<int:pk>/excluir/", views.chamado_excluir, name="chamado_excluir"),
]
