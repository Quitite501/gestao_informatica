from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from .forms import ChamadoForm, ChamadoFiltroForm, ChamadoEncerramentoForm, AcaoChamadoForm
from .models import Chamado, AnexoChamado, AcaoChamado, AnexoAcao


def registrar_auditoria(request, acao, objeto_id, descricao):
    RegistroAuditoria.objects.create(
        usuario=request.user,
        acao=acao,
        modelo_afetado="Chamado",
        objeto_id=str(objeto_id),
        descricao=descricao,
        ip=request.META.get("REMOTE_ADDR"),
    )


@login_required
def chamado_lista(request):
    form_filtro = ChamadoFiltroForm(request.GET or None)
    chamados = Chamado.objects.select_related(
        "solicitante", "tecnico", "categoria").all()

    if form_filtro.is_valid():
        if form_filtro.cleaned_data.get("status"):
            chamados = chamados.filter(status=form_filtro.cleaned_data["status"])
        if form_filtro.cleaned_data.get("categoria"):
            chamados = chamados.filter(categoria=form_filtro.cleaned_data["categoria"])
        if form_filtro.cleaned_data.get("prioridade"):
            chamados = chamados.filter(prioridade=form_filtro.cleaned_data["prioridade"])

    return render(request, "chamados/chamado_lista.html",
        {"chamados": chamados, "form_filtro": form_filtro})


@login_required
def chamado_detalhe(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    anexos = chamado.anexos.all()
    acoes = chamado.acoes.select_related("autor").prefetch_related("anexos").all()
    form_acao = AcaoChamadoForm()
    return render(request, "chamados/chamado_detalhe.html", {
        "chamado": chamado,
        "anexos": anexos,
        "acoes": acoes,
        "form_acao": form_acao,
    })


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_novo(request):
    form = ChamadoForm(request.POST or None)

    if form.is_valid():
        chamado = form.save(commit=False)
        chamado.status = Chamado.STATUS_ABERTO
        chamado.save()

        for arquivo in request.FILES.getlist("anexos"):
            AnexoChamado.objects.create(
                chamado=chamado,
                arquivo=arquivo,
                nome_original=arquivo.name,
                enviado_por=request.user,
            )

        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, chamado.pk,
            f"Chamado #{chamado.pk} criado: {chamado.titulo}")

        return redirect("chamado_detalhe", pk=chamado.pk)

    return render(request, "chamados/chamado_form.html",
        {"form": form, "titulo": "Novo Chamado"})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_atender(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)

    if request.method == "POST":
        chamado.tecnico = request.user
        chamado.status = Chamado.STATUS_EM_ATENDIMENTO
        chamado.save()

        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, chamado.pk,
            f"Chamado #{chamado.pk} assumido por {request.user.nome_completo}")

        return redirect("chamado_detalhe", pk=chamado.pk)

    return render(request, "chamados/chamado_detalhe.html", {"chamado": chamado})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_registrar_acao(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)

    if chamado.status not in [Chamado.STATUS_EM_ATENDIMENTO, Chamado.STATUS_AGUARDANDO]:
        raise PermissionDenied

    if request.method == "POST":
        form = AcaoChamadoForm(request.POST)
        if form.is_valid():
            acao = form.save(commit=False)
            acao.chamado = chamado
            acao.autor = request.user
            acao.save()

            for arquivo in request.FILES.getlist("anexos_acao"):
                AnexoAcao.objects.create(
                    acao=acao,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                )

            registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, chamado.pk,
                f"Ação registrada no Chamado #{chamado.pk} por {request.user.nome_completo}")

            return redirect("chamado_detalhe", pk=chamado.pk)

    return redirect("chamado_detalhe", pk=chamado.pk)


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_encerrar(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)

    if not chamado.tem_acoes():
        return redirect("chamado_detalhe", pk=chamado.pk)

    form = ChamadoEncerramentoForm(request.POST or None, instance=chamado)

    if form.is_valid():
        chamado = form.save(commit=False)
        chamado.status = Chamado.STATUS_ENCERRADO
        chamado.encerrado_por = request.user
        chamado.encerrado_em = timezone.now()
        chamado.save()

        registrar_auditoria(request, RegistroAuditoria.ACAO_ENCERRAMENTO, chamado.pk,
            f"Chamado #{chamado.pk} encerrado por {request.user.nome_completo}")

        return redirect("chamado_detalhe", pk=chamado.pk)

    return render(request, "chamados/chamado_encerramento.html",
        {"form": form, "chamado": chamado})


@login_required
def chamado_reabrir(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)

    eh_solicitante = chamado.solicitante == request.user
    eh_admin = request.user.groups.filter(name="Administrador").exists()

    if not (eh_solicitante or eh_admin):
        raise PermissionDenied

    if request.method == "POST":
        chamado.status = Chamado.STATUS_ABERTO
        chamado.encerrado_por = None
        chamado.encerrado_em = None
        chamado.solucao_tecnica = None
        chamado.save()

        registrar_auditoria(request, RegistroAuditoria.ACAO_REABERTURA, chamado.pk,
            f"Chamado #{chamado.pk} reaberto por {request.user.nome_completo}")

        return redirect("chamado_detalhe", pk=chamado.pk)

    return render(request, "chamados/chamado_detalhe.html", {"chamado": chamado})


@login_required
def chamado_excluir(request, pk):
    eh_admin = request.user.groups.filter(name="Administrador").exists()
    if not eh_admin:
        raise PermissionDenied

    chamado = get_object_or_404(Chamado, pk=pk)

    if request.method == "POST":
        descricao = f"Chamado #{chamado.pk} excluído: '{chamado.titulo}' — solicitante: {chamado.solicitante.nome_completo} — status anterior: {chamado.get_status_display()}"
        registrar_auditoria(request, RegistroAuditoria.ACAO_EXCLUSAO, chamado.pk, descricao)
        chamado.delete()
        return redirect("chamado_lista")

    return render(request, "chamados/chamado_confirmar_exclusao.html", {"chamado": chamado})


@login_required
def chamado_excluir_multiplos(request):
    eh_admin = request.user.groups.filter(name="Administrador").exists()
    if not eh_admin:
        raise PermissionDenied

    if request.method == "POST":
        ids = request.POST.getlist("chamados_selecionados")
        if ids:
            chamados = Chamado.objects.filter(pk__in=ids)
            for chamado in chamados:
                descricao = f"Chamado #{chamado.pk} excluído em lote: '{chamado.titulo}' — solicitante: {chamado.solicitante.nome_completo} — status anterior: {chamado.get_status_display()}"
                registrar_auditoria(request, RegistroAuditoria.ACAO_EXCLUSAO, chamado.pk, descricao)
            chamados.delete()

    return redirect("chamado_lista")
