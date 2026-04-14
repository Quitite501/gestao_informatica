from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import RegistroAuditoria

Usuario = get_user_model()


@login_required
@permission_required("auditoria.view_registroauditoria", raise_exception=True)
def auditoria_lista(request):
    registros = RegistroAuditoria.objects.select_related("usuario").all()

    modelo = request.GET.get("modelo", "")
    acao = request.GET.get("acao", "")
    usuario_id = request.GET.get("usuario", "")

    if modelo:
        registros = registros.filter(modelo_afetado__icontains=modelo)
    if acao:
        registros = registros.filter(acao=acao)
    if usuario_id:
        registros = registros.filter(usuario__id=usuario_id)

    usuarios = Usuario.objects.filter(ativo=True).order_by("nome_completo")
    acoes = RegistroAuditoria.ACAO_CHOICES

    return render(request, "auditoria/auditoria_lista.html", {
        "registros": registros[:200],
        "usuarios": usuarios,
        "acoes": acoes,
        "filtro_modelo": modelo,
        "filtro_acao": acao,
        "filtro_usuario": usuario_id,
    })
