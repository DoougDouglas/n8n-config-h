# PASSO 1: Usar uma imagem base oficial do Python com Debian "Bookworm"
FROM python:3.12-slim-bookworm

# Define o usuário como root para instalar pacotes
USER root

# Instala as dependências de sistema com 'apt-get' (o gerenciador do Debian)
# - nodejs e npm: para instalar o n8n
# - ffmpeg: para seus scripts de áudio
# - build-essential: caso alguma pequena compilação ainda seja necessária
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala o n8n globalmente usando npm
RUN npm install -g n8n

# Cria um usuário não-root 'node' para rodar a aplicação (boa prática de segurança)
# A imagem oficial do n8n também usa um usuário chamado 'node'
RUN useradd -ms /bin/bash node

# Copia os requirements e define o diretório de trabalho
WORKDIR /app
COPY requirements.txt ./

# Instala as bibliotecas Python (isso será MUITO mais rápido agora)
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
