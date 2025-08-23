FROM docker.n8n.io/n8nio/n8n

USER root

# 1. Instala TODAS as dependências do sistema necessárias para a compilação
RUN apk add --no-cache ffmpeg python3 py3-pip python3-dev \
    build-base gcc gfortran musl-dev \
    lapack-dev blas-dev libsndfile-dev openblas-dev \
    ffmpeg-dev cmake ninja llvm-dev

# 2. Copia APENAS a lista de pacotes Python
WORKDIR /app
COPY requirements.txt ./

# 3. Cria o venv e instala os pacotes
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 4. Adiciona o venv ao PATH
ENV PATH="/opt/venv/bin:$PATH"

# 5. Copia seus scripts
COPY ./scripts/*.py /scripts/
RUN mkdir -p /scripts && \
    chmod +x /scripts/*.py

# Configura o diretório de trabalho de volta e muda o usuário
WORKDIR /data
USER node
