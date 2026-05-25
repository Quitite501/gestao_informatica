from django import forms
from .models import Software, LicencaContrato, InstalacaoSoftware
from patrimonio.models import Patrimonio, TipoEquipamento


class SoftwareForm(forms.ModelForm):
    class Meta:
        model = Software
        fields = [
            "nome",
            "fabricante",
            "versao",
            "tipo_licenca",
            "controlado",
            "ativo",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Ex: Microsoft Office 365",
            }),
            "fabricante": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Ex: Microsoft",
            }),
            "versao": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Ex: 2025, 22H2, 16.0",
            }),
            "tipo_licenca": forms.Select(attrs={
                "class": "form-input",
            }),
        }


class SoftwareFiltroForm(forms.Form):
    nome = forms.CharField(required=False)
    fabricante = forms.CharField(required=False)
    controlado = forms.ChoiceField(
        required=False,
        choices=[("", "Todos"), ("true", "Controlados"), ("false", "Não controlados")],
    )


class LicencaContratoForm(forms.ModelForm):
    class Meta:
        model = LicencaContrato
        fields = [
            "software",
            "nota_fiscal",
            "quantidade_adquirida",
            "chave_licenca",
            "data_aquisicao",
            "data_vencimento",
            "observacoes",
        ]
        widgets = {
            "data_aquisicao": forms.DateInput(attrs={"type": "date"}),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}),
        }


class InstalacaoSoftwareForm(forms.ModelForm):
    class Meta:
        model = InstalacaoSoftware
        fields = [
            "software",
            "patrimonio",
            "data_instalacao",
            "observacoes",
            "ativo",
        ]
        widgets = {
            "data_instalacao": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipos_aceitos = TipoEquipamento.objects.filter(aceita_software=True)
        self.fields["patrimonio"].queryset = Patrimonio.objects.filter(
            tipo__in=tipos_aceitos
        ).select_related("tipo", "usuario_atual").order_by("etiqueta")
        self.fields["software"].queryset = Software.objects.filter(
            ativo=True
        ).order_by("nome")
