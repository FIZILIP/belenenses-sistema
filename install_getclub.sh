#!/bin/bash
echo "⚽ GET CLUB - Instalador"
echo "========================"
echo ""

# Verificar se Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "📦 Python 3 não encontrado. A instalar..."
    # Instalar Xcode Command Line Tools (inclui Python)
    xcode-select --install 2>/dev/null
    echo "⚠️ Por favor, instale o Python 3 manualmente e execute este instalador novamente."
    echo "   https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Criar pasta da aplicação
APP_DIR="/Applications/GETCLUB.app/Contents/Resources"
sudo mkdir -p "$APP_DIR"

# Copiar ficheiros do projeto
echo "📁 A copiar ficheiros..."
sudo cp -R "$(dirname "$0")/templates" "$APP_DIR/"
sudo cp -R "$(dirname "$0")/static" "$APP_DIR/"
sudo cp "$(dirname "$0")/app.py" "$APP_DIR/"
sudo cp "$(dirname "$0")/models.py" "$APP_DIR/"
sudo cp "$(dirname "$0")/requirements.txt" "$APP_DIR/"

# Criar ambiente virtual e instalar dependências
echo "📥 A instalar dependências..."
cd "$APP_DIR"
sudo python3 -m venv venv
source venv/bin/activate
sudo pip3 install -r requirements.txt --quiet

# Criar executável do app
sudo mkdir -p /Applications/GETCLUB.app/Contents/MacOS
sudo tee /Applications/GETCLUB.app/Contents/MacOS/GETCLUB > /dev/null << 'APPEOF'
#!/bin/bash
DIR="/Applications/GETCLUB.app/Contents/Resources"
cd "$DIR"
source venv/bin/activate
python3 app.py &
sleep 3
open http://127.0.0.1:5002
APPEOF
sudo chmod +x /Applications/GETCLUB.app/Contents/MacOS/GETCLUB

# Criar Info.plist
sudo tee /Applications/GETCLUB.app/Contents/Info.plist > /dev/null << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>GETCLUB</string>
<key>CFBundleIdentifier</key><string>com.getclub.gestao</string>
<key>CFBundleName</key><string>GET CLUB</string>
<key>CFBundleDisplayName</key><string>GET CLUB</string>
<key>LSMinimumSystemVersion</key><string>10.13</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLISTEOF

# Copiar ícone se existir
if [ -f "$(dirname "$0")/MyIcon.icns" ]; then
    sudo cp "$(dirname "$0")/MyIcon.icns" /Applications/GETCLUB.app/Contents/Resources/icon.icns
fi

# Atualizar Launchpad
killall Dock 2>/dev/null

echo ""
echo "✅ GET CLUB instalado com sucesso!"
echo "📱 Encontre na pasta Aplicações ou Launchpad"
echo ""
