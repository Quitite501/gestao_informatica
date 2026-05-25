from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from django.utils import timezone
from .forms import SoftwareForm, SoftwareFiltroForm, LicencaContratoForm, InstalacaoSoftwareForm
from .models import Software, LicencaContrato, InstalacaoSoftware


@login_required
def software_lista(request):
    # ── Limpar filtros ────────────────────────────────────────────────
    if "limpar" in request.GET:
        request.session.pop("software_filtros", None)
        return redirect("software_lista")

    # ── Salvar filtros na sessão e redirecionar para URL limpa ────────
    if request.GET:
        request.session["software_filtros"] = {
            k: request.GET.getlist(k) for k in request.GET.keys()
        }
        return redirect("software_lista")

    # ── Reconstruir filtros da sessão ─────────────────────────────────
    from django.http import QueryDict
    filtros_salvos = request.session.get("software_filtros", {})
    qd = QueryDict(mutable=True).copy()
    for k, v in filtros_salvos.items():
        if isinstance(v, list):
            for item in v:
                qd.appendlist(k, item)
        else:
            qd[k] = v

    form_filtro = SoftwareFiltroForm(qd or None)
    softwares = Software.objects.all()

    if form_filtro.is_valid():
        if form_filtro.cleaned_data.get("nome"):
            softwares = softwares.filter(nome__icontains=form_filtro.cleaned_data["nome"])
        if form_filtro.cleaned_data.get("fabricante"):
            softwares = softwares.filter(fabricante__icontains=form_filtro.cleaned_data["fabricante"])
        if form_filtro.cleaned_data.get("controlado") == "true":
            softwares = softwares.filter(controlado=True)
        elif form_filtro.cleaned_data.get("controlado") == "false":
            softwares = softwares.filter(controlado=False)

    softwares = softwares.order_by("nome")

    return render(request, "licencas/software_lista.html", {
        "softwares": softwares,
        "form_filtro": form_filtro,
    })


@login_required
def software_detalhe(request, pk):
    software = get_object_or_404(Software, pk=pk)
    contratos = software.contratos.select_related("nota_fiscal").all()
    instalacoes = software.instalacoes.filter(ativo=True).select_related(
        "patrimonio", "patrimonio__usuario_atual", "patrimonio__setor"
    )
    return render(request, "licencas/software_detalhe.html", {
        "software": software,
        "contratos": contratos,
        "instalacoes": instalacoes,
    })


@login_required
@permission_required("licencas.add_software", raise_exception=True)
def software_novo(request):
    form = SoftwareForm(request.POST or None)
    if form.is_valid():
        software = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "Software", software.pk, f"Software {software.nome} cadastrado.")
        return redirect("software_lista")
    return render(request, "licencas/software_form.html", {
        "form": form,
        "titulo": "Novo Software",
    })


@login_required
@permission_required("licencas.change_software", raise_exception=True)
def software_editar(request, pk):
    software = get_object_or_404(Software, pk=pk)
    form = SoftwareForm(request.POST or None, instance=software)
    
    if form.is_valid():
        software = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "Software", software.pk, f"Software {software.nome} editado.")
        return redirect("software_detalhe", pk=software.pk)
    
    contratos = software.contratos.select_related("nota_fiscal").order_by("-data_aquisicao")
    
    return render(request, "licencas/software_form.html", {
        "form": form,
        "software": software,
        "contratos": contratos,
        "titulo": f"Editar Software: {software}",
    })


@login_required
@permission_required("licencas.add_licencacontrato", raise_exception=True)
def licenca_contrato_novo(request):
    # Formulário rápido inline (vindo da tela de edição de software)
    if request.method == "POST" and request.POST.get("quantidade_adquirida") and request.POST.get("software"):
        from notas_fiscais.models import NotaFiscal
        
        software_pk = request.POST.get("software")
        qtd = int(request.POST.get("quantidade_adquirida", 1))
        data_aquisicao = request.POST.get("data_aquisicao")
        data_vencimento = request.POST.get("data_vencimento") or None
        chave = request.POST.get("chave_licenca", "").strip() or None
        nf_numero = request.POST.get("nota_fiscal_numero", "").strip()
        
        nota_fiscal = None
        if nf_numero:
            nota_fiscal = NotaFiscal.objects.filter(numero__icontains=nf_numero).first()
        
        software = get_object_or_404(Software, pk=software_pk)
        contrato = LicencaContrato.objects.create(
            software=software,
            quantidade_adquirida=qtd,
            data_aquisicao=data_aquisicao,
            data_vencimento=data_vencimento,
            chave_licenca=chave,
            nota_fiscal=nota_fiscal,
            criado_por=request.user,
        )
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "LicencaContrato", contrato.pk,
            f"Contrato criado: {software.nome} — {qtd} licença(s)" + (f" — NF: {nota_fiscal.numero}" if nota_fiscal else ""))
        return redirect("software_editar", pk=software.pk)

    form = LicencaContratoForm(request.POST or None)
    if form.is_valid():
        contrato = form.save(commit=False)
        contrato.criado_por = request.user
        contrato.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "LicencaContrato", contrato.pk, f"Contrato de licença cadastrado para {contrato.software.nome}.")
        return redirect("software_editar", pk=contrato.software.pk)
    return render(request, "licencas/licenca_contrato_form.html", {
        "form": form,
        "titulo": "Novo Contrato de Licença",
    })


@login_required
@permission_required("licencas.change_licencacontrato", raise_exception=True)
def licenca_contrato_editar(request, pk):
    contrato = get_object_or_404(LicencaContrato, pk=pk)
    form = LicencaContratoForm(request.POST or None, instance=contrato)
    if form.is_valid():
        contrato = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "LicencaContrato", contrato.pk, f"Contrato de licença editado para {contrato.software.nome}.")
        return redirect("software_detalhe", pk=contrato.software.pk)
    return render(request, "licencas/licenca_contrato_form.html", {
        "form": form,
        "titulo": f"Editar Contrato: {contrato}",
    })


@login_required
@permission_required("licencas.add_instalacaosoftware", raise_exception=True)
def instalacao_nova(request):
    form = InstalacaoSoftwareForm(request.POST or None)
    if form.is_valid():
        instalacao = form.save(commit=False)
        instalacao.registrado_por = request.user
        instalacao.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "InstalacaoSoftware", instalacao.pk, f"Instalação de {instalacao.software.nome} registrada.")
        return redirect("software_detalhe", pk=instalacao.software.pk)
    return render(request, "licencas/instalacao_form.html", {
        "form": form,
        "titulo": "Registrar Instalação",
    })


@login_required
@permission_required("licencas.change_instalacaosoftware", raise_exception=True)
def instalacao_editar(request, pk):
    instalacao = get_object_or_404(InstalacaoSoftware, pk=pk)
    form = InstalacaoSoftwareForm(request.POST or None, instance=instalacao)
    if form.is_valid():
        instalacao = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "InstalacaoSoftware", instalacao.pk, f"Instalação de {instalacao.software.nome} editada.")
        return redirect("software_detalhe", pk=instalacao.software.pk)
    return render(request, "licencas/instalacao_form.html", {
        "form": form,
        "titulo": f"Editar Instalação: {instalacao}",
    })


@login_required
def relatorio_conformidade(request):
    hoje = timezone.now().date()
    softwares = Software.objects.filter(controlado=True, ativo=True)

    relatorio = []
    for sw in softwares:
        total_adquirido = sw.total_adquirido
        total_instalado = sw.total_instalado
        saldo = sw.saldo
        situacao = sw.situacao

        contratos = sw.contratos.all()
        vencimento_status = "ok"
        for c in contratos:
            s = c.status_vencimento
            if s == "vencida":
                vencimento_status = "vencida"
                break
            elif s == "vence_em_breve":
                vencimento_status = "vence_em_breve"

        relatorio.append({
            "software": sw,
            "total_adquirido": total_adquirido,
            "total_instalado": total_instalado,
            "saldo": saldo,
            "situacao": situacao,
            "vencimento_status": vencimento_status,
        })

    return render(request, "licencas/relatorio_conformidade.html", {
        "relatorio": relatorio,
        "hoje": hoje,
    })


@login_required
@permission_required("licencas.add_software", raise_exception=True)
def software_criar_lote(request):
    """Cria múltiplos softwares + contratos de licença a partir de JSON"""
    from django.http import JsonResponse
    import json
    from datetime import date

    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido"}, status=405)

    try:
        licencas = json.loads(request.POST.get("licencas", "[]"))
    except Exception:
        return JsonResponse({"erro": "Dados inválidos"}, status=400)

    if not licencas:
        return JsonResponse({"erro": "Nenhuma licença enviada"}, status=400)

    criados = []
    for lic in licencas:
        nome = lic.get("nome", "").strip()
        qtd  = int(lic.get("qtd", 1) or 1)
        tipo = lic.get("tipo", "perpétua")

        if not nome:
            continue

        software, criado = Software.objects.get_or_create(
            nome=nome,
            defaults={
                "tipo_licenca": tipo,
                "controlado": True,
                "ativo": True,
            }
        )

        # Criar contrato de licença
        LicencaContrato.objects.create(
            software=software,
            quantidade_adquirida=qtd,
            data_aquisicao=date.today(),
            criado_por=request.user,
        )

        registrar_auditoria(
            request, RegistroAuditoria.ACAO_CRIACAO,
            "Software", software.pk,
            f"Software {'criado' if criado else 'atualizado'} em lote: {software.nome} ({qtd} licenças)"
        )
        criados.append(software.nome)

    if not criados:
        return JsonResponse({"erro": "Nenhum software válido encontrado"}, status=400)

    from django.urls import reverse
    return JsonResponse({
        "sucesso": True,
        "criados": criados,
        "redirect": reverse("software_lista"),
    })
