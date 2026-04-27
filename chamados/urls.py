from django.urls import path
from . import views

urlpatterns = [
    path("chamados/calendario/", views.calendario_operacional, name="calendario_operacional"),
    path("chamados/calendario/feriado/novo/", views.calendario_feriado_novo, name="calendario_feriado_novo"),
    path("chamados/calendario/feriado/<int:pk>/editar/", views.calendario_feriado_editar, name="calendario_feriado_editar"),
    path("chamados/calendario/feriado/<int:pk>/excluir/", views.calendario_feriado_excluir, name="calendario_feriado_excluir"),
    path("chamados/", views.chamado_lista, name="chamado_lista"),
    path("chamados/dashboard/", views.chamado_dashboard, name="chamado_dashboard"),
    path("chamados/novo/", views.chamado_novo, name="chamado_novo"),
    path("chamados/excluir/", views.chamado_excluir_multiplos, name="chamado_excluir_multiplos"),
    path("chamados/novos/", views.chamado_check_novos, name="chamado_check_novos"),
    path("chamados/pdf/", views.chamado_pdf_lista, name="chamado_pdf_lista"),
    path("chamados/<int:pk>/", views.chamado_detalhe, name="chamado_detalhe"),
    path("chamados/<int:pk>/atender/", views.chamado_atender, name="chamado_atender"),
    path("chamados/<int:pk>/acao/", views.chamado_registrar_acao, name="chamado_registrar_acao"),
    path("chamados/<int:pk>/encerrar/", views.chamado_encerrar, name="chamado_encerrar"),
    path("chamados/<int:pk>/reabrir/", views.chamado_reabrir, name="chamado_reabrir"),
    path("chamados/<int:pk>/excluir/", views.chamado_excluir, name="chamado_excluir"),
    path("chamados/<int:pk>/editar-titulo/", views.chamado_editar_titulo, name="chamado_editar_titulo"),
    path("chamados/<int:pk>/transferir/", views.chamado_transferir, name="chamado_transferir"),
    path("chamados/<int:pk>/pdf/", views.chamado_pdf_detalhe, name="chamado_pdf_detalhe"),
]
