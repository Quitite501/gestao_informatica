from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from django.utils import timezone
from .forms import SoftwareForm, SoftwareFiltroForm, LicencaContratoForm, InstalacaoSoftwareForm
from .models import Software, LicencaContrato, InstalacaoSoftware


@login_required
def licenca_dashboard(request):
    """Dashboard de licenças com status geral e alertas"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Métricas gerais
    total_softwares = Software.objects.count()
    softwares_controlados = Software.objects.filter(controlado=True).count()
    softwares_ativos = Software.objects.filter(ativo=True).count()
    softwares_inativos = Software.objects.filter(ativo=False).count()
    
    # Softwares com falta de licenças (saldo individual negativo)
    softwares_faltam = []
    for sw in Software.objects.filter(controlado=True):
        if sw.saldo < 0:
            softwares_faltam.append({
                'nome': sw.nome,
                'faltam': abs(sw.saldo)
            })

    # Comparativo Windows vs PCs
    from django.db.models import Sum, Q
    from patrimonio.models import ComputadorEspecificacao
    total_pcs = ComputadorEspecificacao.objects.count()
    licencas_windows = LicencaContrato.objects.filter(
        software__nome__icontains='windows'
    ).exclude(
        software__nome__icontains='server'
    ).exclude(
        software__nome__icontains='CAL'
    ).exclude(
        software__nome__icontains='sql'
    ).aggregate(total=Sum('quantidade_adquirida'))['total'] or 0
    diff_windows = licencas_windows - total_pcs
    
    # Contratos vencidos e próximos ao vencimento
    hoje = timezone.now().date()
    em_30_dias = hoje + timedelta(days=30)
    
    contratos_vencidos = LicencaContrato.objects.filter(
        data_vencimento__lt=hoje
    ).count()
    
    contratos_proximos = LicencaContrato.objects.filter(
        data_vencimento__gte=hoje,
        data_vencimento__lte=em_30_dias
    ).count()
    
    # Contexto para o template
    contexto = {
        'total_softwares': total_softwares,
        'softwares_controlados': softwares_controlados,
        'softwares_ativos': softwares_ativos,
        'softwares_inativos': softwares_inativos,
        'softwares_faltam': softwares_faltam,
        'contratos_vencidos': contratos_vencidos,
        'contratos_proximos': contratos_proximos,
        'total_pcs': total_pcs,
        'licencas_windows': licencas_windows,
        'diff_windows': diff_windows,
    }
    
    return render(request, 'licencas/licenca_dashboard.html', contexto)


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
        if form_filtro.cleaned_data.get("ativo") == "true":
            softwares = softwares.filter(ativo=True)
        elif form_filtro.cleaned_data.get("ativo") == "false":
            softwares = softwares.filter(ativo=False)

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
        qtd_utilizada = int(request.POST.get("quantidade_utilizada", 0) or 0)
        contrato = LicencaContrato.objects.create(
            software=software,
            quantidade_adquirida=qtd,
            quantidade_utilizada=qtd_utilizada,
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


@login_required
def software_gerenciar(request):
    """Página de gerenciamento de softwares com busca"""
    q = request.GET.get('q', '').strip()
    softwares = Software.objects.all()
    
    if q:
        softwares = softwares.filter(nome__icontains=q)
    
    softwares = softwares.order_by('nome')
    
    return render(request, 'licencas/software_gerenciar.html', {
        'softwares': softwares,
        'q': q,
    })


@login_required
def relatorio_customizado(request):
    """Gerador de relatórios customizados de auditoria de licenças"""
    from django.http import HttpResponse
    from django.db.models import Q
    import csv
    
    categorias = {
        'windows': 'Windows (SO)',
        'office': 'Microsoft Office',
        'banco_dados': 'Banco de Dados',
        'antivirus': 'Antivírus/Segurança',
        'desenvolvimento': 'Desenvolvimento',
        'todos': 'Todos',
    }
    
    tipos_analise = {
        'faltam': 'Softwares com FALTA de licenças',
        'excesso': 'Softwares com EXCESSO de licenças',
        'conformidade': 'Conformidade Geral',
        'comparativo': 'Comparativo Adquiridas vs Instaladas',
        'todos': 'Todos os Softwares',
    }
    
    if request.method == 'GET':
        fabricantes = Software.objects.filter(
            fabricante__isnull=False
        ).values_list('fabricante', flat=True).distinct().order_by('fabricante')
        
        return render(request, 'licencas/relatorio_customizado.html', {
            'categorias': categorias,
            'tipos_analise': tipos_analise,
            'fabricantes': list(fabricantes),
        })
    
    elif request.method == 'POST':
        categoria = request.POST.get('categoria', 'todos')
        tipo_analise = request.POST.get('tipo_analise', 'todos')
        fabricante = request.POST.get('fabricante', '')
        ativo = request.POST.get('ativo', 'todos')
        formato = request.POST.get('formato', 'html')
        
        # Filtrar softwares
        softwares = Software.objects.all()
        
        # Por categoria
        if categoria == 'windows':
            softwares = softwares.filter(nome__icontains='windows')
        elif categoria == 'office':
            softwares = softwares.filter(nome__icontains='office')
        elif categoria == 'banco_dados':
            softwares = softwares.filter(Q(nome__icontains='sql') | Q(nome__icontains='oracle') | Q(nome__icontains='mysql'))
        elif categoria == 'antivirus':
            softwares = softwares.filter(Q(nome__icontains='antivírus') | Q(nome__icontains='security'))
        elif categoria == 'desenvolvimento':
            softwares = softwares.filter(Q(nome__icontains='visual') | Q(nome__icontains='java') | Q(nome__icontains='python'))
        
        # Por fabricante
        if fabricante:
            softwares = softwares.filter(fabricante=fabricante)
        
        # Por status
        if ativo == 'ativo':
            softwares = softwares.filter(ativo=True)
        elif ativo == 'inativo':
            softwares = softwares.filter(ativo=False)
        
        softwares = softwares.order_by('nome')
        
        # Filtrar por tipo de análise
        resultado = []
        for sw in softwares:
            saldo = sw.total_adquirido - sw.total_instalado
            include = False
            
            if tipo_analise == 'faltam' and saldo < 0:
                include = True
            elif tipo_analise == 'excesso' and saldo > 0:
                include = True
            elif tipo_analise in ['conformidade', 'comparativo', 'todos']:
                include = True
            
            if include:
                resultado.append(sw)
        
        # PDF export
        if formato == 'pdf':
            from django.urls import reverse
            params = f"?categoria={categoria}&tipo_analise={tipo_analise}&fabricante={fabricante}&ativo={ativo}"
            return redirect(reverse('relatorio_customizado_pdf') + params)
        
        # CSV export
        elif formato == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="relatorio_licencas.csv"'
            response.write('\ufeff')  # BOM para Excel
            writer = csv.writer(response)
            writer.writerow(['Software', 'Fabricante', 'Adquiridas', 'Instaladas', 'Saldo', 'Situação', 'Status'])
            
            for sw in resultado:
                saldo = sw.total_adquirido - sw.total_instalado
                situacao = 'OK' if saldo == 0 else ('FALTAM' if saldo < 0 else 'SOBRAM')
                writer.writerow([sw.nome, sw.fabricante or '-', sw.total_adquirido, sw.total_instalado, saldo, situacao, 'Ativo' if sw.ativo else 'Inativo'])
            
            return response
        
        # Calcular estatísticas
        total_softwares = len(resultado)
        com_falta = sum(1 for sw in resultado if (sw.total_adquirido - sw.total_instalado) < 0)
        com_excesso = sum(1 for sw in resultado if (sw.total_adquirido - sw.total_instalado) > 0)
        total_adquiridas = sum(sw.total_adquirido for sw in resultado)
        total_instaladas = sum(sw.total_instalado for sw in resultado)

        # HTML
        return render(request, 'licencas/relatorio_customizado_resultado.html', {
            'softwares': resultado,
            'categoria': categoria,
            'tipo_analise': tipo_analise,
            'categoria_label': categorias.get(categoria, ''),
            'tipo_analise_label': tipos_analise.get(tipo_analise, ''),
            'fabricante': fabricante,
            'ativo': ativo,
            'total_softwares': total_softwares,
            'com_falta': com_falta,
            'com_excesso': com_excesso,
            'total_adquiridas': total_adquiridas,
            'total_instaladas': total_instaladas,
        })

@login_required
def relatorio_customizado_pdf(request):
    """Gerar PDF do relatório customizado de licenças"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.http import HttpResponse
    from django.db.models import Q
    from datetime import datetime

    try:
        from patrimonio.models import ConfigCartorio
        config_cartorio = ConfigCartorio.objects.first() or ConfigCartorio()
        logo_path = None
        if config_cartorio.logo:
            logo_path = f"file://{config_cartorio.logo.path}"
    except Exception:
        config_cartorio = None
        logo_path = None

    # Parâmetros via GET (passados como query string)
    categoria = request.GET.get('categoria', 'todos')
    tipo_analise = request.GET.get('tipo_analise', 'todos')
    fabricante = request.GET.get('fabricante', '')
    ativo = request.GET.get('ativo', 'todos')

    categorias_labels = {
        'windows': 'Windows (SO)',
        'office': 'Microsoft Office',
        'banco_dados': 'Banco de Dados',
        'antivirus': 'Antivírus/Segurança',
        'desenvolvimento': 'Desenvolvimento',
        'todos': 'Todos',
    }
    tipos_analise_labels = {
        'faltam': 'Softwares com FALTA de licenças',
        'excesso': 'Softwares com EXCESSO de licenças',
        'conformidade': 'Conformidade Geral',
        'comparativo': 'Comparativo Adquiridas vs Instaladas',
        'todos': 'Todos os Softwares',
    }

    softwares = Software.objects.all()
    if categoria == 'windows':
        softwares = softwares.filter(nome__icontains='windows')
    elif categoria == 'office':
        softwares = softwares.filter(nome__icontains='office')
    elif categoria == 'banco_dados':
        softwares = softwares.filter(Q(nome__icontains='sql') | Q(nome__icontains='oracle') | Q(nome__icontains='mysql'))
    elif categoria == 'antivirus':
        softwares = softwares.filter(Q(nome__icontains='antivírus') | Q(nome__icontains='security'))
    elif categoria == 'desenvolvimento':
        softwares = softwares.filter(Q(nome__icontains='visual') | Q(nome__icontains='java') | Q(nome__icontains='python'))

    if fabricante:
        softwares = softwares.filter(fabricante=fabricante)
    if ativo == 'ativo':
        softwares = softwares.filter(ativo=True)
    elif ativo == 'inativo':
        softwares = softwares.filter(ativo=False)

    softwares = softwares.order_by('nome')

    resultado = []
    for sw in softwares:
        saldo = sw.total_adquirido - sw.total_instalado
        if tipo_analise == 'faltam' and saldo < 0:
            resultado.append(sw)
        elif tipo_analise == 'excesso' and saldo > 0:
            resultado.append(sw)
        elif tipo_analise in ['conformidade', 'comparativo', 'todos']:
            resultado.append(sw)

    html_string = render_to_string(
        'licencas/relatorio_customizado_pdf.html',
        {
            'softwares': resultado,
            'categoria_label': categorias_labels.get(categoria, ''),
            'tipo_analise_label': tipos_analise_labels.get(tipo_analise, ''),
            'fabricante': fabricante,
            'ativo': ativo,
            'config_cartorio': config_cartorio,
            'logo_path': logo_path,
            'usuario': request.user,
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
        request=request,
    )

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_licencas_{datetime.now().strftime("%d_%m_%Y")}.pdf"'
    return response


@login_required
def nota_fiscal_data_ajax(request):
    """Retorna data de emissão da nota fiscal para preencher data_aquisicao"""
    from django.http import JsonResponse
    pk = request.GET.get('pk')
    if not pk:
        return JsonResponse({'erro': 'ID não informado'}, status=400)
    try:
        from notas_fiscais.models import NotaFiscal
        nf = NotaFiscal.objects.get(pk=pk)
        return JsonResponse({'data_emissao': nf.data_emissao.strftime('%Y-%m-%d')})
    except Exception:
        return JsonResponse({'erro': 'Nota fiscal não encontrada'}, status=404)


@login_required
def software_busca_ajax(request):
    """Busca softwares para Select2"""
    from django.http import JsonResponse
    q = request.GET.get('q', '').strip()
    softwares = Software.objects.filter(ativo=True)
    if q:
        softwares = softwares.filter(nome__icontains=q)
    softwares = softwares.order_by('nome')[:30]
    resultados = [
        {'id': sw.nome, 'text': f"{sw.nome}", 'fabricante': sw.fabricante or ''}
        for sw in softwares
    ]
    fabricantes = list(
        Software.objects.filter(ativo=True, fabricante__isnull=False)
        .values_list('fabricante', flat=True)
        .distinct().order_by('fabricante')
    )
    return JsonResponse({'results': resultados, 'fabricantes': fabricantes})
