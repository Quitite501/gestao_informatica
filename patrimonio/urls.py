from django.urls import path
from . import views

urlpatterns = [
    path("patrimonio/", views.patrimonio_lista, name="patrimonio_lista"),
    path("patrimonio/novo/", views.patrimonio_novo, name="patrimonio_novo"),
    path("patrimonio/<int:pk>/", views.patrimonio_detalhe, name="patrimonio_detalhe"),
    path("patrimonio/<int:pk>/editar/", views.patrimonio_editar, name="patrimonio_editar"),
    path("computadores/novo/", views.computador_novo, name="computador_novo"),
    path("computadores/<int:pk>/", views.computador_detalhe, name="computador_detalhe"),
    path("computadores/<int:pk>/editar/", views.computador_editar, name="computador_editar"),
    path("relatorio/computadores/", views.relatorio_computadores, name="relatorio_computadores"),
    path("relatorio/computadores/csv/", views.relatorio_computadores_csv, name="relatorio_computadores_csv"),
    path("relatorio/computadores/pdf/", views.relatorio_computadores_pdf, name="relatorio_computadores_pdf"),
]
