# Sistema de Gestao de TI

Sistema web interno para gestao da infraestrutura e operacao de TI.

## Modulos

- Usuarios e setores
- Patrimonio
- Chamados
- Servidores
- Notas fiscais
- Licencas
- Auditoria
- Relatorios

## Stack

- Python
- Django
- PostgreSQL
- Gunicorn
- Nginx
- Tailwind CSS
- JavaScript
- Django REST Framework

## Instalacao

Consulte `docs/DEPLOY.md`.

## Dependencias Python

    pip install -r requirements.txt

## Frontend

    npm ci
    npm run build:css

## Configuracao

Copiar `.env.example` para `.env` e preencher os valores reais localmente.

O `.env` nunca deve ser enviado ao Git.

## Producao

- systemd: `deploy/systemd/sistema_ti.service`
- Nginx: `deploy/nginx/sistema_ti.conf`
- Gunicorn: `gunicorn.conf.py`

## Nao armazenar no Git

- `.env`
- dumps do banco
- backups
- uploads em `media/`
- logs
- certificados e chaves privadas
- `venv`
- `node_modules`
