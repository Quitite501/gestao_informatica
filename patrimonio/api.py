from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ComputadorEspecificacao
from .serializers import ComputadorEspecificacaoSerializer
from auditoria.utils import registrar_auditoria
from auditoria.models import RegistroAuditoria


class ComputadorEspecificacaoViewSet(viewsets.ModelViewSet):
    """
    API REST para ComputadorEspecificacao
    
    Endpoints:
    - GET    /api/computadores/               (listar)
    - POST   /api/computadores/               (criar)
    - GET    /api/computadores/{id}/          (detalhe)
    - PUT    /api/computadores/{id}/          (atualizar completo)
    - PATCH  /api/computadores/{id}/          (atualizar parcial)
    - DELETE /api/computadores/{id}/          (deletar)
    """
    queryset = ComputadorEspecificacao.objects.select_related(
        'patrimonio', 'patrimonio__tipo', 'patrimonio__setor'
    ).order_by('patrimonio__etiqueta')
    serializer_class = ComputadorEspecificacaoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['sistema_operacional', 'endereco_ip', 'endereco_mac']
    search_fields = ['patrimonio__etiqueta', 'endereco_mac', 'endereco_ip']
    ordering_fields = ['criado_em', 'patrimonio__etiqueta']

    def perform_create(self, serializer):
        """Registrar criação na auditoria."""
        computador = serializer.save()
        registrar_auditoria(
            self.request,
            RegistroAuditoria.ACAO_CRIACAO,
            "ComputadorEspecificacao",
            computador.pk,
            f"Computador {computador.patrimonio.etiqueta} criado via API"
        )

    def perform_update(self, serializer):
        """Registrar atualização na auditoria."""
        computador = serializer.save()
        registrar_auditoria(
            self.request,
            RegistroAuditoria.ACAO_EDICAO,
            "ComputadorEspecificacao",
            computador.pk,
            f"Computador {computador.patrimonio.etiqueta} atualizado via API"
        )

    def perform_destroy(self, instance):
        """Registrar exclusão na auditoria."""
        etiqueta = instance.patrimonio.etiqueta
        registrar_auditoria(
            self.request,
            RegistroAuditoria.ACAO_EXCLUSAO,
            "ComputadorEspecificacao",
            instance.pk,
            f"Computador {etiqueta} deletado via API"
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def por_sistema_operacional(self, request):
        """Filtrar computadores por S.O.
        
        Uso: GET /api/computadores/por_sistema_operacional/?so=Windows
        """
        so = request.query_params.get('so')
        if not so:
            return Response(
                {'erro': 'Parâmetro "so" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        computadores = self.queryset.filter(sistema_operacional__icontains=so)
        serializer = self.get_serializer(computadores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_ip(self, request):
        """Filtrar computadores por IP.
        
        Uso: GET /api/computadores/por_ip/?ip=192.168.1.100
        """
        ip = request.query_params.get('ip')
        if not ip:
            return Response(
                {'erro': 'Parâmetro "ip" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        computadores = self.queryset.filter(endereco_ip=ip)
        serializer = self.get_serializer(computadores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_mac(self, request):
        """Filtrar computadores por MAC.
        
        Uso: GET /api/computadores/por_mac/?mac=AA:BB:CC:DD:EE:FF
        """
        mac = request.query_params.get('mac')
        if not mac:
            return Response(
                {'erro': 'Parâmetro "mac" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        computadores = self.queryset.filter(endereco_mac__icontains=mac)
        serializer = self.get_serializer(computadores, many=True)
        return Response(serializer.data)
