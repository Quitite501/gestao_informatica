from django.urls import path
from . import views

urlpatterns = [
    path("licencas/", views.licenca_dashboard, name="licenca_dashboard"),
    path("softwares/", views.software_lista, name="software_lista"),
    path("softwares/novo/", views.software_novo, name="software_novo"),
    path("softwares/gerenciar/", views.software_gerenciar, name="software_gerenciar"),
    path("softwares/<int:pk>/", views.software_detalhe, name="software_detalhe"),
    path("softwares/<int:pk>/editar/", views.software_editar, name="software_editar"),
    path("licencas/contrato/novo/", views.licenca_contrato_novo, name="licenca_contrato_novo"),
    path("licencas/contrato/<int:pk>/editar/", views.licenca_contrato_editar, name="licenca_contrato_editar"),
    # path("instalacoes/nova/", views.instalacao_nova, name="instalacao_nova"),  # Desabilitado
    # path("instalacoes/<int:pk>/editar/", views.instalacao_editar, name="instalacao_editar"),  # Desabilitado
    path("relatorio/conformidade/", views.relatorio_conformidade, name="relatorio_conformidade"),
    path("softwares/criar-lote/", views.software_criar_lote, name="software_criar_lote"),
    path("relatorio-customizado/", views.relatorio_customizado, name="relatorio_customizado"),
    path("relatorio-customizado/pdf/", views.relatorio_customizado_pdf, name="relatorio_customizado_pdf"),
    path("softwares/busca/", views.software_busca_ajax, name="software_busca_ajax"),
    path("nota-fiscal/data/", views.nota_fiscal_data_ajax, name="nota_fiscal_data_ajax"),
]
