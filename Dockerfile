# Base: imagem OFICIAL do n8n via Docker Hub, PINADA na 2.0.2.
# ATENCAO: NAO subir para 2.1.0+ neste Dockerfile! A partir da 2.1.0 a imagem
# oficial e "hardened" (sem apk/apt-get) e nao aceita mais instalacao de pacotes.
# A 2.0.2 e a ultima versao extensivel da linha 2.x.
FROM n8nio/n8n:2.0.2

# Root apenas para instalar pacotes
USER root

# ffmpeg + Python 3 + pip (Alpine usa apk, nao apt-get)
RUN apk add --no-cache ffmpeg python3 py3-pip

# Bibliotecas Python do requirements.txt
# (instala deps de compilacao temporarias e remove depois, para libs que compilam codigo nativo)
COPY requirements.txt /tmp/requirements.txt
RUN apk add --no-cache --virtual .build-deps gcc g++ musl-dev python3-dev libffi-dev \
    && pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt \
    && apk del .build-deps \
    && rm /tmp/requirements.txt

# Seus scripts
COPY ./scripts/ /scripts/
RUN chmod +x /scripts/*.py && chown -R node:node /scripts

# Pasta de trabalho para arquivos dos workflows (TXTs, etc.)
# Sera montada como volume persistente no docker-compose
RUN mkdir -p /files && chown -R node:node /files

# Volta para o usuario padrao da imagem oficial
USER node

# IMPORTANTE: NAO redefinir CMD nem ENTRYPOINT.
# A imagem oficial ja inicia o n8n corretamente — era o CMD manual
# que causava o erro "Command start not found".
