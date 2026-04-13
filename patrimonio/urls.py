from django.urls import path
from . import views

urlpatterns = [
    path("patrimonio/", views.patrimonio_lista, name="patrimonio_lista"),
    path("patrimonio/novo/", views.patrimonio_novo, name="patrimonio_novo"),
    path("patrimonio/<int:pk>/", views.patrimonio_detalhe, name="patrimonio_detalhe"),
    path("patrimonio/<int:pk>/editar/", views.patrimonio_editar, name="patrimonio_editar"),
]
