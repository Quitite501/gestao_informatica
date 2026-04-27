from django import forms
from django.db.models import Q
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

class ChamadoEditarTituloForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["titulo"]
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-input w-full",
                "placeholder": "Novo título do chamado...",
                "maxlength": "255",
            }),
        }
        labels = {
            "titulo": "Título do chamado",
        }


class ChamadoTransferirForm(forms.Form):
    novo_tecnico = forms.ModelChoiceField(
        queryset=None,
        label="Transferir para",
        widget=forms.Select(attrs={"class": "form-input w-full"}),
        empty_label="Selecione o técnico...",
    )
    motivo = forms.CharField(
        required=False,
        label="Motivo da transferência",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": "form-input w-full",
            "placeholder": "Informe o motivo da transferência (opcional)...",
        }),
    )

    def __init__(self, *args, tecnico_atual=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        Usuario = get_user_model()
        perm = Permission.objects.get(codename="can_manage_chamados")
        tecnicos = Usuario.objects.filter(
            Q(groups__permissions=perm) | Q(user_permissions=perm)
        ).distinct().order_by("nome_completo")
        if tecnico_atual:
            tecnicos = tecnicos.exclude(pk=tecnico_atual.pk)
        self.fields["novo_tecnico"].queryset = tecnicos
