import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Carregar variáveis de ambiente
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Configurações do banco de dados
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# Modelo para o log
class LogEntry(BaseModel):
    ip: str
    timestamp: str
    request: str
    status_code: int
    bytes: int


# Modelo para a lista de logs
class LogList(BaseModel):
    logs: List[LogEntry]


app = FastAPI()


# Função para obter conexão com o banco
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao conectar ao banco: {str(e)}"
        )


# Criar tabela se não existir
def create_table_if_not_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        ip VARCHAR(255),
        timestamp VARCHAR(255),
        request TEXT,
        status_code INTEGER,
        bytes INTEGER
    );
    """
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()


# Inicializar tabela na startup
@app.on_event("startup")
async def startup_event():
    create_table_if_not_exists()


# Endpoint GET /health
@app.get("/health")
async def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na saúde: {str(e)}")


# Endpoint POST /logs/ingest
@app.post("/logs/ingest")
async def ingest_logs(log_list: LogList):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO logs (ip, timestamp, request, status_code, bytes)
        VALUES (%s, %s, %s, %s, %s);
        """
        for log in log_list.logs:
            cursor.execute(
                insert_query,
                (log.ip, log.timestamp, log.request, log.status_code, log.bytes),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"{len(log_list.logs)} logs inseridos com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir logs: {str(e)}")


# Endpoint GET /logs/count
@app.get("/logs/count")
async def count_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"total_logs": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar logs: {str(e)}")


# Endpoint GET /logs/top-ips
@app.get("/logs/top-ips")
async def top_ips():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        SELECT ip, COUNT(*) as count
        FROM logs
        GROUP BY ip
        ORDER BY count DESC
        LIMIT 10;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        top_ips_list = [{"ip": row[0], "count": row[1]} for row in results]
        return {"top_ips": top_ips_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter top IPs: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
