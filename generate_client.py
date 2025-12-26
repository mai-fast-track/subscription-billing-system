# generate_client.py
import json
import subprocess
from pathlib import Path

from app.main import app  # должен быть объект FastAPI с именем app

ROOT = Path(__file__).parent
SCHEMA_PATH = ROOT / "openapi.json"
CLIENT_PACKAGE_NAME = "billing_core_client"


def generate_openapi_schema() -> None:
    schema = app.openapi()
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"openapi.json сгенерирован: {SCHEMA_PATH}")


def generate_client() -> None:
    client_dir = ROOT / CLIENT_PACKAGE_NAME
    if client_dir.exists():
        print(f"Удалили старый {client_dir}")
        subprocess.run(["rm", "-rf", str(client_dir)], check=True)

    cmd = [
        "openapi-python-client",
        "generate",
        "--path",
        str(SCHEMA_PATH),
        "--output-path",
        str(ROOT),  # Вывод в корень проекта
        "--meta=poetry",
        "--overwrite",  # Перезапись, если папка существует
    ]
    print("Запуск:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"✅ Клиент сгенерирован в {client_dir}")


if __name__ == "__main__":
    generate_openapi_schema()
    generate_client()
