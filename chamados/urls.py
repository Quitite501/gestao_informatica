from django.urls import path
from . import views

urlpatterns = [
    path("chamados/", views.chamado_lista, name="chamado_lista"),
    path("chamados/novo/", views.chamado_novo, name="chamado_novo"),
    path("chamados/<int:pk>/", views.chamado_detalhe, name="chamado_detalhe"),
    path("chamados/<int:pk>/atender/", views.chamado_atender, name="chamado_atender"),
    path("chamados/<int:pk>/encerrar/", views.chamado_encerrar, name="chamado_encerrar"),
    path("chamados/<int:pk>/reabrir/", views.chamado_reabrir, name="chamado_reabrir"),
]
