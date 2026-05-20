#!/bin/bash
cd "$(dirname "$0")"

echo "⚽ A instalar o Sistema Belenenses..."
echo ""

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 A criar ambiente virtual..."
    python3 -m venv venv
fi

# Ativar e instalar dependências
source venv/bin/activate
echo "📥 A instalar dependências..."
pip3 install -r requirements.txt --quiet

# Iniciar o sistema
echo "🚀 A iniciar o sistema..."
python3 app.py &
sleep 2
open http://127.0.0.1:5002
