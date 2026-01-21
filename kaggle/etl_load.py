import re
import requests
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path("data")
API_URL = "http://localhost:8002"


def parse_tsv_line(line: str, line_num: int = 0) -> Optional[Dict]:
    """
    Parseia linha tentando múltiplos formatos.
    """
    line = line.strip()

    if not line:
        return None

    # DEBUG: Mostrar primeiras 3 linhas para entender formato
    if line_num <= 3:
        print(f"\n🔍 DEBUG Linha {line_num}:")
        print(f"   Raw: {repr(line[:150])}")

    # FORMATO 1: TSV puro (5 colunas separadas por TAB)
    if "\t" in line:
        parts = line.split("\t")

        if line_num <= 3:
            print(f"   TSV: {len(parts)} partes, {parts}")
            for i, p in enumerate(parts[:7]):
                print(f"     [{i}]: {repr(p[:50])}")

        if len(parts) >= 5:
            try:
                result = {
                    "ip": parts[0].strip().strip('"'),
                    "login_name": parts[1].strip().strip('"'),
                    "time": parts[2].strip().strip('"'),
                    "method": parts[3].strip().strip('"'),
                    "url": parts[4].strip().strip('"'),
                    "response": int(parts[5].strip()),
                    "bytes_": int(parts[6].strip()),
                }
                if line_num <= 3:
                    print(f"   ✅ TSV parseado com sucesso!")
                return result
            except (ValueError, IndexError) as e:
                if line_num <= 3:
                    print(f"   ❌ Erro TSV: {e}")

    # FORMATO 2: Apache Common Log
    # Exemplo: 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /history/apollo/ HTTP/1.0" 200 6245
    pattern = r'^(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "([^"]+)" (\d{3}|-) (\d+|-)$'
    match = re.match(pattern, line)

    if match:
        if line_num <= 3:
            print(f"   ✅ Apache Log parseado!")

        try:
            return {
                "ip": parts[0].strip().strip('"'),
                "login_name": parts[1].strip().strip('"'),
                "time": parts[2].strip().strip('"'),
                "method": parts[3].strip().strip('"'),
                "url": parts[4].strip().strip('"'),
                "response": int(parts[5].strip()),
                "bytes_": int(parts[6].strip()),
            }
        except ValueError as e:
            if line_num <= 3:
                print(f"   ❌ Erro Apache: {e}")

    # FORMATO 3: CSV (separado por vírgula)
    if "," in line and "\t" not in line:
        parts = line.split(",")

        if line_num <= 3:
            print(f"   CSV: {len(parts)} partes")

        if len(parts) >= 5:
            try:
                return {
                    "ip": parts[0].strip().strip('"'),
                    "login_name": parts[1].strip().strip('"'),
                    "time": int(parts[2].strip().strip('"')),
                    "method": parts[3].strip().strip('"'),
                    "url": parts[4].strip().strip('"'),
                    "response": int(parts[5].strip()),
                    "bytes_": int(parts[6].strip()),
                }
            except (ValueError, IndexError) as e:
                if line_num <= 3:
                    print(f"   ❌ Erro CSV: {e}")

    if line_num <= 3:
        print(f"   ❌ Nenhum formato reconhecido")

    return None


def load_logs_to_api(batch_size: int = 1000):
    """
    Lê os arquivos .tsv e carrega no PostgreSQL via API.
    """
    print("🔄 Iniciando carga de dados no PostgreSQL...")

    tsv_files = list(DATA_DIR.glob("*.tsv"))

    if not tsv_files:
        print("❌ Nenhum arquivo .tsv encontrado em data/")
        return False

    print(f"📊 Encontrados {len(tsv_files)} arquivo(s):")
    for file in tsv_files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   - {file.name} ({size_mb:.2f} MB)")

    total_lines = 0
    total_parsed = 0
    total_inserted = 0
    batch = []

    for tsv_file in tsv_files:
        print(f"\n📥 Processando: {tsv_file.name}")

        with open(tsv_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1

                # Parsear linha (com debug nas primeiras 3)
                parsed = parse_tsv_line(line, line_num)

                if parsed:
                    total_parsed += 1
                    batch.append(parsed)

                    # Debug: mostrar quando batch está crescendo
                    if line_num <= 10:
                        print(f"   📦 Batch atual: {len(batch)} itens")

                    # Inserir batch quando atingir o tamanho
                    if len(batch) >= batch_size:
                        print(f"\n   🚀 Inserindo batch de {len(batch)} registros...")
                        success = insert_batch(batch)
                        if success:
                            total_inserted += len(batch)
                            print(f"   ✅ Inseridos {total_inserted:,} registros")
                        else:
                            print(f"   ❌ Falha ao inserir batch")
                        batch = []

                # Mostrar progresso
                if line_num % 10000 == 0:
                    print(
                        f"   📊 Linha {line_num:,} | Parseadas: {total_parsed:,} | Batch: {len(batch)}",
                        end="\r",
                    )

                # Para o debug depois de 100 linhas
                if line_num == 100 and total_parsed == 0:
                    print(
                        f"\n\n⚠️ ATENÇÃO: 100 linhas processadas e NENHUMA foi parseada!"
                    )
                    print(f"   O formato do arquivo não está sendo reconhecido.")
                    print(
                        f"   Execute: docker exec nasa-api head -n 5 /app/data/log_1.tsv"
                    )
                    break

        # Inserir batch restante
        if batch:
            print(f"\n   🚀 Inserindo batch final de {len(batch)} registros...")
            success = insert_batch(batch)
            if success:
                total_inserted += len(batch)
                print(f"   ✅ Inseridos {total_inserted:,} registros")
            batch = []

    print(f"\n{'='*50}")
    print(f"📊 Resumo da Carga:")
    print(f"   Total de linhas: {total_lines:,}")
    print(f"   Linhas parseadas: {total_parsed:,}")
    print(f"   Registros inseridos: {total_inserted:,}")
    print(
        f"   Taxa de sucesso: {(total_parsed/total_lines*100 if total_lines > 0 else 0):.2f}%"
    )
    print(f"{'='*50}")

    return total_inserted > 0


def insert_batch(logs: List[Dict]) -> bool:
    """
    Insere um batch de logs via API.
    """
    try:
        response = requests.post(
            f"{API_URL}/logs/ingest", json={"logs": logs}, timeout=30
        )

        if response.status_code == 200:
            return True
        else:
            print(f"\n   ❌ API retornou status {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"\n   ❌ Erro ao inserir batch: {str(e)}")
        return False


if __name__ == "__main__":
    success = load_logs_to_api()
    if success:
        print("\n✅ Carga concluída com sucesso!")
    else:
        print("\n⚠️ Falha na carga de dados")
