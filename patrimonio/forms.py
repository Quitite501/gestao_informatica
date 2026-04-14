from django import forms
from .models import Patrimonio, TipoEquipamento


class PatrimonioForm(forms.ModelForm):
    class Meta:
        model = Patrimonio
        fields = [
            "etiqueta",
            "numero_serie",
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
