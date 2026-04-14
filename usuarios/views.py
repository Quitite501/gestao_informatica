from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from .forms import UsuarioForm
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from .models import Usuario


class UsuarioLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@login_required
def painel(request):
    return render(request, 'usuarios/painel.html')


@login_required
@permission_required('usuarios.view_usuario', raise_exception=True)
def usuario_lista(request):
    usuarios = Usuario.objects.select_related('setor').all().order_by('nome_completo')
    return render(request, 'usuarios/usuario_lista.html', {'usuarios': usuarios})


@login_required
@permission_required('usuarios.add_usuario', raise_exception=True)
def usuario_novo(request):
    form = UsuarioForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('usuario_lista')

    return render(request, 'usuarios/usuario_form.html', {
        'form': form,
        'titulo': 'Novo usuário',
    })


@login_required
@permission_required('usuarios.change_usuario', raise_exception=True)
def usuario_editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario)

    if form.is_valid():
        form.save()
        return redirect('usuario_lista')

    return render(request, 'usuarios/usuario_form.html', {
        'form': form,
        'titulo': f'Editar usuário: {usuario.nome_completo}',
    })


@login_required
@permission_required('usuarios.change_usuario', raise_exception=True)
def usuario_desativar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()
        return redirect('usuario_lista')

    return render(request, 'usuarios/usuario_confirmar_desativacao.html', {
        'usuario': usuario,
    })
