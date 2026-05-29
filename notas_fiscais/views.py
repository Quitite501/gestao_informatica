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
        
        # Salvar itens de software na sessão para tela de vincular licenças
        import json
        itens_json = request.POST.get("itens_software_json", "")
        if itens_json:
            try:
                request.session["itens_software_sugeridos"] = json.loads(itens_json)
            except Exception:
                pass
        
        return redirect("nota_fiscal_vincular_licencas", pk=nota.pk)
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
        
        # Detectar itens de software
        from .extrator import detectar_itens_software
        itens = resultado.get("itens", [])
        itens_analisados = detectar_itens_software(itens)
        itens_software = [i for i in itens_analisados if i['is_software']]
        
        # Pré-preencher formulário com dados extraídos
        dados = {
            "numero": resultado.get("numero") or "",
            "fornecedor": resultado.get("fornecedor") or "",
            "data_emissao": resultado.get("data_emissao") or "",
            "valor_total": resultado.get("valor_total") or "",
        }
        form = NotaFiscalForm(initial=dados)
        
        import json as _json
        return render(request, "notas_fiscais/nota_fiscal_form.html", {
            "form": form,
            "titulo": "Importar Nota Fiscal",
            "dados_importados": resultado,
            "itens": itens_analisados,
            "itens_software": _json.dumps(itens_software, ensure_ascii=False),
            "fonte": resultado.get("fonte"),
        })
    
    return render(request, "notas_fiscais/nota_fiscal_importar.html")


@login_required
@permission_required("notas_fiscais.add_notafiscal", raise_exception=True)
def nota_fiscal_vincular_licencas(request, pk):
    """Vincula licenças de software a uma NF após o cadastro"""
    from licencas.models import Software, LicencaContrato

    nota = get_object_or_404(NotaFiscal, pk=pk)

    if request.method == "POST":
        criadas = 0
        erros = []

        # Unificar itens numerados + manual
        indices = set()
        for key in request.POST.keys():
            if key.startswith("software_"):
                indices.add(key.replace("software_", ""))
        
        for idx in indices:
            nome = request.POST.get(f"software_{idx}", "").strip()
            fabricante = request.POST.get(f"fabricante_{idx}", "").strip()
            versao = request.POST.get(f"versao_{idx}", "").strip()
            tipo = request.POST.get(f"tipo_{idx}", "perpétua")
            qtd = request.POST.get(f"qtd_{idx}", "1")
            chave = request.POST.get(f"chave_{idx}", "").strip()

            if not nome:
                continue

            try:
                qtd = int(qtd)
            except (ValueError, TypeError):
                qtd = 1

            try:
                # Buscar ou criar Software
                software, _ = Software.objects.get_or_create(
                    nome=nome,
                    versao=versao or None,
                    fabricante=fabricante or None,
                    defaults={"tipo_licenca": tipo, "controlado": True}
                )

                # Criar LicencaContrato vinculado à NF
                if not LicencaContrato.objects.filter(software=software, nota_fiscal=nota).exists():
                    LicencaContrato.objects.create(
                        software=software,
                        nota_fiscal=nota,
                        quantidade_adquirida=qtd,
                        chave_licenca=chave or None,
                        data_aquisicao=nota.data_emissao,
                        criado_por=request.user,
                    )
                    criadas += 1
            except Exception as e:
                erros.append(f"{nome}: {e}")

        if erros:
            msg = f"{criadas} licença(s) criada(s). Erros: {', '.join(erros)}"
        else:
            msg = f"{criadas} licença(s) criada(s) e vinculada(s) à NF."

        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "LicencaContrato", nota.pk,
            f"Licenças vinculadas à NF {nota.numero}: {msg}")

        return redirect("nota_fiscal_detalhe", pk=nota.pk)

    # GET: mostrar formulário de vinculação
    licencas_existentes = nota.licencas.select_related("software").all()
    softwares_disponiveis = Software.objects.filter(ativo=True).order_by("nome")

    # Itens sugeridos da sessão (vindos da importação)
    itens_software = request.session.pop("itens_software_sugeridos", [])

    return render(request, "notas_fiscais/nota_fiscal_vincular_licencas.html", {
        "nota": nota,
        "licencas_existentes": licencas_existentes,
        "softwares_disponiveis": softwares_disponiveis,
        "itens_software": itens_software,
    })


@login_required
def nota_fiscal_extrair_ajax(request):
    """Endpoint AJAX: extrai dados da NF e retorna JSON"""
    from django.http import JsonResponse
    from .extrator import extrair_nota_fiscal, detectar_itens_software

    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido"}, status=405)

    arquivo = request.FILES.get("arquivo")
    if not arquivo:
        return JsonResponse({"erro": "Nenhum arquivo enviado"}, status=400)

    resultado = extrair_nota_fiscal(arquivo, arquivo.name)

    if not resultado.get("sucesso"):
        return JsonResponse({
            "sucesso": False,
            "erro": resultado.get("erro", "Erro desconhecido"),
        }, status=400)

    itens = detectar_itens_software(resultado.get("itens", []))

    return JsonResponse({
        "sucesso": True,
        "tipo": resultado.get("tipo", ""),
        "fonte": resultado.get("fonte", ""),
        "numero": resultado.get("numero") or "",
        "fornecedor": resultado.get("fornecedor") or "",
        "data_emissao": resultado.get("data_emissao") or "",
        "valor_total": resultado.get("valor_total") or "",
        "itens": itens,
        "itens_software": [i for i in itens if i.get("is_software")],
    })


@login_required
def nota_fiscal_pdf_consolidado(request):
    """Mescla todos os PDFs de notas fiscais em um único arquivo."""
    from pypdf import PdfWriter
    import io
    from django.http import HttpResponse
    from datetime import datetime

    nfs = NotaFiscal.objects.exclude(
        arquivo_pdf=''
    ).exclude(
        arquivo_pdf__isnull=True
    ).order_by('data_emissao')

    writer = PdfWriter()
    incluidos = 0

    for nf in nfs:
        try:
            writer.append(nf.arquivo_pdf.path)
            incluidos += 1
        except Exception:
            continue

    if incluidos == 0:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, "Nenhum PDF encontrado para consolidar.")
        return redirect("nota_fiscal_lista")

    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="notas_fiscais_consolidado_'
        f'{datetime.now().strftime("%d_%m_%Y")}.pdf"'
    )
    return response
