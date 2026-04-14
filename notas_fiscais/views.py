from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NotaFiscalForm, NotaFiscalFiltroForm
from .models import NotaFiscal


@login_required
def nota_fiscal_lista(request):
    form_filtro = NotaFiscalFiltroForm(request.GET or None)
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
        form.save()
        return redirect("nota_fiscal_detalhe", pk=nota.pk)
    return render(request, "notas_fiscais/nota_fiscal_form.html", {
        "form": form,
        "titulo": f"Editar Nota Fiscal: {nota.numero}",
    })
