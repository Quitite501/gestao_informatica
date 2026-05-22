from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from patrimonio.models import ComputadorEspecificacao, Patrimonio, TipoEquipamento
from usuarios.models import Setor


@receiver(pre_save, sender=ComputadorEspecificacao)
def auto_criar_patrimonio_se_nao_existir(sender, instance, **kwargs):
    """Auto-cria Patrimonio se patrimonio_id nao existir"""
    
    if not instance.patrimonio_id:
        return
    
    try:
        patrimonio = Patrimonio.objects.get(pk=instance.patrimonio_id)
        instance.patrimonio = patrimonio
        return
    except Patrimonio.DoesNotExist:
        pass
    except (ValueError, TypeError):
        raise ValidationError("Patrimonio ID deve ser um número inteiro válido")
    
    # AUTO-CRIAR PATRIMONIO
    hostname = instance.hostname or f"PC-{instance.patrimonio_id}"
    
    tipo_pc, _ = TipoEquipamento.objects.get_or_create(
        nome="Desktop",
        defaults={"descricao": "Computador Desktop/Workstation"}
    )
    
    setor = Setor.objects.filter(ativo=True).first()
    etiqueta = limpar_etiqueta(hostname, instance.patrimonio_id)
    
    patrimonio = Patrimonio.objects.create(
        id=instance.patrimonio_id,
        etiqueta=etiqueta,
        hostname=hostname,
        tipo=tipo_pc,
        marca="Auto-gerado",
        modelo="Coleta Automática",
        descricao=(
            f"Patrimônio criado automaticamente pelo Coletor.\n"
            f"Hostname: {hostname}\nMAC: {instance.endereco_mac}\n"
            f"IP: {instance.endereco_ip}\nS.O.: {instance.sistema_operacional}"
        ),
        status="em_uso",
        setor=setor,
    )
    
    instance.patrimonio = patrimonio


def limpar_etiqueta(hostname, patrimonio_id):
    import re
    etiqueta = str(hostname or f"AUTO-{patrimonio_id}").upper()
    etiqueta = re.sub(r"[^A-Z0-9_-]", "-", etiqueta)
    etiqueta = re.sub(r"-+", "-", etiqueta).strip("-")
    return (etiqueta or f"AUTO-{patrimonio_id}")[:40]
