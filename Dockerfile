FROM docker.n8n.io/n8nio/n8n

USER root

# Instala ffmpeg, python, compiladores e as libs de desenvolvimento do Python
# A linha abaixo foi a principal alteração
RUN apk add --no-cache ffmpeg python3 py3-pip python3-dev \
    build-base gcc gfortran musl-dev \
    lapack-dev blas-dev libsndfile-dev openblas-dev

# Cria um ambiente virtual em /opt/venv
RUN python3 -m venv /opt/venv

# Adiciona o executável do venv ao PATH do sistema
ENV PATH="/opt/venv/bin:$PATH"

# Atualiza pip e instala as bibliotecas Python necessárias (agora dentro do venv)
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir numpy scipy librosa reportlab aubio praat-parselmouth

# Cria diretório pros scripts
RUN mkdir -p /scripts

# Copia os scripts para dentro do container
COPY ./scripts/*.py /scripts/

# Garante que os scripts podem rodar
RUN chmod +x /scripts/*.py

USER node
