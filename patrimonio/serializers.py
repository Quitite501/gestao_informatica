from rest_framework import serializers
from patrimonio.models import ComputadorEspecificacao, Patrimonio


class PatrimonioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrimonio
        fields = ['id', 'etiqueta', 'hostname', 'tipo', 'marca', 'modelo', 'status']


class ComputadorEspecificacaoSerializer(serializers.ModelSerializer):
    patrimonio = PatrimonioSerializer(read_only=True)
    patrimonio_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = ComputadorEspecificacao
        fields = [
            'id',
            'patrimonio',
            'patrimonio_id',
            'hostname',
            'ram_gb',
            'sistema_operacional',
            'endereco_ip',
            'endereco_mac',
            'processador',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def create(self, validated_data):
        """
        Criar ComputadorEspecificacao.
        O signal auto_criar_patrimonio_se_nao_existir cuidara de vincular o patrimonio.
        """
        return ComputadorEspecificacao.objects.create(**validated_data)
