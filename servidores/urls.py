from django.urls import path
from . import views

urlpatterns = [
    path('servidores/', views.servidor_lista, name='servidor_lista'),
    path('servidores/novo/', views.servidor_novo, name='servidor_novo'),
    path('servidores/<int:pk>/', views.servidor_detalhe, name='servidor_detalhe'),
    path('servidores/<int:pk>/editar/', views.servidor_editar, name='servidor_editar'),
    path('servidores/<int:pk>/mudanca/', views.mudanca_registrar, name='mudanca_registrar'),
]
