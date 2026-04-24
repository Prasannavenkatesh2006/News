$env:API_PORT = "8001"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "3006"
$env:POSTGRES_DB = "anip"
$env:OPENAI_API_KEY = "sk-dummy-key-for-initialization-only"
$env:PYTHONPATH = "C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/src;C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/services/api"

cd C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/services/api
uvicorn app.main:app --host 127.0.0.1 --port 8001
