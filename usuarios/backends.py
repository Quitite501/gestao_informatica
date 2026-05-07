import unicodedata
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

def normalizar(texto):
    if not texto:
        return ''
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('ascii')
    return texto.lower().strip()

class BackendSemAcento(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        Usuario = get_user_model()
        entrada = normalizar(username or '')
        for u in Usuario.objects.filter(is_active=True):
            if normalizar(u.username) == entrada:
                if u.check_password(password):
                    return u
        return None
