# Base: imagem OFICIAL do n8n (Alpine), versao PINADA.
# Para atualizar o n8n no futuro, troque o numero abaixo de forma consciente.
FROM docker.n8n.io/n8nio/n8n:2.11.4

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

# Volta para o usuario padrao da imagem oficial
USER node

# IMPORTANTE: NAO redefinir CMD nem ENTRYPOINT.
# A imagem oficial ja inicia o n8n corretamente — era o CMD manual
# que causava o erro "Command start not found".
