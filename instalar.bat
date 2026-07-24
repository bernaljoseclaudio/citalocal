@echo off
REM =====================================================================
REM instalar.bat - CitaLocal
REM ---------------------------------------------------------------------
REM Instalador automático para Windows.
REM =====================================================================

echo ======================================
echo    Instalador de CitaLocal
echo ======================================
echo.

REM --- 1) Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python. Descargalo desde:
    echo https://www.python.org/downloads/
    echo IMPORTANTE: marca la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo Python encontrado.

REM --- 2) Crear entorno virtual ---
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
) else (
    echo El entorno virtual ya existe.
)

REM --- 3) Instalar dependencias ---
echo Instalando dependencias de Python...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
call venv\Scripts\deactivate.bat
echo Dependencias instaladas.

REM --- 4) Verificar Ollama ---
where ollama >nul 2>&1
if errorlevel 1 (
    echo.
    echo Ollama no esta instalado.
    echo Descargalo desde: https://ollama.com/download
    echo Instalalo y luego vuelve a ejecutar este script.
    pause
) else (
    echo Ollama ya esta instalado.
)

echo.
echo ======================================
echo    Instalacion completada
echo ======================================
echo.
echo Para iniciar CitaLocal, haz doble clic en: iniciar.bat
echo.
pause