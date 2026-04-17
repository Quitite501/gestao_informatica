from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .forms import PatrimonioForm, PatrimonioFiltroForm
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from .models import Patrimonio, MovimentacaoPatrimonio


def _registrar_movimentacao(patrimonio_antes, patrimonio_depois, usuario_logado):
    houve_mudanca = (
        patrimonio_antes.usuario_atual != patrimonio_depois.usuario_atual
        or patrimonio_antes.setor != patrimonio_depois.setor
        or patrimonio_antes.status != patrimonio_depois.status
    )

    if not houve_mudanca:
        return

    if patrimonio_antes.usuario_atual != patrimonio_depois.usuario_atual:
        if patrimonio_depois.usuario_atual:
            tipo = MovimentacaoPatrimonio.TIPO_ATRIBUICAO
        else:
            tipo = MovimentacaoPatrimonio.TIPO_DEVOLUCAO
    elif patrimonio_depois.status == Patrimonio.STATUS_EM_MANUTENCAO:
        tipo = MovimentacaoPatrimonio.TIPO_MANUTENCAO
    elif patrimonio_antes.status == Patrimonio.STATUS_EM_MANUTENCAO:
        tipo = MovimentacaoPatrimonio.TIPO_RETORNO
    elif patrimonio_depois.status == Patrimonio.STATUS_BAIXADO:
        tipo = MovimentacaoPatrimonio.TIPO_BAIXA
    elif patrimonio_antes.setor != patrimonio_depois.setor:
        tipo = MovimentacaoPatrimonio.TIPO_TRANSFERENCIA
    else:
        tipo = MovimentacaoPatrimonio.TIPO_OUTRO

    MovimentacaoPatrimonio.objects.create(
        patrimonio=patrimonio_depois,
        tipo=tipo,
        usuario_anterior=patrimonio_antes.usuario_atual,
        setor_anterior=patrimonio_antes.setor,
        status_anterior=patrimonio_antes.status,
        usuario_novo=patrimonio_depois.usuario_atual,
        setor_novo=patrimonio_depois.setor,
        status_novo=patrimonio_depois.status,
        registrado_por=usuario_logado,
    )


@login_required
def patrimonio_lista(request):
    # ── Limpar filtros ────────────────────────────────────────────────
    if "limpar" in request.GET:
        request.session.pop("patrimonio_filtros", None)
        return redirect("patrimonio_lista")

    # ── Salvar filtros na sessão e redirecionar para URL limpa ────────
    if request.GET:
        request.session["patrimonio_filtros"] = {
            k: request.GET.getlist(k) for k in request.GET.keys()
        }
        return redirect("patrimonio_lista")

    # ── Reconstruir filtros da sessão ─────────────────────────────────
    from django.http import QueryDict
    filtros_salvos = request.session.get("patrimonio_filtros", {})
    qd = QueryDict(mutable=True).copy()
    for k, v in filtros_salvos.items():
        if isinstance(v, list):
            for item in v:
                qd.appendlist(k, item)
        else:
            qd[k] = v

    form_filtro = PatrimonioFiltroForm(qd or None)
    patrimonios = Patrimonio.objects.select_related("tipo", "setor", "usuario_atual").all()

    if form_filtro.is_valid():
        etiqueta = form_filtro.cleaned_data.get("etiqueta")
        tipo = form_filtro.cleaned_data.get("tipo")
        status = form_filtro.cleaned_data.get("status")

        if etiqueta:
            patrimonios = patrimonios.filter(
                Q(etiqueta__icontains=etiqueta) | Q(modelo__icontains=etiqueta) | Q(marca__icontains=etiqueta)
            )
        if tipo:
            patrimonios = patrimonios.filter(tipo=tipo)
        if status:
            patrimonios = patrimonios.filter(status=status)

    patrimonios = patrimonios.order_by("etiqueta")

    return render(request, "patrimonio/patrimonio_lista.html", {
        "patrimonios": patrimonios,
        "form_filtro": form_filtro,
        "total": patrimonios.count(),
    })


@login_required
def patrimonio_detalhe(request, pk):
    patrimonio = get_object_or_404(
        Patrimonio.objects.select_related("tipo", "setor", "usuario_atual", "criado_por"),
        pk=pk,
    )
    movimentacoes = patrimonio.movimentacoes.select_related(
        "usuario_anterior", "usuario_novo", "setor_anterior", "setor_novo", "registrado_por"
    ).order_by("-data")

    return render(request, "patrimonio/patrimonio_detalhe.html", {
        "patrimonio": patrimonio,
        "movimentacoes": movimentacoes,
    })


@login_required
@permission_required("patrimonio.can_manage_patrimonio", raise_exception=True)
def patrimonio_novo(request):
    form = PatrimonioForm(request.POST or None)

    if form.is_valid():
        patrimonio = form.save(commit=False)
        patrimonio.criado_por = request.user
        patrimonio.save()

        if patrimonio.usuario_atual or patrimonio.setor:
            if patrimonio.usuario_atual:
                tipo = MovimentacaoPatrimonio.TIPO_ATRIBUICAO
            else:
                tipo = MovimentacaoPatrimonio.TIPO_OUTRO
            MovimentacaoPatrimonio.objects.create(
                patrimonio=patrimonio,
                tipo=tipo,
                usuario_novo=patrimonio.usuario_atual,
                setor_novo=patrimonio.setor,
                status_novo=patrimonio.status,
                registrado_por=request.user,
            )

        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "Patrimonio", patrimonio.pk, f"Patrimônio {patrimonio.etiqueta} cadastrado.")
        return redirect("patrimonio_detalhe", pk=patrimonio.pk)

    return render(request, "patrimonio/patrimonio_form.html", {
        "form": form,
        "titulo": "Novo patrimonio",
    })


@login_required
@permission_required("patrimonio.can_manage_patrimonio", raise_exception=True)
def patrimonio_editar(request, pk):
    patrimonio = get_object_or_404(Patrimonio, pk=pk)

    estado_anterior = Patrimonio(
        usuario_atual=patrimonio.usuario_atual,
        setor=patrimonio.setor,
        status=patrimonio.status,
    )

    form = PatrimonioForm(request.POST or None, instance=patrimonio)

    if form.is_valid():
        patrimonio_atualizado = form.save()
        _registrar_movimentacao(estado_anterior, patrimonio_atualizado, request.user)
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "Patrimonio", patrimonio_atualizado.pk, f"Patrimônio {patrimonio_atualizado.etiqueta} editado.")
        return redirect("patrimonio_detalhe", pk=patrimonio_atualizado.pk)

    return render(request, "patrimonio/patrimonio_form.html", {
        "form": form,
        "titulo": f"Editar patrimonio: {patrimonio.etiqueta}",
        "patrimonio": patrimonio,
    })
