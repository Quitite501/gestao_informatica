from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from .forms import NotaFiscalForm, NotaFiscalFiltroForm
from .models import NotaFiscal


@login_required
def nota_fiscal_lista(request):
    # ── Limpar filtros ────────────────────────────────────────────────
    if "limpar" in request.GET:
        request.session.pop("nota_fiscal_filtros", None)
        return redirect("nota_fiscal_lista")

    # ── Salvar filtros na sessão e redirecionar para URL limpa ────────
    if request.GET:
        request.session["nota_fiscal_filtros"] = {
            k: request.GET.getlist(k) for k in request.GET.keys()
        }
        return redirect("nota_fiscal_lista")

    # ── Reconstruir filtros da sessão ─────────────────────────────────
    from django.http import QueryDict
    filtros_salvos = request.session.get("nota_fiscal_filtros", {})
    qd = QueryDict(mutable=True).copy()
    for k, v in filtros_salvos.items():
        if isinstance(v, list):
            for item in v:
                qd.appendlist(k, item)
        else:
            qd[k] = v

    form_filtro = NotaFiscalFiltroForm(qd or None)
    notas = NotaFiscal.objects.all()

    if form_filtro.is_valid():
        if form_filtro.cleaned_data.get("numero"):
            notas = notas.filter(numero__icontains=form_filtro.cleaned_data["numero"])
        if form_filtro.cleaned_data.get("fornecedor"):
            notas = notas.filter(fornecedor__icontains=form_filtro.cleaned_data["fornecedor"])
        if form_filtro.cleaned_data.get("data_de"):
            notas = notas.filter(data_emissao__gte=form_filtro.cleaned_data["data_de"])
        if form_filtro.cleaned_data.get("data_ate"):
            notas = notas.filter(data_emissao__lte=form_filtro.cleaned_data["data_ate"])

    notas = notas.order_by("-data_emissao")

    return render(request, "notas_fiscais/nota_fiscal_lista.html", {
        "notas": notas,
        "form_filtro": form_filtro,
    })


@login_required
def nota_fiscal_detalhe(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    patrimonios = nota.patrimonios.select_related("tipo", "usuario_atual").all()
    licencas = nota.licencas.select_related("software").all()
    return render(request, "notas_fiscais/nota_fiscal_detalhe.html", {
        "nota": nota,
        "patrimonios": patrimonios,
        "licencas": licencas,
    })


@login_required
@permission_required("notas_fiscais.add_notafiscal", raise_exception=True)
def nota_fiscal_nova(request):
    form = NotaFiscalForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        nota = form.save(commit=False)
        nota.criado_por = request.user
        nota.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "NotaFiscal", nota.pk, f"Nota fiscal {nota.numero} cadastrada.")
        return redirect("nota_fiscal_detalhe", pk=nota.pk)
    return render(request, "notas_fiscais/nota_fiscal_form.html", {
        "form": form,
        "titulo": "Nova Nota Fiscal",
    })


@login_required
@permission_required("notas_fiscais.change_notafiscal", raise_exception=True)
def nota_fiscal_editar(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    form = NotaFiscalForm(request.POST or None, request.FILES or None, instance=nota)
    if form.is_valid():
        nota = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "NotaFiscal", nota.pk, f"Nota fiscal {nota.numero} editada.")
        return redirect("nota_fiscal_detalhe", pk=nota.pk)
    return render(request, "notas_fiscais/nota_fiscal_form.html", {
        "form": form,
        "titulo": f"Editar Nota Fiscal: {nota.numero}",
    })


@login_required
@permission_required("notas_fiscais.add_notafiscal", raise_exception=True)
def nota_fiscal_importar(request):
    """Importa NF via XML ou PDF e pré-preenche o formulário"""
    from .extrator import extrair_nota_fiscal
    import json

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return render(request, "notas_fiscais/nota_fiscal_importar.html", {
                "erro": "Nenhum arquivo enviado."
            })
        
        resultado = extrair_nota_fiscal(arquivo, arquivo.name)
        
        if not resultado.get("sucesso"):
            return render(request, "notas_fiscais/nota_fiscal_importar.html", {
                "erro": f"Erro ao processar arquivo: {resultado.get('erro')}",
                "dica": "Verifique se o arquivo é um XML NF-e válido ou um PDF com texto extraível."
            })
        
        # Pré-preencher formulário com dados extraídos
        dados = {
            "numero": resultado.get("numero") or "",
            "fornecedor": resultado.get("fornecedor") or "",
            "data_emissao": resultado.get("data_emissao") or "",
            "valor_total": resultado.get("valor_total") or "",
        }
        form = NotaFiscalForm(initial=dados)
        
        return render(request, "notas_fiscais/nota_fiscal_form.html", {
            "form": form,
            "titulo": "Importar Nota Fiscal",
            "dados_importados": resultado,
            "itens": resultado.get("itens", []),
            "fonte": resultado.get("fonte"),
        })
    
    return render(request, "notas_fiscais/nota_fiscal_importar.html")
