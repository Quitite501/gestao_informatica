from rest_framework import serializers
from .models import ComputadorEspecificacao, Patrimonio


class PatrimonioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrimonio
        fields = ['id', 'etiqueta', 'hostname', 'tipo', 'marca', 'modelo', 'status']


class ComputadorEspecificacaoSerializer(serializers.ModelSerializer):
    patrimonio = PatrimonioSerializer(read_only=True)
    patrimonio_id = serializers.PrimaryKeyRelatedField(
        queryset=Patrimonio.objects.all(),
        write_only=True,
        source='patrimonio'
    )

    class Meta:
        model = ComputadorEspecificacao
        fields = [
            'id',
            'patrimonio',
            'patrimonio_id',
            'ram_gb',
            'sistema_operacional',
            'endereco_ip',
            'endereco_mac',
            'processador',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
