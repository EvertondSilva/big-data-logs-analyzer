# Usar imagem base Python 3.11
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    default-jdk-headless \
    wget \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Configurar JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY api.py .
COPY kaggle/etl_download.py ./etl_download.py
COPY kaggle/etl_load.py ./etl_load.py
COPY PySpark/spark_analysis.py ./spark_analysis.py
COPY wait-for-postgres.sh .
COPY .env .

# Tornar script executável
RUN chmod +x wait-for-postgres.sh

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

# Criar script de inicialização otimizado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "================================================"\n\
echo "🚀 INICIANDO PIPELINE NASA ETL"\n\
echo "================================================"\n\
echo ""\n\
\n\
# Função para testar conexão PostgreSQL\n\
test_postgres() {\n\
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1\n\
    return $?\n\
}\n\
\n\
# Aguardar PostgreSQL aceitar conexões\n\
echo "⏳ Aguardando PostgreSQL aceitar conexões..."\n\
max_attempts=60\n\
attempt=1\n\
\n\
while [ $attempt -le $max_attempts ]; do\n\
    if test_postgres; then\n\
        echo "✅ PostgreSQL está aceitando conexões!"\n\
        break\n\
    fi\n\
    echo "   Tentativa $attempt/$max_attempts - Aguardando PostgreSQL..."\n\
    sleep 2\n\
    attempt=$((attempt + 1))\n\
done\n\
\n\
if [ $attempt -gt $max_attempts ]; then\n\
    echo "❌ Timeout: PostgreSQL não respondeu a tempo"\n\
    exit 1\n\
fi\n\
\n\
# Aguardar mais 5 segundos para garantir que o banco está estável\n\
echo "⏳ Aguardando estabilização do banco (5s)..."\n\
sleep 5\n\
\n\
# Iniciar API em background\n\
echo ""\n\
echo "================================================"\n\
echo "🚀 INICIANDO API FASTAPI (Porta 8002)"\n\
echo "================================================"\n\
python api.py &\n\
API_PID=$!\n\
echo "API iniciada com PID: $API_PID"\n\
\n\
# Aguardar API estar respondendo\n\
echo ""\n\
echo "⏳ Aguardando API inicializar..."\n\
max_attempts=30\n\
attempt=1\n\
\n\
while [ $attempt -le $max_attempts ]; do\n\
    if curl -s http://localhost:8002/health >/dev/null 2>&1; then\n\
        echo "✅ API está respondendo no endpoint /health!"\n\
        break\n\
    fi\n\
    echo "   Tentativa $attempt/$max_attempts - Aguardando API..."\n\
    sleep 2\n\
    attempt=$((attempt + 1))\n\
done\n\
\n\
if [ $attempt -gt $max_attempts ]; then\n\
    echo "❌ Timeout: API não respondeu a tempo"\n\
    kill $API_PID 2>/dev/null || true\n\
    exit 1\n\
fi\n\
\n\
# Aguardar mais um pouco para garantir que a API está estável\n\
echo "⏳ Aguardando estabilização da API (3s)..."\n\
sleep 3\n\
\n\
# Executar ETL Load\n\
echo ""\n\
echo "================================================"\n\
echo "📥 EXECUTANDO ETL LOAD"\n\
echo "================================================"\n\
\n\
if python etl_load.py; then\n\
    echo ""\n\
    echo "✅ ETL Load concluído com sucesso!"\n\
else\n\
    echo ""\n\
    echo "⚠️ ETL Load falhou (código de saída: $?)"\n\
    echo "⚠️ Continuando para manter API rodando..."\n\
fi\n\
\n\
# Aguardar antes do PySpark\n\
echo ""\n\
echo "⏳ Aguardando 5 segundos antes da análise PySpark..."\n\
sleep 5\n\
\n\
# Executar análise PySpark\n\
echo ""\n\
echo "================================================"\n\
echo "🔥 EXECUTANDO ANÁLISE PYSPARK"\n\
echo "================================================"\n\
\n\
if python spark_analysis.py; then\n\
    echo ""\n\
    echo "✅ Análise PySpark concluída com sucesso!"\n\
else\n\
    echo ""\n\
    echo "⚠️ Análise PySpark falhou (código de saída: $?)"\n\
    echo "⚠️ API continua rodando..."\n\
fi\n\
\n\
# Pipeline concluído\n\
echo ""\n\
echo "================================================"\n\
echo "✅ PIPELINE CONCLUÍDO!"\n\
echo "================================================"\n\
echo "📊 API: http://localhost:8002"\n\
echo "📊 Health: http://localhost:8002/health"\n\
echo "📈 Dashboard: http://localhost:8050"\n\
echo "================================================"\n\
echo ""\n\
echo "🔄 API rodando... (use Ctrl+C para parar)"\n\
\n\
# Manter API rodando em primeiro plano\n\
wait $API_PID\n' > /app/start.sh && chmod +x /app/start.sh

# Comando para executar
CMD ["/app/start.sh"]