from django.contrib import admin
from .models import Servidor, MudancaServidor


class MudancaInline(admin.TabularInline):
    model = MudancaServidor
    extra = 0
    readonly_fields = ('criado_em', 'origem', 'autor')
    fields = ('tipo', 'titulo', 'descricao', 'origem', 'chamado', 'autor', 'criado_em')


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'hostname', 'ip', 'sistema_operacional', 'tipo', 'status')
    list_filter = ('tipo', 'status')
    search_fields = ('nome', 'hostname', 'ip')
    inlines = [MudancaInline]


@admin.register(MudancaServidor)
class MudancaServidorAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'titulo', 'tipo', 'origem', 'autor', 'criado_em')
    list_filter = ('tipo', 'origem', 'servidor')
    search_fields = ('titulo', 'descricao')
    readonly_fields = ('criado_em',)
