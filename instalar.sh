#!/bin/bash
# =====================================================================
# instalar.sh - CitaLocal
# ---------------------------------------------------------------------
# Instalador automático para Linux/Ubuntu.
# Prepara todo lo necesario para ejecutar CitaLocal:
#   1) Verifica Python
#   2) Crea el entorno virtual
#   3) Instala las dependencias de Python
#   4) Verifica si Ollama está instalado (y ofrece instalarlo)
#   5) Descarga un modelo de IA recomendado si no hay ninguno
# =====================================================================

set -e  # detener el script si algo falla

echo "======================================"
echo "   Instalador de CitaLocal"
echo "======================================"
echo ""

# --- 1) Verificar Python ---
if ! command -v python3 &> /dev/null; then
    echo "❌ No se encontró Python 3. Instálalo con:"
    echo "   sudo apt install python3 python3-venv python3-pip -y"
    exit 1
fi
echo "✅ Python encontrado: $(python3 --version)"

# --- 2) Verificar/instalar python3-venv ---
if ! python3 -c "import venv" &> /dev/null; then
    echo "Instalando python3-venv (requiere tu contraseña)..."
    sudo apt update
    sudo apt install python3-venv -y
fi

# --- 3) Crear entorno virtual ---
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
else
    echo "✅ El entorno virtual ya existe."
fi

# --- 4) Instalar dependencias ---
echo "Instalando dependencias de Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo "✅ Dependencias instaladas."

# --- 5) Verificar Ollama ---
echo ""
if command -v ollama &> /dev/null; then
    echo "✅ Ollama ya está instalado."
else
    echo "⚠️  Ollama no está instalado."
    read -p "¿Deseas instalarlo ahora? (s/n): " respuesta
    if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "Puedes instalarlo más tarde con:"
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
    fi
fi

# --- 6) Verificar/descargar modelo de IA ---
echo ""
if command -v ollama &> /dev/null; then
    MODELOS=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$MODELOS" -eq 0 ]; then
        echo "No se detectaron modelos de IA instalados."
        read -p "¿Descargar el modelo recomendado 'phi3:mini' (~2.3GB)? (s/n): " resp2
        if [ "$resp2" = "s" ] || [ "$resp2" = "S" ]; then
            ollama pull phi3:mini
        fi
    else
        echo "✅ Ya tienes al menos un modelo de IA instalado."
    fi
fi

# --- 7) Crear acceso directo de escritorio ---
chmod +x iniciar.sh
DESKTOP_FILE="$HOME/Desktop/CitaLocal.desktop"
if [ -d "$HOME/Desktop" ]; then
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CitaLocal
Comment=Buscador y sintetizador local de literatura científica
Exec=bash -c "cd $(pwd) && ./iniciar.sh"
Icon=$(pwd)/assets/icon.png
Terminal=true
Categories=Science;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "✅ Acceso directo creado en el Escritorio."
fi

# --- 8) Descargar modelos recomendados ---
echo ""
if command -v ollama &> /dev/null; then
    echo "Verificando modelos recomendados para CitaLocal..."

    if ollama list | grep -q "llama3.2:3b"; then
        echo "✅ llama3.2:3b ya está instalado."
    else
        read -p "¿Descargar modelo rápido 'llama3.2:3b' (~2GB)? (s/n): " resp3
        if [ "$resp3" = "s" ] || [ "$resp3" = "S" ]; then
            ollama pull llama3.2:3b
        fi
    fi

    if ollama list | grep -q "llama3.1:8b"; then
        echo "✅ llama3.1:8b ya está instalado."
    else
        read -p "¿Descargar modelo de calidad 'llama3.1:8b' (~4.9GB)? (s/n): " resp4
        if [ "$resp4" = "s" ] || [ "$resp4" = "S" ]; then
            ollama pull llama3.1:8b
        fi
    fi

    # --- 9) Crear modelo citalocal-quality ---
    if ollama list | grep -q "citalocal-quality"; then
        echo "✅ El modelo citalocal-quality ya existe."
    else
        echo "Creando modelo citalocal-quality (optimizado para síntesis IMRAD)..."
        ollama create citalocal-quality -f ./Modelfile
        echo "✅ Modelo citalocal-quality creado."
    fi
fi

# --- 10) Crear acceso directo de escritorio ---
chmod +x iniciar.sh
DESKTOP_FILE="$HOME/Desktop/CitaLocal.desktop"
if [ -d "$HOME/Desktop" ]; then
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CitaLocal
Comment=Buscador y sintetizador local de literatura científica
Exec=bash -c "cd $(pwd) && ./iniciar.sh"
Icon=$(pwd)/assets/icon.png
Terminal=true
Categories=Science;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "✅ Acceso directo creado en el Escritorio."
fi

echo ""
echo "======================================"
echo "   ✅ Instalación completada"
echo "======================================"
echo ""
echo "Para iniciar CitaLocal, ejecuta:"
echo "   ./iniciar.sh"
echo "o haz doble clic en el ícono creado en tu Escritorio."