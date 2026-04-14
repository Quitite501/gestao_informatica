from django.contrib import admin
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
