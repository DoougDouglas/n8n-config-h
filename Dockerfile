# PASSO 1: Usar uma imagem base oficial do Python com Debian "Bookworm"
FROM python:3.12-slim-bookworm

# Define o usuário como root para instalar pacotes
USER root

# Instala as dependências de sistema, mas agora forçando a instalação do Node.js v20
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Limpa o cache do NPM e instala o n8n globalmente para garantir uma instalação limpa
RUN npm cache clean --force && npm install -g n8n

# Cria um usuário não-root 'node' para rodar a aplicação (boa prática de segurança)
RUN useradd -ms /bin/bash node

# Copia os requirements e define o diretório de trabalho
WORKDIR /app
COPY requirements.txt ./

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia seus scripts
COPY ./scripts/ /scripts/
RUN chmod +x /scripts/*.py

# Muda a propriedade dos arquivos para o usuário 'node'
RUN chown -R node:node /app /scripts

# Muda para o usuário 'node'
USER node

# Define o comando padrão para iniciar o n8n quando o contêiner rodar
CMD ["n8n"]
