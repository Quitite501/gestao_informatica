from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .api import ComputadorEspecificacaoViewSet

router = SimpleRouter()
router.register(r'computadores', ComputadorEspecificacaoViewSet, basename='computador-api')

urlpatterns = [
    path('api/', include(router.urls)),
]
