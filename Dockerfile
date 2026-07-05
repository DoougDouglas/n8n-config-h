# Base Debian (Bookworm) com Python 3.12 — a mesma que voce ja usava.
# E a base certa para o seu stack de audio: aubio, parselmouth, llvmlite etc.
# baixam wheels prontos (glibc) ou compilam de boa no gcc do Debian.
FROM python:3.12-slim-bookworm

USER root

# Node.js 22 + ffmpeg + wget (healthcheck) + build-essential (compila aubio e modulos nativos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# n8n PINADO na 2.0.2 — NUNCA usar @latest (foi isso que derrubou tudo).
# 2.0.2 e a versao 2.x compativel com este modelo de instalacao customizada.
RUN npm cache clean --force && npm install -g n8n@2.0.2

# Usuario nao-root para rodar a aplicacao
RUN useradd -ms /bin/bash node

# Bibliotecas Python (maioria via wheels prontos no Debian)
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Seus scripts
COPY ./scripts/ /scripts/
RUN chmod +x /scripts/*.py

# Pasta de trabalho persistente para arquivos dos workflows (montada via volume no compose)
RUN mkdir -p /files

# Home do n8n e permissoes
RUN mkdir -p /home/node/.n8n \
    && chown -R node:node /app /scripts /files /home/node

USER node

# Inicia o n8n (comando padrao = start)
CMD ["n8n"]
