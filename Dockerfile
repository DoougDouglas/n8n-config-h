FROM docker.n8n.io/n8nio/n8n

USER root

# Instala ffmpeg + python + pip + compiladores e libs
RUN apk add --no-cache ffmpeg python3 py3-pip python3-dev \
    build-base gcc gfortran musl-dev \
    lapack-dev blas-dev libsndfile-dev openblas-dev

# --- Início da Modificação ---

# 1. Cria um ambiente virtual em /opt/venv
RUN python3 -m venv /opt/venv

# 2. Adiciona o executável do venv ao PATH do sistema
#    Isso faz com que os comandos 'python' e 'pip' usem o venv por padrão
ENV PATH="/opt/venv/bin:$PATH"

# --- Fim da Modificação ---

# Instala as bibliotecas Python necessárias (agora dentro do venv)
RUN pip install --no-cache-dir numpy scipy librosa reportlab aubio praat-parselmouth

# Cria diretório pros scripts
RUN mkdir -p /scripts

# Copia os scripts para dentro do container
COPY ./scripts/*.py /scripts/

# Garante que os scripts podem rodar
RUN chmod +x /scripts/*.py

USER node
