from django import forms

from .models import Usuario


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'nome_completo',
            'login_rede',
            'ramal',
            'cargo',
            'setor',
            'ativo',
            'is_staff',
            'groups',
            'password',
            'foto',
        ]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            usuario.set_password(password)

        if commit:
            usuario.save()
            self.save_m2m()

        return usuario


class CredencialExternaForm(forms.ModelForm):
    class Meta:
        from .models import CredencialExterna
        model = CredencialExterna
        fields = ['plataforma', 'login', 'observacao', 'ativo']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }
