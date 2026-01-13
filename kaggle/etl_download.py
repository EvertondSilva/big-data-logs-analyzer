import os
import kagglehub
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretório para armazenar dados
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def download_nasa_logs():
    """
    Baixa o dataset NASA Access Logs usando kagglehub.
    """
    print("🔄 Iniciando download do dataset NASA Access Logs...")

    # Obter credenciais do .env
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")

    if not kaggle_username or not kaggle_key:
        print("❌ Erro: KAGGLE_USERNAME ou KAGGLE_KEY não configurados no .env")
        return False

    try:

        print("📥 Baixando dataset via kagglehub...")

        # Download do dataset
        path = kagglehub.dataset_download("souhagaa/nasa-access-log-dataset")
        print(path)
        print(f"✅ Download concluído!")
        print(f"📁 Caminho: {path}")

        # Copiar arquivos .txt para o diretório data
        source_path = Path(path)
        txt_files = list(source_path.glob("*.tsv"))

        if not txt_files:
            print("⚠️ Nenhum arquivo .tsv encontrado no dataset")
            return False

        print(f"📊 Copiando {len(txt_files)} arquivo(s)...")

        for txt_file in txt_files:
            dest_file = DATA_DIR / txt_file.name
            # Copiar arquivo
            import shutil

            shutil.copy2(txt_file, dest_file)
            size_mb = dest_file.stat().st_size / (1024 * 1024)
            print(f"   ✅ {txt_file.name} ({size_mb:.2f} MB)")

        print(f"\n✅ Dataset pronto em: {DATA_DIR}")
        return True

    except ImportError:
        print("❌ Erro: kagglehub não está instalado.")
        print("   Execute: pip install kagglehub")
        return False
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


if __name__ == "__main__":
    success = download_nasa_logs()
    if success:
        print("\n✅ Dataset pronto para processamento!")
    else:
        print("\n⚠️ Falha no download, mas continuando...")
