from django.shortcuts import redirect
from django.urls import reverse

URLS_LIVRES = [
    '/trocar-senha/',
    '/logout/',
    '/login/',
    '/static/',
    '/media/',
]

class ForcarTrocaSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            livre = any(path.startswith(u) for u in URLS_LIVRES)
            if not livre and getattr(request.user, 'force_password_change', False):
                return redirect(reverse('usuario_trocar_senha'))
        return self.get_response(request)
