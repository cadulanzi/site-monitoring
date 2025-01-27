# Use a versão mínima do Python para reduzir tamanho da imagem
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema para compilar pacotes (ex: gcc, libpq-dev, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*  # Limpa cache para reduzir o tamanho da imagem

# Copia o arquivo de dependências antes de copiar todo o código
COPY requirements.txt /app/requirements.txt

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte para dentro do container
COPY . /app

# Expõe a porta do FastAPI
EXPOSE 8000

# Define o comando de execução do serviço
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
