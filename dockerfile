# Usar imagem base Python 3.11
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências do sistema (Java para PySpark)
RUN apt-get update && apt-get install -y \
    default-jdk-headless \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Configurar JAVA_HOME (caminho padrão do default-jdk)
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY api.py .
COPY kaggle/etl_download.py ./etl_download.py
COPY kaggle/etl_load.py ./etl_load.py
COPY PySpark/spark_analysis.py ./spark_analysis.py
COPY .env .

# Criar diretório para dados
RUN mkdir -p /app/data

# Baixar driver JDBC PostgreSQL
RUN wget https://jdbc.postgresql.org/download/postgresql-42.7.1.jar -O /app/postgresql-42.7.1.jar

# Criar diretório .cache para kagglehub
RUN mkdir -p /root/.cache/kagglehub

# Baixar dataset NASA automaticamente
RUN python etl_download.py || echo "⚠️ Download falhou, continuando..."

# Expor porta 8002
EXPOSE 8002

# Criar script de inicialização bash
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Iniciando API..."\n\
python api.py &\n\
API_PID=$!\n\
\n\
echo "⏳ Aguardando API iniciar (10s)..."\n\
sleep 10\n\
\n\
echo "📥 Carregando dados no PostgreSQL..."\n\
python etl_load.py\n\
\n\
echo "⏳ Aguardando carga concluir (5s)..."\n\
sleep 5\n\
\n\
echo "🔥 Iniciando análise PySpark..."\n\
python spark_analysis.py\n\
\n\
echo "✅ Pipeline completo! API rodando..."\n\
wait $API_PID\n' > /app/start.sh && chmod +x /app/start.sh

# Comando para executar o script de inicialização
CMD ["/app/start.sh"]