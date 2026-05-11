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
    chamados = servidor.chamados.order_by('-criado_em')
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
