from django import forms
from .models import Chamado, CategoriaChamado, AcaoChamado


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solicitante", "titulo", "descricao", "categoria", "prioridade"]
        widgets = {
            "descricao": forms.Textarea(attrs={
                "class": "quill-editor",
                "id": "id_descricao",
            }),
        }


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
        widgets = {
            "solucao_tecnica": forms.Textarea(attrs={
                "class": "quill-editor",
                "id": "id_solucao_tecnica",
            }),
        }

    def clean_solucao_tecnica(self):
        solucao = self.cleaned_data.get("solucao_tecnica")
        if not solucao or not solucao.strip() or solucao.strip() in ("<p><br></p>", "<p></p>"):
            raise forms.ValidationError(
                "A solução técnica é obrigatória para encerrar o chamado.")
        return solucao


class AcaoChamadoForm(forms.ModelForm):
    class Meta:
        model = AcaoChamado
        fields = ["descricao"]
        widgets = {
            "descricao": forms.Textarea(attrs={
                "class": "quill-editor",
                "id": "id_descricao_acao",
            }),
        }

    def clean_descricao(self):
        descricao = self.cleaned_data.get("descricao")
        if not descricao or not descricao.strip() or descricao.strip() in ("<p><br></p>", "<p></p>"):
            raise forms.ValidationError("A descrição da ação não pode estar vazia.")
        return descricao
