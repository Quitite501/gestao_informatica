from django import forms
from .models import Chamado, CategoriaChamado, AcaoChamado


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solicitante", "titulo", "descricao", "categoria", "prioridade"]


class ChamadoFiltroForm(forms.Form):
    """
    Formulário de filtro com suporte a múltipla seleção.
    Define valores padrão: Aberto, Em atendimento, Aguardando usuário.
    """
    
    status = forms.MultipleChoiceField(
        choices=Chamado.STATUS_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'multi-select-dropdown'}),
        label="Status",
    )
    
    categoria = forms.ModelMultipleChoiceField(
        queryset=CategoriaChamado.objects.filter(ativo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'multi-select-dropdown'}),
        label="Categoria",
    )
    
    prioridade = forms.MultipleChoiceField(
        choices=Chamado.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'multi-select-dropdown'}),
        label="Prioridade",
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data início",
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data fim",
    )

    solicitante_nome = forms.CharField(
        required=False,
        label="Solicitante",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nome do solicitante...',
            'class': 'form-input',
        }),
    )
    
    def __init__(self, *args, **kwargs):
        """
        Define valores padrão apenas quando o formulário é carregado
        sem parâmetros GET (primeira vez que a tela é aberta).
        """
        super().__init__(*args, **kwargs)
        
        # Se não há dados GET, aplica filtros padrão
        if not self.data:
            self.initial['status'] = [
                Chamado.STATUS_ABERTO,
                Chamado.STATUS_EM_ATENDIMENTO,
                Chamado.STATUS_AGUARDANDO,
            ]


class ChamadoEncerramentoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solucao_tecnica"]
    
    def clean_solucao_tecnica(self):
        solucao = self.cleaned_data.get("solucao_tecnica")
        if not solucao or not solucao.strip():
            raise forms.ValidationError(
                "A solução técnica é obrigatória para encerrar o chamado."
            )
        return solucao


class AcaoChamadoForm(forms.ModelForm):
    class Meta:
        model = AcaoChamado
        fields = ["descricao"]
        widgets = {
            "descricao": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Descreva a acao realizada...",
                "class": "form-input",
            }),
        }
