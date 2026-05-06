from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Setor, Plataforma, CredencialExterna


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = (
        "username",
        "nome_completo",
        "email",
        "login_rede",
        "setor",
        "ativo",
        "is_staff",
    )
    list_filter = ("ativo", "is_staff", "is_superuser", "groups", "setor")
    search_fields = ("username", "nome_completo", "email", "login_rede")
    ordering = ("nome_completo",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Dados operacionais",
            {
                "fields": (
                    "nome_completo",
                    "login_rede",
                    "ramal",
                    "cargo",
                    "setor",
                    "ativo",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Dados adicionais",
            {
                "fields": (
                    "email",
                    "nome_completo",
                    "login_rede",
                    "ramal",
                    "cargo",
                    "setor",
                    "ativo",
                )
            },
        ),
    )


@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'url', 'ativo', 'criado_em')
    search_fields = ('nome',)
    list_filter = ('ativo',)
