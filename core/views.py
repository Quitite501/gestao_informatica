from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum
from django.contrib.auth import get_user_model
from chamados.models import Chamado
from patrimonio.models import Patrimonio
from notas_fiscais.models import NotaFiscal

Usuario = get_user_model()


@login_required
def relatorio_chamados(request):
    por_status = Chamado.objects.values("status").annotate(total=Count("id")).order_by("status")
    por_prioridade = Chamado.objects.values("prioridade").annotate(total=Count("id")).order_by("prioridade")
    chamados = Chamado.objects.select_related("solicitante", "tecnico", "categoria").all()
    return render(request, "relatorios/relatorio_chamados.html", {
        "por_status": por_status,
        "por_prioridade": por_prioridade,
        "chamados": chamados,
    })


@login_required
def relatorio_patrimonio(request):
    por_status = Patrimonio.objects.values("status").annotate(total=Count("id")).order_by("status")
    por_setor = Patrimonio.objects.values("setor__nome").annotate(total=Count("id")).order_by("setor__nome")
    patrimonios = Patrimonio.objects.select_related("tipo", "setor", "usuario_atual").all()
    return render(request, "relatorios/relatorio_patrimonio.html", {
        "por_status": por_status,
        "por_setor": por_setor,
        "patrimonios": patrimonios,
    })


@login_required
def relatorio_usuarios(request):
    ativos = Usuario.objects.filter(ativo=True).order_by("nome_completo")
    inativos = Usuario.objects.filter(ativo=False).order_by("nome_completo")
    return render(request, "relatorios/relatorio_usuarios.html", {
        "ativos": ativos,
        "inativos": inativos,
    })


@login_required
def relatorio_notas_fiscais(request):
    notas = NotaFiscal.objects.all().order_by("-data_emissao")
    valor_total = notas.aggregate(total=Sum("valor_total"))["total"] or 0
    return render(request, "relatorios/relatorio_notas_fiscais.html", {
        "notas": notas,
        "valor_total": valor_total,
    })


# ── Handler de erro 403 ──────────────────────────────────────────────────────
def pagina_403(request, exception=None):
    """
    View customizada para o erro 403 (Acesso Negado).
    Exibe informações do módulo acessado para facilitar a identificação
    pelo administrador do sistema.
    """
    return render(request, '403.html', status=403)
