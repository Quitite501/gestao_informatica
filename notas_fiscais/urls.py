from django.urls import path
from . import views

urlpatterns = [
    path("notas-fiscais/", views.nota_fiscal_lista, name="nota_fiscal_lista"),
    path("notas-fiscais/nova/", views.nota_fiscal_nova, name="nota_fiscal_nova"),
    path("notas-fiscais/<int:pk>/", views.nota_fiscal_detalhe, name="nota_fiscal_detalhe"),
    path("notas-fiscais/<int:pk>/editar/", views.nota_fiscal_editar, name="nota_fiscal_editar"),
    path("notas-fiscais/importar/", views.nota_fiscal_importar, name="nota_fiscal_importar"),
    path("notas-fiscais/<int:pk>/licencas/", views.nota_fiscal_vincular_licencas, name="nota_fiscal_vincular_licencas"),
]
