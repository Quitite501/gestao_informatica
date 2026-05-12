from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Servidor, MudancaServidor
from .forms import ServidorForm, MudancaServidorForm


@login_required
def servidor_lista(request):
    servidores = Servidor.objects.all()
    return render(request, 'servidores/servidor_lista.html', {
        'servidores': servidores,
        'total_ativos': servidores.filter(status='ativo').count(),
        'total_manutencao': servidores.filter(status='manutencao').count(),
        'total_inativos': servidores.filter(status='inativo').count(),
    })


@login_required
def servidor_detalhe(request, pk):
    servidor = get_object_or_404(Servidor, pk=pk)
    mudancas = servidor.mudancas.all()
    try:
        chamados = servidor.chamados.order_by('-criado_em')
    except Exception:
        chamados = []
    form_mudanca = MudancaServidorForm()
    return render(request, 'servidores/servidor_detalhe.html', {
        'servidor': servidor,
        'mudancas': mudancas,
        'chamados': chamados,
        'form_mudanca': form_mudanca,
    })


@login_required
def servidor_novo(request):
    if request.method == 'POST':
        form = ServidorForm(request.POST)
        if form.is_valid():
            servidor = form.save()
            messages.success(request, f'Servidor {servidor.nome} cadastrado com sucesso.')
            return redirect('servidor_detalhe', pk=servidor.pk)
    else:
        form = ServidorForm()
    return render(request, 'servidores/servidor_form.html', {
        'form': form,
        'titulo': 'Novo servidor',
    })


@login_required
def servidor_editar(request, pk):
    servidor = get_object_or_404(Servidor, pk=pk)
    if request.method == 'POST':
        form = ServidorForm(request.POST, instance=servidor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servidor atualizado com sucesso.')
            return redirect('servidor_detalhe', pk=servidor.pk)
    else:
        form = ServidorForm(instance=servidor)
    return render(request, 'servidores/servidor_form.html', {
        'form': form,
        'titulo': f'Editar — {servidor.nome}',
        'servidor': servidor,
    })


@login_required
def mudanca_registrar(request, pk):
    servidor = get_object_or_404(Servidor, pk=pk)
    if request.method == 'POST':
        form = MudancaServidorForm(request.POST)
        if form.is_valid():
            mudanca = form.save(commit=False)
            mudanca.servidor = servidor
            mudanca.autor = request.user
            mudanca.origem = 'manual'
            mudanca.save()
            messages.success(request, 'Mudança registrada com sucesso.')
            return redirect('servidor_detalhe', pk=servidor.pk)
    return redirect('servidor_detalhe', pk=servidor.pk)


@login_required
def servidor_relatorio(request):
    from chamados.models import Chamado
    servidores = Servidor.objects.all()
    servidor_id = request.GET.get('servidor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')

    mudancas = MudancaServidor.objects.select_related('servidor', 'autor', 'chamado').all()

    if servidor_id:
        mudancas = mudancas.filter(servidor_id=servidor_id)
    if data_inicio:
        mudancas = mudancas.filter(criado_em__date__gte=data_inicio)
    if data_fim:
        mudancas = mudancas.filter(criado_em__date__lte=data_fim)
    if tipo:
        mudancas = mudancas.filter(tipo=tipo)

    return render(request, 'servidores/servidor_relatorio.html', {
        'mudancas': mudancas,
        'servidores': servidores,
        'tipos': MudancaServidor.TIPO_CHOICES,
        'filtros': {
            'servidor_id': servidor_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'tipo': tipo,
        },
        'servidor_selecionado': Servidor.objects.filter(pk=servidor_id).first() if servidor_id else None,
    })


@login_required
def servidor_relatorio_csv(request):
    import csv
    from django.http import HttpResponse

    servidor_id = request.GET.get('servidor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')

    mudancas = MudancaServidor.objects.select_related('servidor', 'autor', 'chamado').all()
    if servidor_id:
        mudancas = mudancas.filter(servidor_id=servidor_id)
    if data_inicio:
        mudancas = mudancas.filter(criado_em__date__gte=data_inicio)
    if data_fim:
        mudancas = mudancas.filter(criado_em__date__lte=data_fim)
    if tipo:
        mudancas = mudancas.filter(tipo=tipo)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="auditoria_servidores.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Data', 'Servidor', 'Tipo', 'Título', 'Descrição', 'Origem', 'Chamado', 'Autor'])
    for m in mudancas:
        writer.writerow([
            m.criado_em.strftime('%d/%m/%Y %H:%M'),
            m.servidor.nome,
            m.get_tipo_display(),
            m.titulo,
            m.descricao,
            m.get_origem_display(),
            f'#{m.chamado.pk}' if m.chamado else '',
            m.autor.nome_completo if m.autor else '',
        ])
    return response


@login_required
def servidor_relatorio_pdf(request):
    from weasyprint import HTML

    servidor_id = request.GET.get('servidor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')

    mudancas = MudancaServidor.objects.select_related('servidor', 'autor', 'chamado').all()
    if servidor_id:
        mudancas = mudancas.filter(servidor_id=servidor_id)
    if data_inicio:
        mudancas = mudancas.filter(criado_em__date__gte=data_inicio)
    if data_fim:
        mudancas = mudancas.filter(criado_em__date__lte=data_fim)
    if tipo:
        mudancas = mudancas.filter(tipo=tipo)

    servidor_obj = Servidor.objects.filter(pk=servidor_id).first() if servidor_id else None
    # Coletar chamados vinculados com dados completos
    chamados_ids = mudancas.exclude(chamado=None).values_list('chamado_id', flat=True).distinct()
    from chamados.models import Chamado, AcaoChamado, AnexoChamado
    chamados_detalhes = []
    for cid in chamados_ids:
        try:
            c = Chamado.objects.select_related('solicitante','tecnico','categoria','encerrado_por').get(pk=cid)
            acoes = AcaoChamado.objects.filter(chamado=c).order_by('criado_em')
            anexos = AnexoChamado.objects.filter(chamado=c)
            chamados_detalhes.append({'chamado': c, 'acoes': acoes, 'anexos': anexos})
        except Exception:
            pass

    from django.utils import timezone
    html_string = render(request, 'servidores/servidor_relatorio_pdf.html', {
        'mudancas': mudancas,
        'servidor': servidor_obj,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'now': timezone.localtime().strftime('%d/%m/%Y %H:%M'),
        'chamados_detalhes': chamados_detalhes,
    }).content.decode('utf-8')

    from django.http import HttpResponse
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    nome = f'auditoria_servidores.pdf'
    response['Content-Disposition'] = f'inline; filename="{nome}"'
    return response
