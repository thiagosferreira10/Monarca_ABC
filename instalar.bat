@echo off
title Instalador - Monarca Ferramentas
color 0A

echo ============================================
echo   INSTALADOR - Monarca Ferramentas
echo   TAG Tecnologia
echo ============================================
echo.

:: -----------------------------------------------
:: 1. Verificar Python
:: -----------------------------------------------
echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo  ERRO: Python nao encontrado!
    echo.
    echo  Instale o Python 3.14 antes de continuar:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: Marque a opcao "Add Python to PATH"
    echo  durante a instalacao!
    echo.
    goto :fim
)

for /f "tokens=*" %%i in ('python --version') do echo   Encontrado: %%i
echo.

:: -----------------------------------------------
:: 2. Instalar dependencias
:: -----------------------------------------------
echo [2/3] Instalando dependencias...
echo   Isso pode levar alguns minutos na primeira vez.
echo.

pip install -r requirements.txt --quiet
if errorlevel 1 (
    color 0E
    echo.
    echo  AVISO: Alguns pacotes podem nao ter sido instalados.
    echo  Tente executar manualmente:
    echo    pip install -r requirements.txt
    echo.
) else (
    echo   Dependencias instaladas com sucesso!
)
echo.

:: -----------------------------------------------
:: 3. Verificar instalacao
:: -----------------------------------------------
echo [3/3] Verificando instalacao...

python -c "import streamlit; print('   Streamlit:', streamlit.__version__)" 2>nul || echo   FALTA: streamlit
python -c "import pandas; print('   Pandas:', pandas.__version__)" 2>nul || echo   FALTA: pandas
python -c "import firebird.driver; print('   Firebird: OK')" 2>nul || echo   FALTA: firebird-driver
python -c "import xlsxwriter; print('   XlsxWriter:', xlsxwriter.__version__)" 2>nul || echo   FALTA: xlsxwriter
python -c "import dotenv; print('   DotEnv: OK')" 2>nul || echo   FALTA: python-dotenv

echo.
echo ============================================
echo   INSTALACAO CONCLUIDA!
echo.
echo   Para iniciar o sistema:
echo   Clique duplo em Ferramentas.exe
echo ============================================
echo.

:fim
pause
