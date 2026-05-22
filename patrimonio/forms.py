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
