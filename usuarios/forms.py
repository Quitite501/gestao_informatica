from django import forms

from .models import Usuario


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=False
    )
    perm_abrir_chamados = forms.BooleanField(required=False, label='Pode abrir chamados')
    perm_tecnico = forms.BooleanField(required=False, label='Técnico')
    perm_gerenciar_usuarios = forms.BooleanField(required=False, label='Pode gerenciar usuários')
    perm_parametrizacao = forms.BooleanField(required=False, label='Pode acessar parametrização')

    PERMS_ABRIR_CHAMADOS = ['add_chamado', 'view_chamado', 'add_anexochamado']
    PERMS_TECNICO = ['can_manage_chamados', 'can_manage_patrimonio', 'view_patrimonio',
                     'view_notafiscal', 'view_software', 'view_registroauditoria',
                     'view_instalacaosoftware', 'view_licencacontrato']
    PERMS_GERENCIAR_USUARIOS = ['add_usuario', 'change_usuario', 'view_usuario',
                                 'add_setor', 'change_setor', 'view_setor']
    PERMS_PARAMETRIZACAO = ['add_categoriachamado', 'change_categoriachamado',
                             'add_configuracaosla', 'change_configuracaosla',
                             'add_tipoequipamento', 'change_tipoequipamento',
                             'add_feriadodiaatipico', 'change_feriadodiaatipico']

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'nome_completo', 'login_rede',
            'ramal', 'cargo', 'setor', 'ativo', 'is_staff', 'password', 'foto',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            user_perms = set(self.instance.user_permissions.values_list('codename', flat=True))
            self.fields['perm_abrir_chamados'].initial = bool(user_perms & set(self.PERMS_ABRIR_CHAMADOS))
            self.fields['perm_tecnico'].initial = bool(user_perms & set(self.PERMS_TECNICO))
            self.fields['perm_gerenciar_usuarios'].initial = bool(user_perms & set(self.PERMS_GERENCIAR_USUARIOS))
            self.fields['perm_parametrizacao'].initial = bool(user_perms & set(self.PERMS_PARAMETRIZACAO))

    def _sync_perms(self, usuario, codenames, grant):
        from django.contrib.auth.models import Permission
        perms = Permission.objects.filter(codename__in=codenames)
        if grant:
            usuario.user_permissions.add(*perms)
        else:
            usuario.user_permissions.remove(*perms)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            usuario.set_password(password)
        if commit:
            usuario.save()
            self._sync_perms(usuario, self.PERMS_ABRIR_CHAMADOS, self.cleaned_data.get('perm_abrir_chamados'))
            self._sync_perms(usuario, self.PERMS_TECNICO, self.cleaned_data.get('perm_tecnico'))
            if self.cleaned_data.get('is_staff'):
                self._sync_perms(usuario, self.PERMS_GERENCIAR_USUARIOS, self.cleaned_data.get('perm_gerenciar_usuarios'))
                self._sync_perms(usuario, self.PERMS_PARAMETRIZACAO, self.cleaned_data.get('perm_parametrizacao'))
            else:
                self._sync_perms(usuario, self.PERMS_GERENCIAR_USUARIOS, False)
                self._sync_perms(usuario, self.PERMS_PARAMETRIZACAO, False)
        return usuario


class CredencialExternaForm(forms.ModelForm):
    class Meta:
        from .models import CredencialExterna
        model = CredencialExterna
        fields = ['plataforma', 'login', 'observacao', 'ativo']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }
