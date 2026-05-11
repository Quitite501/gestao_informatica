from django import forms
from .models import Servidor, MudancaServidor


class ServidorForm(forms.ModelForm):
    class Meta:
        model = Servidor
        fields = [
            'nome', 'hostname', 'ip', 'sistema_operacional',
            'funcao', 'tipo', 'status', 'localizacao', 'observacoes'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'hostname': forms.TextInput(attrs={'class': 'form-input'}),
            'ip': forms.TextInput(attrs={'class': 'form-input'}),
            'sistema_operacional': forms.TextInput(attrs={'class': 'form-input'}),
            'funcao': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }


class MudancaServidorForm(forms.ModelForm):
    class Meta:
        model = MudancaServidor
        fields = ['tipo', 'titulo', 'descricao', 'chamado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Configuracao PAM aplicada'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Descreva o que foi feito, comandos aplicados, resultado...'}),
            'chamado': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chamado'].required = False
        self.fields['chamado'].empty_label = '— nenhum —'
