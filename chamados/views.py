from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ChamadoForm, ChamadoFiltroForm, ChamadoEncerramentoForm
from .models import Chamado, AnexoChamado


@login_required
def chamado_lista(request):
    form_filtro = ChamadoFiltroForm(request.GET or None)
    chamados = Chamado.objects.select_related("solicitante", "tecnico", "categoria").all()
    if form_filtro.is_valid():
        if form_filtro.cleaned_data.get("status"):
            chamados = chamados.filter(status=form_filtro.cleaned_data["status"])
        if form_filtro.cleaned_data.get("categoria"):
            chamados = chamados.filter(categoria=form_filtro.cleaned_data["categoria"])
        if form_filtro.cleaned_data.get("prioridade"):
            chamados = chamados.filter(prioridade=form_filtro.cleaned_data["prioridade"])
    return render(request, "chamados/chamado_lista.html", {"chamados": chamados, "form_filtro": form_filtro})


@login_required
def chamado_detalhe(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    anexos = chamado.anexos.all()
    return render(request, "chamados/chamado_detalhe.html", {"chamado": chamado, "anexos": anexos})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_novo(request):
    form = ChamadoForm(request.POST or None)
    if form.is_valid():
        chamado = form.save(commit=False)
        chamado.status = Chamado.STATUS_ABERTO
        chamado.save()
        if request.FILES.get("anexo"):
            AnexoChamado.objects.create(
                chamado=chamado,
                arquivo=request.FILES["anexo"],
                enviado_por=request.user,
            )
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_form.html", {"form": form, "titulo": "Novo Chamado"})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_atender(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    if request.method == "POST":
        chamado.tecnico = request.user
        chamado.status = Chamado.STATUS_EM_ATENDIMENTO
        chamado.save()
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_detalhe.html", {"chamado": chamado})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_encerrar(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    form = ChamadoEncerramentoForm(request.POST or None, instance=chamado)
    if form.is_valid():
        chamado = form.save(commit=False)
        chamado.status = Chamado.STATUS_ENCERRADO
        chamado.encerrado_por = request.user
        chamado.encerrado_em = timezone.now()
        chamado.save()
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_encerramento.html", {"form": form, "chamado": chamado})


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
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_detalhe.html", {"chamado": chamado})
