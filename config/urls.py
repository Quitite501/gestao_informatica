from django.contrib import admin
from core.views import pagina_403
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
    path("", include("patrimonio.urls")),
    path("", include("chamados.urls")),
    path("", include("auditoria.urls")),
    path("", include("core.urls")),
    path("", include("notas_fiscais.urls")),
    path("", include("licencas.urls")),
    path("", include("servidores.urls")),
]

handler403 = pagina_403

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
