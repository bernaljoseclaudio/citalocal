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

REM --- 5) Descargar modelos recomendados ---
where ollama >nul 2>&1
if not errorlevel 1 (
    echo.
    echo Verificando modelos recomendados para CitaLocal...

    ollama list | findstr "llama3.2:3b" >nul 2>&1
    if errorlevel 1 (
        set /p resp3="¿Descargar modelo rapido 'llama3.2:3b' (~2GB)? (s/n): "
        if /i "%resp3%"=="s" ollama pull llama3.2:3b
    ) else (
        echo llama3.2:3b ya esta instalado.
    )

    ollama list | findstr "llama3.1:8b" >nul 2>&1
    if errorlevel 1 (
        set /p resp4="¿Descargar modelo de calidad 'llama3.1:8b' (~4.9GB)? (s/n): "
        if /i "%resp4%"=="s" ollama pull llama3.1:8b
    ) else (
        echo llama3.1:8b ya esta instalado.
    )

    REM --- 6) Crear modelo citalocal-quality ---
    ollama list | findstr "citalocal-quality" >nul 2>&1
    if errorlevel 1 (
        echo Creando modelo citalocal-quality...
        ollama create citalocal-quality -f Modelfile
        echo Modelo citalocal-quality creado.
    ) else (
        echo El modelo citalocal-quality ya existe.
    )
)

echo.
echo ======================================
echo    Instalacion completada
echo ======================================
echo.
echo Para iniciar CitaLocal, haz doble clic en: iniciar.bat
echo.
pause