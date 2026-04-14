from .models import RegistroAuditoria


def registrar_auditoria(request, acao, modelo_afetado, objeto_id="", descricao=""):
    ip = request.META.get("REMOTE_ADDR")
    usuario = request.user if request.user.is_authenticated else None
    RegistroAuditoria.objects.create(
        usuario=usuario,
        acao=acao,
        modelo_afetado=modelo_afetado,
        objeto_id=str(objeto_id),
        descricao=descricao,
        ip=ip,
    )
