# Usar imagem base Python 3.11
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY api.py .
COPY .env .

# Expor porta 8000
EXPOSE 8000

# Comando para rodar a API
CMD ["python", "api.py"]