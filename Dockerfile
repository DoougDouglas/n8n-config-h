FROM docker.n8n.io/n8nio/n8n

USER root

# Instala ffmpeg + python + pip
RUN apk add --no-cache ffmpeg python3 py3-pip

# Instala bibliotecas Python que vamos usar
RUN pip3 install --no-cache-dir numpy librosa parselmouth reportlab aubio

# Cria diretório pros scripts
RUN mkdir -p /scripts

# Copia os scripts para dentro do container
COPY ./scripts/*.py /scripts/

# Garante que os scripts podem rodar
RUN chmod +x /scripts/*.py

USER node
