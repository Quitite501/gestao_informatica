from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from .forms import UsuarioForm
from .models import Usuario


class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy("login")


@login_required
def painel(request):
    from chamados.models import Chamado
    from patrimonio.models import Patrimonio
    from licencas.models import LicencaContrato
    hoje = timezone.now().date()
    em_30_dias = hoje + timedelta(days=30)
    context = {
        'total_chamados_abertos': Chamado.objects.exclude(status='encerrado').count(),
        'total_chamados_criticos': Chamado.objects.filter(status__in=['aberto', 'em_atendimento'], prioridade='critica').count(),
        'total_patrimonio_disponivel': Patrimonio.objects.filter(status='disponivel').count(),
        'total_licencas_vencer': LicencaContrato.objects.filter(data_vencimento__lte=em_30_dias, data_vencimento__gte=hoje).count(),
        'total_usuarios_ativos': Usuario.objects.filter(ativo=True).count(),
        'ultimos_registros': RegistroAuditoria.objects.select_related('usuario').all()[:5],
        'ultimos_chamados': Chamado.objects.select_related('solicitante', 'tecnico', 'categoria').exclude(status='encerrado').order_by('-criado_em')[:5],
    }
    return render(request, 'usuarios/painel.html', context)


@login_required
@permission_required("usuarios.view_usuario", raise_exception=True)
def usuario_lista(request):
    usuarios = Usuario.objects.select_related("setor").all().order_by("nome_completo")
    return render(request, "usuarios/usuario_lista.html", {"usuarios": usuarios})


@login_required
@permission_required("usuarios.add_usuario", raise_exception=True)
def usuario_novo(request):
    form = UsuarioForm(request.POST or None)
    if form.is_valid():
        usuario = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "Usuario",
            usuario.pk, f"Usuário {usuario.nome_completo} criado.")
        return redirect("usuario_lista")
    return render(request, "usuarios/usuario_form.html", {
        "form": form,
        "titulo": "Novo usuário",
    })


@login_required
@permission_required("usuarios.change_usuario", raise_exception=True)
def usuario_editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario)
    if form.is_valid():
        usuario = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "Usuario",
            usuario.pk, f"Usuário {usuario.nome_completo} editado.")
        return redirect("usuario_lista")
    return render(request, "usuarios/usuario_form.html", {
        "form": form,
        "titulo": f"Editar usuário: {usuario.nome_completo}",
    })


@login_required
@permission_required("usuarios.change_usuario", raise_exception=True)
def usuario_desativar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_DESATIVACAO, "Usuario",
            usuario.pk, f"Usuário {usuario.nome_completo} desativado.")
        return redirect("usuario_lista")
    return render(request, "usuarios/usuario_confirmar_desativacao.html", {
        "usuario": usuario,
    })
