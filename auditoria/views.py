from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import RegistroAuditoria

Usuario = get_user_model()


@login_required
@permission_required("auditoria.view_registroauditoria", raise_exception=True)
def auditoria_lista(request):
    from django.shortcuts import redirect

    # ── Limpar filtros ────────────────────────────────────────────────
    if "limpar" in request.GET:
        request.session.pop("auditoria_filtros", None)
        return redirect("auditoria_lista")

    # ── Salvar filtros na sessão e redirecionar para URL limpa ────────
    if request.GET:
        request.session["auditoria_filtros"] = {
            k: request.GET.getlist(k) for k in request.GET.keys()
        }
        return redirect("auditoria_lista")

    # ── Ler filtros da sessão ─────────────────────────────────────────
    filtros_salvos = request.session.get("auditoria_filtros", {})
    modelo     = filtros_salvos.get("modelo", [""])[0] if filtros_salvos.get("modelo") else ""
    acao       = filtros_salvos.get("acao", [""])[0] if filtros_salvos.get("acao") else ""
    usuario_id = filtros_salvos.get("usuario", [""])[0] if filtros_salvos.get("usuario") else ""

    registros = RegistroAuditoria.objects.select_related("usuario").all()

    if modelo:
        registros = registros.filter(modelo_afetado__icontains=modelo)
    if acao:
        registros = registros.filter(acao=acao)
    if usuario_id:
        registros = registros.filter(usuario__id=usuario_id)

    registros = registros.order_by("-criado_em")
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
