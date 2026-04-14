from django import forms
from .models import NotaFiscal


class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            "numero",
            "fornecedor",
            "data_emissao",
            "valor_total",
            "arquivo_pdf",
            "arquivo_xml",
            "observacoes",
        ]
        widgets = {
            "data_emissao": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_emissao"].input_formats = ["%Y-%m-%d"]


class NotaFiscalFiltroForm(forms.Form):
    numero = forms.CharField(required=False, label="Número")
    fornecedor = forms.CharField(required=False)
    data_de = forms.DateField(
        required=False,
        label="Data de emissão (de)",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    data_ate = forms.DateField(
        required=False,
        label="Data de emissão (até)",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
