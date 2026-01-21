from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, desc, hour, to_timestamp, 
    regexp_extract, when, sum as _sum, avg, stddev
)
from pyspark.sql.types import IntegerType
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do PostgreSQL
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# URL JDBC
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_spark_session():
    """
    Cria sessão Spark com configurações otimizadas.
    """
    print("🚀 Inicializando Spark Session...")
    
    spark = SparkSession.builder \
        .appName("NASA Logs Analysis") \
        .config("spark.jars", "/app/postgresql-42.7.1.jar") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print("✅ Spark Session criada com sucesso!")
    return spark

def load_data_from_postgres(spark):
    """
    Carrega dados do PostgreSQL usando PySpark.
    """
    print("📥 Carregando dados do PostgreSQL...")
    
    df = spark.read \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", "logs") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load()
    
    print(f"✅ Dados carregados: {df.count():,} registros")
    return df

def basic_statistics(df):
    """
    1. Estatísticas Básicas
    """
    print("\n" + "="*60)
    print("📊 1. ESTATÍSTICAS BÁSICAS")
    print("="*60)
    
    total_logs = df.count()
    print(f"Total de Logs: {total_logs:,}")
    
    # IPs únicos
    unique_ips = df.select("ip").distinct().count()
    print(f"IPs Únicos: {unique_ips:,}")
    
    # Estatísticas de bytes
    stats = df.select(
        avg("bytes").alias("avg_bytes"),
        _sum("bytes").alias("total_bytes"),
        stddev("bytes").alias("stddev_bytes")
    ).collect()[0]
    
    print(f"Bytes Médios: {stats['avg_bytes']:.2f}")
    print(f"Total de Bytes: {stats['total_bytes']:,}")
    print(f"Desvio Padrão: {stats['stddev_bytes']:.2f}")
    
    # Distribuição de status codes
    print("\n📈 Distribuição de Status Codes:")
    df.groupBy("response") \
        .agg(count("*").alias("count")) \
        .orderBy(desc("count")) \
        .show(10)

def top_ips_analysis(df):
    """
    2. Top IPs Mais Ativos
    """
    print("\n" + "="*60)
    print("🌐 2. TOP 20 IPs MAIS ATIVOS")
    print("="*60)
    
    top_ips = df.groupBy("ip") \
        .agg(
            count("*").alias("ip"),
            _sum("bytes").alias("total_bytes"),
            avg("bytes").alias("avg_bytes")
        ) \
        .orderBy(desc("ip")) \
        .limit(20)
    
    top_ips.show(20, truncate=False)
    
    return top_ips

def resource_analysis(df):
    """
    3. Recursos Mais Acessados
    """
    print("\n" + "="*60)
    print("📂 3. TOP 20 RECURSOS MAIS ACESSADOS")
    print("="*60)
    
    # Extrair path da request (GET /path HTTP/1.0 -> /path)
    df_with_path = df.withColumn(
        "path",
        regexp_extract(col("url"), r"^\w+\s+(\S+)", 1)
    )
    
    top_resources = df_with_path.groupBy("path") \
        .agg(
            count("*").alias("urls"),
            _sum("bytes").alias("total_bytes")
        ) \
        .orderBy(desc("urls")) \
        .limit(20)
    
    top_resources.show(20, truncate=False)
    
    return top_resources

def http_methods_analysis(df):
    """
    4. Análise de Métodos HTTP
    """
    print("\n" + "="*60)
    print("🔧 4. DISTRIBUIÇÃO DE MÉTODOS HTTP")
    print("="*60)
    
    # Extrair método HTTP (GET, POST, etc)
    df_with_method = df.withColumn(
        "method",
        regexp_extract(col("method"), r"^(\w+)", 1)
    )
    
    methods = df_with_method.groupBy("method") \
        .agg(count("*").alias("count")) \
        .orderBy(desc("count"))
    
    methods.show()
    
    return methods

def error_analysis(df):
    """
    5. Análise de Erros (4xx, 5xx)
    """
    print("\n" + "="*60)
    print("❌ 5. ANÁLISE DE ERROS")
    print("="*60)
    
    # Filtrar apenas erros 4xx e 5xx
    errors = df.filter(
        (col("response") >= 400) & (col("response") < 600)
    )
    
    total_errors = errors.count()
    print(f"Total de Erros: {total_errors:,}")
    
    print("\n📊 Top 10 IPs com Mais Erros:")
    errors.groupBy("ip") \
        .agg(count("*").alias("error_count")) \
        .orderBy(desc("error_count")) \
        .show(10, truncate=False)
    
    print("\n📊 Distribuição de Códigos de Erro:")
    errors.groupBy("response") \
        .agg(count("*").alias("count")) \
        .orderBy(desc("count")) \
        .show()
    
    return errors

def suspicious_ips_detection(df):
    """
    6. Detecção de IPs Suspeitos (Possível DDoS/Brute Force)
    """
    print("\n" + "="*60)
    print("🚨 6. DETECÇÃO DE IPs SUSPEITOS")
    print("="*60)
    
    # Calcular requests por IP
    ip_stats = df.groupBy("ip") \
        .agg(
            count("*").alias("request_count"),
            avg("bytes").alias("avg_bytes")
        )
    
    # Calcular média e desvio padrão GLOBAL (do ip_stats, não do df original)
    global_stats = ip_stats.agg(
        avg("request_count").alias("mean_requests"),
        stddev("request_count").alias("stddev_requests")
    ).collect()[0]
    
    mean_requests = global_stats['mean_requests']
    stddev_requests = global_stats['stddev_requests']
    
    print(f"📊 Estatísticas Globais:")
    print(f"   Média de requests por IP: {mean_requests:.2f}")
    print(f"   Desvio padrão: {stddev_requests:.2f}")
    
    # Definir threshold: média + 3 * desvio padrão (Z-score > 3)
    # Ou use um threshold fixo se preferir
    if stddev_requests and stddev_requests > 0:
        threshold = mean_requests + (3 * stddev_requests)
        print(f"   Threshold calculado (Z-score > 3): {threshold:.2f}")
    else:
        threshold = 1000  # Fallback para threshold fixo
        print(f"   Usando threshold fixo: {threshold}")
    
    # Filtrar IPs suspeitos
    suspicious = ip_stats.filter(col("request_count") > threshold) \
        .orderBy(desc("request_count"))
    
    suspicious_count = suspicious.count()
    print(f"\nIPs Suspeitos Detectados: {suspicious_count}")
    
    if suspicious_count > 0:
        print("\n⚠️ Top 20 IPs Suspeitos:")
        suspicious.show(20, truncate=False)
    else:
        print("\n✅ Nenhum IP suspeito detectado com o threshold atual")
    
    return suspicious

def save_results_to_postgres(df, table_name):
    """
    Salva resultados de volta no PostgreSQL com tratamento de erros.
    """
    print(f"\n💾 Salvando resultados em: {table_name}")
    
    try:
        # Verificar se o DataFrame está vazio
        count = df.count()
        if count == 0:
            print(f"⚠️ DataFrame vazio, pulando salvamento de '{table_name}'")
            return
        
        print(f"   Registros a salvar: {count}")
        
        # Configurar propriedades JDBC
        properties = {
            "user": DB_USER,
            "password": DB_PASSWORD,
            "driver": "org.postgresql.Driver"
        }
        
        # Salvar no PostgreSQL
        df.write \
            .jdbc(
                url=JDBC_URL,
                table=table_name,
                mode="overwrite",
                properties=properties
            )
        
        print(f"✅ Tabela '{table_name}' criada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao salvar tabela '{table_name}': {str(e)}")
        print(f"   Tipo de erro: {type(e).__name__}")
        
        # Tentar salvar como fallback (sem JDBC, apenas log)
        print(f"   Mostrando primeiros registros em vez de salvar:")
        df.show(10, truncate=False)

def main():
    """
    Pipeline principal de análise.
    """
    print("\n" + "="*60)
    print("🔥 ANÁLISE DE LOGS NASA COM PYSPARK")
    print("="*60)
    
    # 1. Criar Spark Session
    spark = create_spark_session()
    
    # 2. Carregar dados
    df = load_data_from_postgres(spark)
    
    # Cache para performance
    df.cache()
    
    # 3. Análises
    basic_statistics(df)
    top_ips = top_ips_analysis(df)
    top_resources = resource_analysis(df)
    methods = http_methods_analysis(df)
    errors = error_analysis(df)
    suspicious = suspicious_ips_detection(df)
    
    # 4. Salvar resultados no PostgreSQL
    print("\n" + "="*60)
    print("💾 SALVANDO RESULTADOS NO POSTGRESQL")
    print("="*60)
    
    save_results_to_postgres(top_ips, "analysis_top_ips")
    save_results_to_postgres(top_resources, "analysis_top_resources")
    save_results_to_postgres(methods, "analysis_http_methods")
    save_results_to_postgres(suspicious, "analysis_suspicious_ips")
    
    # 5. Finalizar
    print("\n" + "="*60)
    print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*60)
    
    spark.stop()

if __name__ == "__main__":
    main()