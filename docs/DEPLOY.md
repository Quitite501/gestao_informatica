# Implantacao - Sistema de Gestao de TI

## Diretorio da aplicacao

/opt/sistema_ti

## Plataforma

- Ubuntu 24.04 LTS
- Python 3.12
- Django
- PostgreSQL
- Gunicorn
- Nginx
- systemd
- Node.js / Tailwind CSS

## Ambiente Python

Criar o ambiente virtual e instalar as dependencias:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Variaveis de ambiente

Criar o arquivo:

    /opt/sistema_ti/.env

Usar `.env.example` como referencia.

O arquivo `.env` real nunca deve ser versionado.

## Banco PostgreSQL

Variaveis utilizadas:

- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT

Depois de preparar o banco:

    python manage.py migrate

## Frontend

Instalar as dependencias:

    npm ci

Gerar o CSS:

    npm run build:css

## Arquivos estaticos

    python manage.py collectstatic --noinput

## Gunicorn

Configuracao:

    gunicorn.conf.py

Bind atual:

    127.0.0.1:8001

## systemd

Arquivo de referencia:

    deploy/systemd/sistema_ti.service

Instalacao:

    sudo cp deploy/systemd/sistema_ti.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable sistema_ti
    sudo systemctl restart sistema_ti

## Nginx

Arquivo de referencia:

    deploy/nginx/sistema_ti.conf

Instalacao:

    sudo cp deploy/nginx/sistema_ti.conf /etc/nginx/sites-available/sistema_ti
    sudo ln -s /etc/nginx/sites-available/sistema_ti /etc/nginx/sites-enabled/sistema_ti
    sudo nginx -t
    sudo systemctl reload nginx

## HTTPS

Arquivos utilizados atualmente:

    /etc/nginx/ssl/sistema_ti.crt
    /etc/nginx/ssl/sistema_ti.key

A chave privada nunca deve ser armazenada no Git.

## Logs

Gunicorn:

    /opt/sistema_ti/logs/gunicorn_access.log
    /opt/sistema_ti/logs/gunicorn_error.log

Django:

    /opt/sistema_ti/logs/

Logs nao devem ser versionados.

## Midia

Uploads da aplicacao:

    /opt/sistema_ti/media/

O diretorio `media` nao faz parte do Git e precisa de backup separado.
