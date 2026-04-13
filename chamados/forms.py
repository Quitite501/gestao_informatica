from django import forms
from .models import Chamado, CategoriaChamado


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solicitante", "titulo", "descricao", "categoria", "prioridade"]


class ChamadoFiltroForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "Todos")] + Chamado.STATUS_CHOICES,
        required=False,
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaChamado.objects.filter(ativo=True),
        required=False,
        empty_label="Todas",
    )
    prioridade = forms.ChoiceField(
        choices=[("", "Todas")] + Chamado.PRIORIDADE_CHOICES,
        required=False,
    )


class ChamadoEncerramentoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solucao_tecnica"]

    def clean_solucao_tecnica(self):
        solucao = self.cleaned_data.get("solucao_tecnica")
        if not solucao or not solucao.strip():
            raise forms.ValidationError("A solucao tecnica e obrigatoria para encerrar o chamado.")
        return solucao
