from django import forms
from django.db.models import Q
from .models import Chamado, FeriadoDiaAtipico, CategoriaChamado, AcaoChamado


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["solicitante", "titulo", "descricao", "categoria", "prioridade"]
        widgets = {
            "solicitante": forms.Select(attrs={
                "class": "tom-select tom-select-solicitante",
                "autocomplete": "off",
                "data-placeholder": "Digite para buscar o solicitante",
            }),
            "titulo": forms.TextInput(attrs={
                "class": "form-input chamado-input-padrao",
                "placeholder": "Informe um titulo objetivo do chamado",
                "maxlength": "255",
                "data-maxlength": "255",
                "autocomplete": "off",
            }),
            "categoria": forms.Select(attrs={
                "class": "tom-select tom-select-categoria",
                "autocomplete": "off",
                "data-placeholder": "Selecione a categoria",
                "data-tooltip": "A categoria influencia o calculo do SLA.",
            }),
            "prioridade": forms.Select(attrs={
                "class": "form-input chamado-input-padrao chamado-prioridade-select",
                "data-prioridade": "1",
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        from django.contrib.auth import get_user_model
        Usuario = get_user_model()

        solicitante_id = None
        if self.is_bound:
            solicitante_id = self.data.get(self.add_prefix("solicitante"))
        elif self.initial.get("solicitante"):
            solicitante_id = self.initial.get("solicitante")
        elif getattr(self.instance, "solicitante_id", None):
            solicitante_id = self.instance.solicitante_id

        if solicitante_id:
            self.fields["solicitante"].queryset = (
                Usuario.objects
                .filter(pk=solicitante_id)
                .select_related("setor")
            )
        else:
            self.fields["solicitante"].queryset = Usuario.objects.none()

        self.fields["solicitante"].label_from_instance = self._label_solicitante

        self.fields["categoria"].queryset = CategoriaChamado.objects.filter(
            ativo=True
        ).order_by("nome")

        for nome in ["solicitante", "titulo", "descricao", "categoria", "prioridade"]:
            self.fields[nome].required = True

        if user and not self._pode_escolher_solicitante(user):
            self.fields["solicitante"].initial = user.pk
            self.fields["solicitante"].queryset = Usuario.objects.filter(pk=user.pk)
            self.fields["solicitante"].widget = forms.HiddenInput()

    @staticmethod
    def _label_solicitante(usuario):
        setor = getattr(usuario, "setor", None)
        if setor:
            return f"{usuario.nome_completo} - {setor.nome}"
        return usuario.nome_completo or usuario.get_username()

    @staticmethod
    def _pode_escolher_solicitante(user):
        return (
            user.is_superuser
            or user.is_staff
            or user.has_perm("chamados.can_manage_chamados")
        )

    def clean_titulo(self):
        titulo = (self.cleaned_data.get("titulo") or "").strip()
        if not titulo:
            raise forms.ValidationError("Informe o titulo do chamado.")
        return titulo

    def clean_solicitante(self):
        solicitante = self.cleaned_data.get("solicitante")
        user = getattr(self, "user", None)

        if user and not self._pode_escolher_solicitante(user):
            return user

        return solicitante


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


class FeriadoDiaAtipicoForm(forms.ModelForm):
    class Meta:
        model = FeriadoDiaAtipico
        fields = ["data", "descricao", "tipo", "contabiliza_sla",
                  "hora_inicio_especial", "hora_fim_especial"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio_especial": forms.TimeInput(attrs={"type": "time"}),
            "hora_fim_especial": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        contabiliza = cleaned.get("contabiliza_sla")
        h_ini = cleaned.get("hora_inicio_especial")
        h_fim = cleaned.get("hora_fim_especial")
        if tipo == "dia_atipico_com_expediente" and contabiliza:
            if not h_ini or not h_fim:
                raise forms.ValidationError(
                    "Dias atipicos com expediente especial exigem horario de inicio e fim."
                )
            if h_ini >= h_fim:
                raise forms.ValidationError(
                    "O horario de inicio deve ser anterior ao horario de fim."
                )
        return cleaned
