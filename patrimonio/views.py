from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .forms import PatrimonioForm, PatrimonioFiltroForm, ComputadorEspecificacaoForm, ComputadorCompletoForm
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria
from .models import Patrimonio, MovimentacaoPatrimonio, ComputadorEspecificacao


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


# ────────────────────────────────────────────────────────────────────────────
# COMPUTADOR ESPECIFICAÇÃO (CRUD + Relatório de Auditoria)
# ────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required("patrimonio.can_manage_patrimonio", raise_exception=True)
def computador_novo(request):
    form = ComputadorEspecificacaoForm(request.POST or None)
    if form.is_valid():
        computador = form.save()
        registrar_auditoria(request, RegistroAuditoria.ACAO_CRIACAO, "ComputadorEspecificacao", computador.pk,
            f"Especificação do computador {computador.patrimonio.etiqueta} cadastrada.")
        return redirect("computador_detalhe", pk=computador.pk)
    return render(request, "patrimonio/computador_form.html", {
        "form": form,
        "titulo": "Novo Computador",
    })


@login_required
def computador_detalhe(request, pk):
    from .models import ComputadorEspecificacao
    computador = get_object_or_404(ComputadorEspecificacao, pk=pk)
    return render(request, "patrimonio/computador_detalhe.html", {
        "computador": computador,
        "patrimonio": computador.patrimonio,
    })


@login_required
@permission_required("patrimonio.can_manage_patrimonio", raise_exception=True)
def computador_editar(request, pk):
    from .models import ComputadorEspecificacao
    computador = get_object_or_404(ComputadorEspecificacao, pk=pk)
    form = ComputadorCompletoForm(request.POST or None, instance=computador)
    if form.is_valid():
        computador = form.save()
        form.salvar_patrimonio(computador)
        registrar_auditoria(request, RegistroAuditoria.ACAO_EDICAO, "ComputadorEspecificacao", computador.pk,
            f"Computador {computador.patrimonio.etiqueta} editado (dados técnicos e patrimônio).")
        return redirect("computador_detalhe", pk=computador.pk)
    return render(request, "patrimonio/computador_form.html", {
        "form": form,
        "titulo": f"Editar Computador: {computador.patrimonio.etiqueta}",
        "computador": computador,
    })


def normalizar_so(so_name):
    """Normaliza nome do S.O. para agrupar variações"""
    import re
    if not so_name:
        return "Desconhecido"
    
    # Windows Server (antes do Windows genérico)
    if 'Windows' in so_name and 'Server' in so_name:
        match = re.search(r'Server (\d+)', so_name)
        if match:
            return f"Windows Server {match.group(1)}"
        return "Windows Server"

    # Windows
    if 'Windows' in so_name or 'windows' in so_name.lower():
        # Extrair versão principal (Windows 11, Windows 10, etc)
        match = re.search(r'Windows (\d+)', so_name)
        if match:
            versao = match.group(1)
            # Extrair edição (Pro, Home, Enterprise, etc)
            if 'Pro' in so_name:
                return f"Windows {versao} Pro"
            elif 'Enterprise' in so_name:
                return f"Windows {versao} Enterprise"
            elif 'Home' in so_name:
                return f"Windows {versao} Home"
            else:
                return f"Windows {versao}"
        return "Windows"
    
    # Linux
    if 'Linux' in so_name or 'linux' in so_name.lower():
        if 'Ubuntu' in so_name:
            match = re.search(r'Ubuntu (\d+\.\d+)', so_name)
            if match:
                return f"Ubuntu {match.group(1)}"
            return "Ubuntu"
        elif 'Mint' in so_name:
            match = re.search(r'Mint (\d+\.\d+)', so_name)
            if match:
                return f"Linux Mint {match.group(1)}"
            return "Linux Mint"
        elif 'CentOS' in so_name or 'RedHat' in so_name:
            return "RedHat/CentOS"
        elif 'Debian' in so_name:
            import re as _re
            m = _re.search(r'Debian GNU/Linux (\d+)', so_name)
            if m:
                return f'Debian GNU/Linux {m.group(1)}'
            return 'Debian'
        else:
            return "Linux"
    
    # macOS
    if 'macOS' in so_name or 'Mac' in so_name or 'Darwin' in so_name:
        match = re.search(r'(\d+\.\d+)', so_name)
        if match:
            return f"macOS {match.group(1)}"
        return "macOS"
    
    return so_name


@login_required
def relatorio_computadores(request):
    """Relatório de auditoria de computadores cadastrados."""
    from .models import ComputadorEspecificacao
    from django.core.paginator import Paginator
    from datetime import datetime
    from django.db.models import Q, Count
    
    computadores = ComputadorEspecificacao.objects.select_related(
        "patrimonio", "patrimonio__tipo", "patrimonio__setor", "patrimonio__usuario_atual"
    ).order_by("patrimonio__etiqueta")
    
    # Filtros
    hostname = request.GET.get("hostname", "").strip()
    usuario = request.GET.get("usuario", "").strip()
    setor = request.GET.get("setor", "").strip()
    
    if hostname:
        computadores = computadores.filter(
            Q(hostname__icontains=hostname) | 
            Q(patrimonio__hostname__icontains=hostname)
        )
    if usuario:
        computadores = computadores.filter(patrimonio__usuario_atual__username__icontains=usuario)
    if setor:
        computadores = computadores.filter(patrimonio__setor__id=setor)
    
    # Estatísticas
    total = computadores.count()
    
    # Contar por S.O normalizado
    so_stats_raw = computadores.values('sistema_operacional').annotate(
        count=Count('id')
    ).order_by('sistema_operacional')
    
    # Normalizar e agrupar
    so_normalized = {}
    so_grouped = {}
    
    for so in so_stats_raw:
        so_original = so['sistema_operacional'] or 'Desconhecido'
        so_normalizado = normalizar_so(so_original)
        
        # Agrupar por nome normalizado
        if so_normalizado not in so_normalized:
            so_normalized[so_normalizado] = {'count': 0, 'original': so_original}
        so_normalized[so_normalizado]['count'] += so['count']
    
    # Categorizar por tipo
    for so_nome, so_data in so_normalized.items():
        if 'Windows Server' in so_nome:
            tipo = 'Windows Server'
        elif 'Windows' in so_nome:
            tipo = 'Windows'
        elif 'Linux' in so_nome or 'Ubuntu' in so_nome or 'Debian' in so_nome:
            tipo = 'Linux'
        elif 'macOS' in so_nome:
            tipo = 'macOS'
        else:
            tipo = 'Outro'
        
        if tipo not in so_grouped:
            so_grouped[tipo] = []
        so_grouped[tipo].append({'sistema_operacional': so_nome, 'count': so_data['count']})
    
    # Ordenar grupos e itens dentro deles (itens por quantidade decrescente)
    so_stats = []
    ordem = ['Windows', 'Windows Server', 'Linux', 'macOS', 'Outro']
    for tipo in ordem:
        if tipo in so_grouped:
            items_ordenados = sorted(so_grouped[tipo], key=lambda x: x['count'], reverse=True)
            so_stats.append({'tipo': tipo, 'items': items_ordenados})
    
    # Verificação
    total_so = sum(so['count'] for so in so_stats_raw)
    so_valido = total_so == total
    
    # Usuários
    usuarios_stats = computadores.filter(
        patrimonio__usuario_atual__isnull=False
    ).values('patrimonio__usuario_atual__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Paginação
    paginator = Paginator(computadores, 15)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    from usuarios.models import Setor
    setores = Setor.objects.filter(ativo=True).order_by("nome")
    
    return render(request, "patrimonio/relatorio_computadores.html", {
        "page": page,
        "computadores": page.object_list,
        "paginator": paginator,
        "total": total,
        "so_stats": so_stats,
        "so_valido": so_valido,
        "total_so": total_so,
        "usuarios_stats": usuarios_stats,
        "setores": setores,
        "filtros": {"hostname": hostname, "usuario": usuario, "setor": setor},
    })
@login_required
def relatorio_computadores_csv(request):
    """Export de auditoria de computadores em CSV."""
    import csv
    from django.http import HttpResponse
    from .models import ComputadorEspecificacao
    
    computadores = ComputadorEspecificacao.objects.select_related(
        "patrimonio", "patrimonio__tipo", "patrimonio__setor", "patrimonio__usuario_atual"
    ).order_by("patrimonio__etiqueta")
    
    # Filtros
    so = request.GET.get("so", "").strip()
    ip = request.GET.get("ip", "").strip()
    mac = request.GET.get("mac", "").strip()
    
    if so:
        computadores = computadores.filter(sistema_operacional__icontains=so)
    if ip:
        computadores = computadores.filter(endereco_ip=ip)
    if mac:
        computadores = computadores.filter(endereco_mac__icontains=mac)
    
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="auditoria_computadores.csv"'
    response.write("\ufeff")  # BOM para UTF-8
    
    writer = csv.writer(response)
    writer.writerow(["Etiqueta", "Hostname", "Tipo", "Setor", "Usuário", "RAM (GB)", "S.O.", "IP", "MAC", "Processador", "Data"])
    
    for c in computadores:
        writer.writerow([
            c.patrimonio.etiqueta,
            c.patrimonio.hostname or "",
            c.patrimonio.tipo.nome if c.patrimonio.tipo else "",
            c.patrimonio.setor.nome if c.patrimonio.setor else "",
            c.patrimonio.usuario_atual.nome_completo if c.patrimonio.usuario_atual else "",
            c.ram_gb or "",
            c.sistema_operacional or "",
            c.endereco_ip or "",
            c.endereco_mac or "",
            c.processador or "",
            c.atualizado_em.strftime("%d/%m/%Y %H:%M"),
        ])
    
    return response


@login_required
def relatorio_computadores_pdf(request):
    """Export de auditoria de computadores em PDF (paisagem com cards)."""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.http import HttpResponse
    from .models import ComputadorEspecificacao, ConfigCartorio
    from datetime import datetime
    from django.db.models import Q, Count
    
    computadores = ComputadorEspecificacao.objects.select_related(
        "patrimonio", "patrimonio__tipo", "patrimonio__setor", "patrimonio__usuario_atual"
    ).order_by("patrimonio__etiqueta")
    
    # Filtros novos
    hostname = request.GET.get("hostname", "").strip()
    usuario = request.GET.get("usuario", "").strip()
    
    if hostname:
        computadores = computadores.filter(
            Q(hostname__icontains=hostname) | 
            Q(patrimonio__hostname__icontains=hostname)
        )
    if usuario:
        computadores = computadores.filter(patrimonio__usuario_atual__username__icontains=usuario)
    
    # Estatísticas
    total = computadores.count()
    # Mesmo agrupamento da view web
    so_stats_raw = computadores.values('sistema_operacional').annotate(
        count=Count('id')
    ).order_by('sistema_operacional')
    
    so_normalized = {}
    so_grouped = {}
    
    for so in so_stats_raw:
        so_original = so['sistema_operacional'] or 'Desconhecido'
        so_normalizado = normalizar_so(so_original)
        if so_normalizado not in so_normalized:
            so_normalized[so_normalizado] = {'count': 0}
        so_normalized[so_normalizado]['count'] += so['count']
    
    for so_nome, so_data in so_normalized.items():
        if 'Windows Server' in so_nome:
            tipo = 'Windows Server'
        elif 'Windows' in so_nome:
            tipo = 'Windows'
        elif 'Linux' in so_nome or 'Ubuntu' in so_nome or 'Debian' in so_nome:
            tipo = 'Linux'
        elif 'macOS' in so_nome:
            tipo = 'macOS'
        else:
            tipo = 'Outro'
        if tipo not in so_grouped:
            so_grouped[tipo] = []
        so_grouped[tipo].append({'sistema_operacional': so_nome, 'count': so_data['count']})
    
    so_stats = []
    for tipo in ['Windows', 'Windows Server', 'Linux', 'macOS', 'Outro']:
        if tipo in so_grouped:
            so_stats.append({'tipo': tipo, 'items': sorted(so_grouped[tipo], key=lambda x: x['count'], reverse=True)})
    
    total_so = sum(so['count'] for so in so_stats_raw)
    so_valido = total_so == total
    
    usuarios_stats = computadores.filter(
        patrimonio__usuario_atual__isnull=False
    ).values('patrimonio__usuario_atual__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Carregar configuração do cartório
    config_cartorio = ConfigCartorio.objects.first() or ConfigCartorio()
    
    # Caminho absoluto para weasyprint carregar a imagem
    logo_path = None
    if config_cartorio.logo:
        import os
        logo_path = f"file://{config_cartorio.logo.path}"
    
    html_string = render_to_string(
        "patrimonio/relatorio_computadores_pdf.html",
        {
            "computadores": computadores,
            "total": total,
            "so_stats": so_stats,
            "so_valido": so_valido,
            "total_so": total_so,
            "usuarios_stats": usuarios_stats,
            "usuario": request.user,
            "config_cartorio": config_cartorio,
            "logo_path": logo_path,
            "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
        request=request,
    )
    
    # PDF em paisagem
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        page_size=('A4', 'landscape')
    )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="auditoria_computadores_%s.pdf"' % datetime.now().strftime("%d_%m_%Y")
    return response
@login_required
def computador_deletar(request, pk):
    """Deletar ComputadorEspecificacao."""
    from .models import ComputadorEspecificacao
    computador = get_object_or_404(ComputadorEspecificacao, pk=pk)
    
    if request.method == "POST":
        etiqueta = computador.patrimonio.etiqueta
        patrimonio_id = computador.patrimonio.pk
        computador.delete()
        registrar_auditoria(request, RegistroAuditoria.ACAO_EXCLUSAO, "ComputadorEspecificacao", patrimonio_id,
            f"Computador {etiqueta} deletado do sistema.")
        return redirect("relatorio_computadores")
    
    return render(request, "patrimonio/computador_confirmar_delecao.html", {
        "computador": computador,
    })
