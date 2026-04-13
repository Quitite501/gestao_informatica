from django.contrib import admin
from .models import Patrimonio, TipoEquipamento, MovimentacaoPatrimonio


@admin.register(TipoEquipamento)
class TipoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)


class MovimentacaoInline(admin.TabularInline):
    model = MovimentacaoPatrimonio
    extra = 0
    readonly_fields = ("tipo", "usuario_anterior", "usuario_novo", "setor_anterior",
                       "setor_novo", "status_anterior", "status_novo", "registrado_por", "data")
    can_delete = False


@admin.register(Patrimonio)
class PatrimonioAdmin(admin.ModelAdmin):
    list_display = ("etiqueta", "tipo", "marca", "modelo", "setor", "usuario_atual", "status")
    list_filter = ("status", "tipo", "setor")
    search_fields = ("etiqueta", "marca", "modelo", "numero_serie")
    readonly_fields = ("criado_por", "criado_em", "atualizado_em")
    inlines = [MovimentacaoInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(MovimentacaoPatrimonio)
class MovimentacaoPatrimonioAdmin(admin.ModelAdmin):
    list_display = ("patrimonio", "tipo", "usuario_anterior", "usuario_novo", "registrado_por", "data")
    list_filter = ("tipo",)
    search_fields = ("patrimonio__etiqueta",)
    readonly_fields = ("data",)
