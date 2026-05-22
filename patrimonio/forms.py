from django import forms
from .models import Patrimonio, TipoEquipamento, ComputadorEspecificacao


class PatrimonioForm(forms.ModelForm):
    class Meta:
        model = Patrimonio
        fields = [
            "etiqueta",
            "numero_serie",
            "hostname",
            "tipo",
            "marca",
            "modelo",
            "descricao",
            "setor",
            "usuario_atual",
            "status",
            "observacoes",
            "nota_fiscal",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        usuario_atual = cleaned_data.get("usuario_atual")
        status = cleaned_data.get("status")

        if usuario_atual and status == Patrimonio.STATUS_DISPONIVEL:
            cleaned_data["status"] = Patrimonio.STATUS_EM_USO

        if not usuario_atual and status == Patrimonio.STATUS_EM_USO:
            cleaned_data["status"] = Patrimonio.STATUS_DISPONIVEL

        return cleaned_data


class PatrimonioFiltroForm(forms.Form):
    etiqueta = forms.CharField(required=False, label="Etiqueta")
    tipo = forms.ModelChoiceField(
        queryset=TipoEquipamento.objects.filter(ativo=True),
        required=False,
        label="Tipo",
        empty_label="Todos os tipos",
    )
    status = forms.ChoiceField(
        choices=[("", "Todos os status")] + Patrimonio.STATUS_CHOICES,
        required=False,
        label="Status",
    )


class ComputadorEspecificacaoForm(forms.ModelForm):
    class Meta:
        model = ComputadorEspecificacao
        fields = [
            "patrimonio",
            "hostname",
            "ram_gb",
            "sistema_operacional",
            "endereco_ip",
            "endereco_mac",
            "processador",
        ]
        widgets = {
            "patrimonio": forms.Select(attrs={"class": "form-control"}),
            "hostname": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: WORKSTATION-01"}),
            "ram_gb": forms.NumberInput(attrs={"class": "form-control"}),
            "sistema_operacional": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Windows 11 Pro"}),
            "endereco_ip": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 192.168.1.100"}),
            "endereco_mac": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: AA:BB:CC:DD:EE:FF"}),
            "processador": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Intel Core i7-12700K"}),
        }

    def clean_endereco_mac(self):
        mac = self.cleaned_data.get("endereco_mac", "").strip()
        if mac:
            # Validação simples de MAC
            if not all(c in "0123456789ABCDEFabcdef:-" for c in mac):
                raise forms.ValidationError("MAC inválido. Use formato: XX:XX:XX:XX:XX:XX")
        return mac


class ComputadorCompletoForm(forms.ModelForm):
    """Formulário combinado: ComputadorEspecificacao + campos do Patrimônio"""
    
    # Campos do Patrimônio
    patrimonio_setor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Setor",
        empty_label="— Sem setor —",
    )
    patrimonio_usuario = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Usuário Vinculado",
        empty_label="— Sem usuário —",
    )
    patrimonio_status = forms.ChoiceField(
        choices=Patrimonio.STATUS_CHOICES,
        required=False,
        label="Status do Patrimônio",
    )
    
    class Meta:
        model = ComputadorEspecificacao
        fields = [
            "hostname",
            "ram_gb",
            "sistema_operacional",
            "endereco_ip",
            "endereco_mac",
            "processador",
        ]
        widgets = {
            "hostname": forms.TextInput(attrs={"placeholder": "Ex: WORKSTATION-01"}),
            "ram_gb": forms.NumberInput(attrs={"min": 1, "max": 1024}),
            "sistema_operacional": forms.TextInput(attrs={"placeholder": "Ex: Windows 11 Pro"}),
            "endereco_ip": forms.TextInput(attrs={"placeholder": "Ex: 192.168.1.100"}),
            "endereco_mac": forms.TextInput(attrs={"placeholder": "Ex: AA:BB:CC:DD:EE:FF"}),
            "processador": forms.TextInput(attrs={"placeholder": "Ex: Intel Core i7-12700K"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        from usuarios.models import Setor, Usuario
        self.fields['patrimonio_setor'].queryset = Setor.objects.filter(ativo=True).order_by("nome")
        self.fields['patrimonio_usuario'].queryset = Usuario.objects.filter(ativo=True).order_by("nome_completo")
        self.fields['patrimonio_usuario'].label_from_instance = lambda u: f"{u.nome_completo} ({u.username})"
        
        # Preencher com dados do patrimônio se existir
        if self.instance and self.instance.pk and hasattr(self.instance, 'patrimonio'):
            p = self.instance.patrimonio
            self.fields['patrimonio_setor'].initial = p.setor
            self.fields['patrimonio_usuario'].initial = p.usuario_atual
            self.fields['patrimonio_status'].initial = p.status
    
    def clean_endereco_mac(self):
        mac = self.cleaned_data.get("endereco_mac", "").strip()
        if mac and not all(c in "0123456789ABCDEFabcdef:-" for c in mac):
            raise forms.ValidationError("MAC inválido. Use formato: XX:XX:XX:XX:XX:XX")
        return mac
    
    def salvar_patrimonio(self, computador):
        """Salva os campos do Patrimônio após salvar o computador"""
        p = computador.patrimonio
        p.setor = self.cleaned_data.get('patrimonio_setor')
        p.usuario_atual = self.cleaned_data.get('patrimonio_usuario')
        status = self.cleaned_data.get('patrimonio_status')
        if status:
            p.status = status
        # Sincronizar hostname
        if computador.hostname:
            p.hostname = computador.hostname
        p.save()
