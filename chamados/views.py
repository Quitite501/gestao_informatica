from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .forms import ChamadoForm, ChamadoFiltroForm, ChamadoEncerramentoForm, ChamadoEditarTituloForm, ChamadoTransferirForm
from .models import Chamado, AnexoChamado, AcaoChamado, AnexoAcao, ConfiguracaoSLA
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria



@login_required
def chamado_dashboard(request):
    from django.db.models import Count
    from datetime import timedelta
    hoje = timezone.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())

    # KPI cards
    total_abertos    = Chamado.objects.exclude(status=Chamado.STATUS_ENCERRADO).count()
    total_criticos   = Chamado.objects.filter(
        status__in=[Chamado.STATUS_ABERTO, Chamado.STATUS_EM_ATENDIMENTO],
        prioridade='critica'
    ).count()
    abertos_hoje     = Chamado.objects.filter(criado_em__date=hoje).count()
    abertos_semana   = Chamado.objects.filter(criado_em__date__gte=inicio_semana).count()

    # Por status (somente ativos)
    por_status = {
        'aberto':            Chamado.objects.filter(status=Chamado.STATUS_ABERTO).count(),
        'em_atendimento':    Chamado.objects.filter(status=Chamado.STATUS_EM_ATENDIMENTO).count(),
        'aguardando_usuario': Chamado.objects.filter(status=Chamado.STATUS_AGUARDANDO).count(),
        'encerrado_mes':     Chamado.objects.filter(
            status=Chamado.STATUS_ENCERRADO,
            encerrado_em__date__gte=hoje.replace(day=1)
        ).count(),
    }

    # Por prioridade (somente ativos)
    por_prioridade = {
        'critica': Chamado.objects.filter(prioridade='critica').exclude(status=Chamado.STATUS_ENCERRADO).count(),
        'alta':    Chamado.objects.filter(prioridade='alta').exclude(status=Chamado.STATUS_ENCERRADO).count(),
        'media':   Chamado.objects.filter(prioridade='media').exclude(status=Chamado.STATUS_ENCERRADO).count(),
        'baixa':   Chamado.objects.filter(prioridade='baixa').exclude(status=Chamado.STATUS_ENCERRADO).count(),
    }

    # SLA — calcular para cada chamado ativo
    chamados_ativos = Chamado.objects.exclude(status=Chamado.STATUS_ENCERRADO)
    sla_no_prazo = sla_em_risco = sla_vencido = 0
    for c in chamados_ativos:
        s = c.status_sla()
        if s == 'no_prazo':
            sla_no_prazo += 1
        elif s == 'em_risco':
            sla_em_risco += 1
        elif s == 'vencido':
            sla_vencido += 1

    # Por técnico (chamados ativos)
    from django.conf import settings
    from django.contrib.auth import get_user_model
    User = get_user_model()
    por_tecnico = (
        Chamado.objects
        .exclude(status=Chamado.STATUS_ENCERRADO)
        .values('tecnico__pk', 'tecnico__nome_completo')
        .annotate(total=Count('pk'))
        .order_by('-total')[:6]
    )

    # Últimos 7 dias — chamados abertos por dia
    ultimos_7 = []
    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)
        ultimos_7.append({
            'dia': dia.strftime('%a'),
            'data': dia.strftime('%d/%m'),
            'total': Chamado.objects.filter(criado_em__date=dia).count(),
        })
    max_dia = max((d['total'] for d in ultimos_7), default=1) or 1

    context = {
        'total_abertos':    total_abertos,
        'total_criticos':   total_criticos,
        'sla_vencido':      sla_vencido,
        'sla_em_risco':     sla_em_risco,
        'abertos_hoje':     abertos_hoje,
        'abertos_semana':   abertos_semana,
        'por_status':       por_status,
        'por_prioridade':   por_prioridade,
        'sla_no_prazo':     sla_no_prazo,
        'por_tecnico':      por_tecnico,
        'ultimos_7':        ultimos_7,
        'max_dia':          max_dia,
    }
    return render(request, 'chamados/chamado_dashboard.html', context)

@login_required
def chamado_lista(request):
    """
    Listagem de chamados com filtros múltiplos.
    Filtros são armazenados na sessão — URL permanece limpa.
    """
    from django.http import QueryDict

    # ── Limpar filtros ────────────────────────────────────────────────
    if "limpar" in request.GET:
        request.session.pop("chamado_filtros", None)
        return redirect("chamado_lista")

    # ── Receber filtros via GET e salvar na sessão ────────────────────
    if request.GET:
        # 'page' não é filtro — nunca salvar na sessão nem causar redirect
        filtros_novos = {k: request.GET.getlist(k) for k in request.GET.keys() if k != "page"}
        if filtros_novos:
            request.session["chamado_filtros"] = filtros_novos
            return redirect("chamado_lista")
        # Se só veio ?page=N, deixa prosseguir normalmente

    # ── Primeira carga sem sessão: aplica filtros padrão (ISO 20000) ──
    if "chamado_filtros" not in request.session:
        request.session["chamado_filtros"] = {"_filtro_padrao": True}

    # ── Reconstruir QueryDict a partir da sessão ─────────────────────
    filtros_salvos = request.session.get("chamado_filtros", {})
    qd = QueryDict(mutable=True)
    qd_copy = qd.copy()
    for k, v in filtros_salvos.items():
        if isinstance(v, list):
            for item in v:
                qd_copy.appendlist(k, item)
        else:
            qd_copy[k] = v

    form_filtro = ChamadoFiltroForm(qd_copy)
    chamados = Chamado.objects.select_related(
        "solicitante", "tecnico", "categoria"
    ).all()

    if form_filtro.is_valid():
        # Filtro múltiplo de status
        status_selecionados = form_filtro.cleaned_data.get("status")
        if status_selecionados:
            chamados = chamados.filter(status__in=status_selecionados)

        # Filtro múltiplo de categoria
        categorias_selecionadas = form_filtro.cleaned_data.get("categoria")
        if categorias_selecionadas:
            chamados = chamados.filter(categoria__in=categorias_selecionadas)

        # Filtro múltiplo de prioridade
        prioridades_selecionadas = form_filtro.cleaned_data.get("prioridade")
        if prioridades_selecionadas:
            chamados = chamados.filter(prioridade__in=prioridades_selecionadas)

        # Filtro por período
        if form_filtro.cleaned_data.get("data_inicio"):
            chamados = chamados.filter(
                criado_em__date__gte=form_filtro.cleaned_data["data_inicio"]
            )
        if form_filtro.cleaned_data.get("data_fim"):
            chamados = chamados.filter(
                criado_em__date__lte=form_filtro.cleaned_data["data_fim"]
            )

        # Filtro por nome do solicitante
        solicitante_nome = form_filtro.cleaned_data.get("solicitante_nome", "").strip()
        if solicitante_nome:
            chamados = chamados.filter(
                solicitante__nome_completo__icontains=solicitante_nome
            )

    # ── Filtro padrão ISO 20000: ativos sempre + encerrados 30 dias ──
    filtro_padrao_ativo = filtros_salvos.get("_filtro_padrao", False)
    if filtro_padrao_ativo:
        from datetime import date, timedelta
        data_corte = date.today() - timedelta(days=30)
        chamados = chamados.filter(
            Q(status__in=[
                Chamado.STATUS_ABERTO,
                Chamado.STATUS_EM_ATENDIMENTO,
                Chamado.STATUS_AGUARDANDO,
            ]) |
            Q(status=Chamado.STATUS_ENCERRADO,
              criado_em__date__gte=data_corte)
        )
    chamados = chamados.order_by("-criado_em")

    # ── Paginação ────────────────────────────────────────────────────
    from django.core.paginator import Paginator
    paginator   = Paginator(chamados, 15)
    page_number = request.GET.get("page")
    page_obj    = paginator.get_page(page_number)

    return render(
        request,
        "chamados/chamado_lista.html",
        {"chamados": page_obj, "form_filtro": form_filtro, "page_obj": page_obj, "filtro_padrao_ativo": filtro_padrao_ativo}
    )


@login_required
def chamado_detalhe(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    anexos = chamado.anexos.all()
    acoes = AcaoChamado.objects.filter(chamado=chamado).order_by("criado_em")
    for acao in acoes:
        acao.anexos_lista = AnexoAcao.objects.filter(acao=acao)
    return render(
        request,
        "chamados/chamado_detalhe.html",
        {"chamado": chamado, "anexos": anexos, "acoes": acoes}
    )



@login_required
def chamado_sla_previsao(request):
    categoria_id = request.GET.get("categoria")
    prioridade = request.GET.get("prioridade")

    prioridades_validas = dict(Chamado.PRIORIDADE_CHOICES)
    if prioridade not in prioridades_validas:
        return JsonResponse({
            "ok": False,
            "erro": "Prioridade invalida.",
        }, status=400)

    config = None

    if categoria_id:
        config = ConfiguracaoSLA.objects.filter(
            prioridade=prioridade,
            categoria_id=categoria_id,
        ).first()

    if config is None:
        config = ConfiguracaoSLA.objects.filter(
            prioridade=prioridade,
            categoria__isnull=True,
        ).first()

    prazo_horas = (
        config.prazo_horas
        if config
        else Chamado.PRAZO_PADRAO_HORAS.get(prioridade, 48)
    )

    from chamados.sla_utils import calcular_vencimento_sla

    vencimento = calcular_vencimento_sla(timezone.now(), prazo_horas * 60)
    vencimento_local = timezone.localtime(vencimento)

    return JsonResponse({
        "ok": True,
        "prioridade": prioridade,
        "prioridade_label": prioridades_validas[prioridade],
        "prazo_horas": prazo_horas,
        "prazo_texto": f"{prazo_horas} horas",
        "vencimento_iso": vencimento.isoformat(),
        "vencimento_formatado": vencimento_local.strftime("%d/%m/%Y %H:%M"),
    })

@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_novo(request):
    form = ChamadoForm(request.POST or None, user=request.user)
    if form.is_valid():
        chamado = form.save(commit=False)
        chamado.status = Chamado.STATUS_ABERTO
        chamado.save()
        
        for arquivo in request.FILES.getlist("anexos"):
            AnexoChamado.objects.create(
                chamado=chamado,
                arquivo=arquivo,
                nome_original=arquivo.name,
            )
        
        return redirect("chamado_detalhe", pk=chamado.pk)
    
    return render(
        request,
        "chamados/chamado_form.html",
        {"form": form, "titulo": "Novo Chamado"}
    )


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
def chamado_registrar_acao(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    if request.method == "POST":
        from .forms import AcaoChamadoForm
        form = AcaoChamadoForm(request.POST, request.FILES)
        if form.is_valid():
            acao = form.save(commit=False)
            acao.chamado = chamado
            acao.autor = request.user
            acao.save()
            
            # Processar múltiplos anexos
            for arquivo in request.FILES.getlist('anexos'):
                from .models import AnexoAcao
                AnexoAcao.objects.create(
                    acao=acao,
                    arquivo=arquivo,
                    nome_original=arquivo.name
                )
            

            # Hook: registrar mudanca no servidor vinculado ao chamado
            if chamado.servidor:
                try:
                    from servidores.models import MudancaServidor
                    MudancaServidor.objects.create(
                        servidor=chamado.servidor,
                        titulo=f'Acao no chamado #{chamado.pk}: {chamado.titulo[:80]}',
                        tipo='outro',
                        descricao=acao.descricao,
                        origem='chamado',
                        chamado=chamado,
                        autor=request.user,
                    )
                except Exception:
                    pass
            return redirect("chamado_detalhe", pk=chamado.pk)
    
    return redirect("chamado_detalhe", pk=chamado.pk)


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_encerrar(request, pk):
    """
    Encerra o chamado via POST e redireciona para a lista de chamados.
    """
    chamado = get_object_or_404(Chamado, pk=pk)
    if not chamado.tem_acoes():
        messages.warning(request, "Registre ao menos uma ação antes de encerrar o chamado.")
        return redirect("chamado_detalhe", pk=chamado.pk)
    
    if request.method != "POST":
        return redirect("chamado_detalhe", pk=chamado.pk)
    
    chamado.status = Chamado.STATUS_ENCERRADO
    chamado.encerrado_por = request.user
    chamado.encerrado_em = timezone.now()
    chamado.save()
    
    registrar_auditoria(request, RegistroAuditoria.ACAO_ENCERRAMENTO, "Chamado", str(chamado.pk),
        f"Chamado #{chamado.pk} encerrado por {request.user.nome_completo}")
    
    messages.success(request, f"Chamado #{chamado.pk} encerrado com sucesso.")
    return redirect("chamado_lista")


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
        
        registrar_auditoria(request, RegistroAuditoria.ACAO_REABERTURA, "Chamado", str(chamado.pk),
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
        registrar_auditoria(request, RegistroAuditoria.ACAO_EXCLUSAO, "Chamado", str(chamado.pk), descricao)
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
                registrar_auditoria(request, RegistroAuditoria.ACAO_EXCLUSAO, "Chamado", str(chamado.pk), descricao)
            chamados.delete()
    
    return redirect("chamado_lista")


@login_required
def chamado_check_novos(request):
    ultimo_pk = int(request.GET.get("ultimo_pk", 0))
    novos = Chamado.objects.filter(pk__gt=ultimo_pk).order_by("-pk")
    total = novos.count()
    novo_pk = novos.first().pk if novos.exists() else ultimo_pk
    
    return JsonResponse({
        "novo_chamado": total > 0,
        "total_novos": total,
        "novo_pk": novo_pk,
    })


@login_required
def chamado_pdf_lista(request):
    """Gera PDF paisagem com filtros ativos lidos da sessão."""
    from django.http import QueryDict

    filtros_salvos = request.session.get("chamado_filtros", {})
    qd = QueryDict(mutable=True).copy()
    for k, v in filtros_salvos.items():
        if isinstance(v, list):
            for item in v:
                qd.appendlist(k, item)
        else:
            qd[k] = v

    form_filtro = ChamadoFiltroForm(qd or None)
    chamados = Chamado.objects.select_related(
        'solicitante', 'tecnico', 'categoria'
    ).order_by('-criado_em')

    if form_filtro.is_valid():
        status_selecionados = form_filtro.cleaned_data.get('status')
        if status_selecionados:
            chamados = chamados.filter(status__in=status_selecionados)
        categorias_selecionadas = form_filtro.cleaned_data.get('categoria')
        if categorias_selecionadas:
            chamados = chamados.filter(categoria__in=categorias_selecionadas)
        prioridades_selecionadas = form_filtro.cleaned_data.get('prioridade')
        if prioridades_selecionadas:
            chamados = chamados.filter(prioridade__in=prioridades_selecionadas)
        if form_filtro.cleaned_data.get('data_inicio'):
            chamados = chamados.filter(
                criado_em__date__gte=form_filtro.cleaned_data['data_inicio']
            )
        if form_filtro.cleaned_data.get('data_fim'):
            chamados = chamados.filter(
                criado_em__date__lte=form_filtro.cleaned_data['data_fim']
            )
        solicitante_nome = form_filtro.cleaned_data.get('solicitante_nome', '').strip()
        if solicitante_nome:
            chamados = chamados.filter(
                solicitante__nome_completo__icontains=solicitante_nome
            )

    html_string = render_to_string(
        'chamados/chamado_pdf_lista.html',
        {'chamados': chamados, 'usuario': request.user},
        request=request,
    )
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="chamados.pdf"'
    return response


@login_required
def chamado_pdf_detalhe(request, pk):
    """Gera PDF retrato com dados completos e histórico do chamado."""
    chamado = get_object_or_404(Chamado, pk=pk)
    anexos  = chamado.anexos.all()
    acoes   = AcaoChamado.objects.filter(chamado=chamado).order_by("criado_em")
    html_string = render_to_string(
        'chamados/chamado_pdf_detalhe.html',
        {'chamado': chamado, 'anexos': anexos,
         'acoes': acoes, 'usuario': request.user},
        request=request,
    )
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    nome = f'chamado_{chamado.pk}.pdf'
    response['Content-Disposition'] = f'inline; filename="{nome}"'
    return response


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_editar_titulo(request, pk):
    """Permite alterar o título de um chamado não encerrado."""
    chamado = get_object_or_404(Chamado, pk=pk)
    if chamado.status == Chamado.STATUS_ENCERRADO:
        messages.error(request, "Não é possível alterar o título de um chamado encerrado.")
        return redirect("chamado_detalhe", pk=chamado.pk)
    titulo_anterior = chamado.titulo
    form = ChamadoEditarTituloForm(request.POST or None, instance=chamado)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar_auditoria(
            request,
            RegistroAuditoria.ACAO_EDICAO,
            "Chamado",
            str(chamado.pk),
            f"Título alterado de '{titulo_anterior}' para '{chamado.titulo}'",
        )
        messages.success(request, "Título do chamado atualizado com sucesso.")
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_editar_titulo.html", {
        "chamado": chamado,
        "form": form,
    })


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def chamado_transferir(request, pk):
    """Transfere o chamado para outro técnico."""
    chamado = get_object_or_404(Chamado, pk=pk)
    if chamado.status not in [Chamado.STATUS_EM_ATENDIMENTO, Chamado.STATUS_AGUARDANDO, Chamado.STATUS_ABERTO]:
        messages.error(request, "Não é possível transferir um chamado encerrado.")
        return redirect("chamado_detalhe", pk=chamado.pk)
    tecnico_anterior = chamado.tecnico
    form = ChamadoTransferirForm(
        request.POST or None,
        tecnico_atual=chamado.tecnico,
    )
    if request.method == "POST" and form.is_valid():
        novo_tecnico = form.cleaned_data["novo_tecnico"]
        motivo = form.cleaned_data.get("motivo", "").strip()
        chamado.tecnico = novo_tecnico
        if chamado.status == Chamado.STATUS_ABERTO:
            chamado.status = Chamado.STATUS_EM_ATENDIMENTO
        chamado.save()
        desc = (
            f"Chamado transferido de "
            f"'{tecnico_anterior.nome_completo if tecnico_anterior else 'Nenhum'}' "
            f"para '{novo_tecnico.nome_completo}'"
        )
        if motivo:
            desc += f" — Motivo: {motivo}"
        registrar_auditoria(
            request,
            RegistroAuditoria.ACAO_EDICAO,
            "Chamado",
            str(chamado.pk),
            desc,
        )
        messages.success(
            request,
            f"Chamado transferido para {novo_tecnico.nome_completo} com sucesso.",
        )
        return redirect("chamado_detalhe", pk=chamado.pk)
    return render(request, "chamados/chamado_transferir.html", {
        "chamado": chamado,
        "form": form,
        "tecnico_anterior": tecnico_anterior,
    })


# ------------------------------------------------------------------ Calendario Operacional

@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def calendario_operacional(request):
    from .models import ConfiguracaoExpediente, FeriadoDiaAtipico
    expedientes = ConfiguracaoExpediente.objects.all()
    feriados = FeriadoDiaAtipico.objects.all()
    return render(request, "chamados/calendario_operacional.html", {
        "expedientes": expedientes,
        "feriados": feriados,
    })


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def calendario_feriado_novo(request):
    from .forms import FeriadoDiaAtipicoForm
    if request.method == "POST":
        form = FeriadoDiaAtipicoForm(request.POST)
        if form.is_valid():
            from chamados.sla_utils import capturar_vencimentos_atuais
            vencimentos_antes = capturar_vencimentos_atuais()
            feriado = form.save(commit=False)
            feriado.criado_por = request.user
            feriado.save()
            registrar_auditoria(request, "Cadastro", str(feriado.pk),
                                f"Feriado cadastrado: {feriado.descricao} em {feriado.data:%d/%m/%Y}")
            # Recalcular SLAs impactados
            from chamados.sla_utils import recalcular_slas_impactados
            total = recalcular_slas_impactados(feriado.data, "Cadastro de feriado: " + feriado.descricao, request.user, vencimentos_antes)
            if total > 0:
                messages.info(request, f"{total} chamado(s) tiveram o SLA recalculado.")
            messages.success(request, f"Feriado \"{feriado.descricao}\" cadastrado com sucesso.")
            return redirect("calendario_operacional")
    else:
        form = FeriadoDiaAtipicoForm()
    return render(request, "chamados/calendario_feriado_form.html", {"form": form})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def calendario_feriado_editar(request, pk):
    from .models import FeriadoDiaAtipico
    from .forms import FeriadoDiaAtipicoForm
    feriado = get_object_or_404(FeriadoDiaAtipico, pk=pk)
    if request.method == "POST":
        form = FeriadoDiaAtipicoForm(request.POST, instance=feriado)
        if form.is_valid():
            from chamados.sla_utils import capturar_vencimentos_atuais
            vencimentos_antes = capturar_vencimentos_atuais()
            form.save()
            registrar_auditoria(request, "Alteracao", str(feriado.pk),
                                f"Feriado alterado: {feriado.descricao} em {feriado.data:%d/%m/%Y}")
            # Recalcular SLAs impactados
            from chamados.sla_utils import recalcular_slas_impactados
            total = recalcular_slas_impactados(feriado.data, "Alteracao de feriado: " + feriado.descricao, request.user, vencimentos_antes)
            if total > 0:
                messages.info(request, f"{total} chamado(s) tiveram o SLA recalculado.")
            messages.success(request, f"Feriado \"{feriado.descricao}\" atualizado com sucesso.")
            return redirect("calendario_operacional")
    else:
        form = FeriadoDiaAtipicoForm(instance=feriado)
    return render(request, "chamados/calendario_feriado_form.html", {"form": form})


@login_required
@permission_required("chamados.can_manage_chamados", raise_exception=True)
def calendario_feriado_excluir(request, pk):
    from .models import FeriadoDiaAtipico
    if request.method == "POST":
        feriado = get_object_or_404(FeriadoDiaAtipico, pk=pk)
        descricao = feriado.descricao
        data_str = f"{feriado.data:%d/%m/%Y}"
        from chamados.sla_utils import capturar_vencimentos_atuais
        vencimentos_antes = capturar_vencimentos_atuais()
        data_feriado = feriado.data
        feriado.delete()
        registrar_auditoria(request, "Exclusao", str(pk),
                            f"Feriado excluido: {descricao} em {data_str}")
        # Recalcular SLAs impactados
        from chamados.sla_utils import recalcular_slas_impactados
        total = recalcular_slas_impactados(data_feriado, "Exclusao de feriado: " + descricao, request.user, vencimentos_antes)
        if total > 0:
            messages.info(request, f"{total} chamado(s) tiveram o SLA recalculado.")
        messages.success(request, f"Feriado \"{descricao}\" excluido com sucesso.")
    return redirect("calendario_operacional")
