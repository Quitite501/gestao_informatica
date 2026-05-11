from django.urls import path
from . import views

urlpatterns = [
    path('', views.servidor_lista, name='servidor_lista'),
    path('novo/', views.servidor_novo, name='servidor_novo'),
    path('<int:pk>/', views.servidor_detalhe, name='servidor_detalhe'),
    path('<int:pk>/editar/', views.servidor_editar, name='servidor_editar'),
    path('<int:pk>/mudanca/', views.mudanca_registrar, name='mudanca_registrar'),
]
