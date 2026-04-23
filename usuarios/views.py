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
    inicio_mes = hoje.replace(day=1)

    # KPIs originais
    total_chamados_abertos    = Chamado.objects.exclude(status='encerrado').count()
    total_chamados_criticos   = Chamado.objects.filter(status__in=['aberto','em_atendimento'], prioridade='critica').count()
    total_patrimonio_disponivel = Patrimonio.objects.filter(status='disponivel').count()
    total_licencas_vencer     = LicencaContrato.objects.filter(data_vencimento__lte=em_30_dias, data_vencimento__gte=hoje).count()
    total_usuarios_ativos     = Usuario.objects.filter(ativo=True).count()
    ultimos_registros         = RegistroAuditoria.objects.select_related('usuario').all()[:5]
    ultimos_chamados          = Chamado.objects.select_related('solicitante','tecnico','categoria').exclude(status='encerrado').order_by('-criado_em')[:5]

    # Chamados por status
    chamados_aberto          = Chamado.objects.filter(status='aberto').count()
    chamados_em_atendimento  = Chamado.objects.filter(status='em_atendimento').count()
    chamados_aguardando      = Chamado.objects.filter(status='aguardando_usuario').count()
    chamados_encerrados_mes  = Chamado.objects.filter(status='encerrado', encerrado_em__date__gte=inicio_mes).count()
    total_status             = chamados_aberto + chamados_em_atendimento + chamados_aguardando + chamados_encerrados_mes or 1

    # Chamados por prioridade (ativos)
    chamados_critica  = Chamado.objects.filter(prioridade='critica').exclude(status='encerrado').count()
    chamados_alta     = Chamado.objects.filter(prioridade='alta').exclude(status='encerrado').count()
    chamados_media    = Chamado.objects.filter(prioridade='media').exclude(status='encerrado').count()
    chamados_baixa    = Chamado.objects.filter(prioridade='baixa').exclude(status='encerrado').count()
    total_prioridade  = chamados_critica + chamados_alta + chamados_media + chamados_baixa or 1

    # SLA resumido
    sla_no_prazo = sla_em_risco = sla_vencido = 0
    for c in Chamado.objects.exclude(status='encerrado'):
        s = c.status_sla()
        if s == 'no_prazo':   sla_no_prazo += 1
        elif s == 'em_risco': sla_em_risco += 1
        elif s == 'vencido':  sla_vencido  += 1

    # Patrimônio por status
    patrimonio_em_uso     = Patrimonio.objects.filter(status='em_uso').count()
    patrimonio_manutencao = Patrimonio.objects.filter(status='manutencao').count()
    patrimonio_total      = Patrimonio.objects.count()

    # Licenças em alerta
    licencas_vencidas = LicencaContrato.objects.filter(data_vencimento__lt=hoje).count()
    licencas_alerta   = LicencaContrato.objects.filter(
        data_vencimento__lte=em_30_dias, data_vencimento__gte=hoje
    ).select_related('software').order_by('data_vencimento')[:5]

    context = {
        # originais
        'total_chamados_abertos':       total_chamados_abertos,
        'total_chamados_criticos':      total_chamados_criticos,
        'total_patrimonio_disponivel':  total_patrimonio_disponivel,
        'total_licencas_vencer':        total_licencas_vencer,
        'total_usuarios_ativos':        total_usuarios_ativos,
        'ultimos_registros':            ultimos_registros,
        'ultimos_chamados':             ultimos_chamados,
        # chamados por status
        'chamados_aberto':              chamados_aberto,
        'chamados_em_atendimento':      chamados_em_atendimento,
        'chamados_aguardando':          chamados_aguardando,
        'chamados_encerrados_mes':      chamados_encerrados_mes,
        'total_status':                 total_status,
        # chamados por prioridade
        'chamados_critica':             chamados_critica,
        'chamados_alta':                chamados_alta,
        'chamados_media':               chamados_media,
        'chamados_baixa':               chamados_baixa,
        'total_prioridade':             total_prioridade,
        # SLA
        'sla_no_prazo':                 sla_no_prazo,
        'sla_em_risco':                 sla_em_risco,
        'sla_vencido':                  sla_vencido,
        # patrimônio
        'patrimonio_em_uso':            patrimonio_em_uso,
        'patrimonio_manutencao':        patrimonio_manutencao,
        'patrimonio_total':             patrimonio_total,
        # licenças
        'licencas_vencidas':            licencas_vencidas,
        'licencas_alerta':              licencas_alerta,
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
    form = UsuarioForm(request.POST or None, request.FILES or None)
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
    form = UsuarioForm(request.POST or None, request.FILES or None, instance=usuario)
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
