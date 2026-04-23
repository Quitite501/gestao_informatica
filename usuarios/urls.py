from django.urls import path
from .views import (
    UsuarioLoginView,
    UsuarioLogoutView,
    painel,
    usuario_lista,
    usuario_novo,
    usuario_editar,
    usuario_desativar,
    usuario_recuperar_senha,
    usuario_redefinir_senha,
    usuario_meu_perfil,
)

urlpatterns = [
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
    path('recuperar-senha/', usuario_recuperar_senha, name='usuario_recuperar_senha'),
    path('usuarios/<int:pk>/redefinir-senha/', usuario_redefinir_senha, name='usuario_redefinir_senha'),
    path('meu-perfil/', usuario_meu_perfil, name='usuario_meu_perfil'),
    path('', painel, name='painel'),
    path('usuarios/', usuario_lista, name='usuario_lista'),
    path('usuarios/novo/', usuario_novo, name='usuario_novo'),
    path('usuarios/<int:pk>/editar/', usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/desativar/', usuario_desativar, name='usuario_desativar'),
]
