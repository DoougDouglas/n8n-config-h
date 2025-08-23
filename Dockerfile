FROM docker.n8n.io/n8nio/n8n

USER root

# Instala ffmpeg + python + pip + compiladores e libs
RUN apk add --no-cache ffmpeg python3 py3-pip \
    build-base gcc gfortran musl-dev \
    lapack-dev blas-dev libsndfile-dev openblas-dev

# Instala as bibliotecas Python necessárias
RUN pip3 install --no-cache-dir numpy scipy librosa reportlab aubio praat-parselmouth

# Cria diretório pros scripts
RUN mkdir -p /scripts

# Copia os scripts para dentro do container
COPY ./scripts/*.py /scripts/

# Garante que os scripts podem rodar
RUN chmod +x /scripts/*.py

USER node
