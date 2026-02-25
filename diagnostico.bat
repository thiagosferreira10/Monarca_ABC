@echo off
title Diagnostico - Monarca ABC
echo ============================================
echo  DIAGNOSTICO - Monarca Curva ABC
echo ============================================
echo.

echo [1] Pasta atual:
cd
echo.

echo [2] Python:
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH!
    echo Instale Python 3.14 e marque "Add to PATH"
    goto :fim
)

echo.
echo [3] Streamlit:
python -m streamlit --version
if errorlevel 1 (
    echo ERRO: Streamlit nao instalado!
    echo Execute instalar.bat primeiro!
    goto :fim
)

echo.
echo [4] Arquivos necessarios:
if exist "HOME.py" (echo OK: HOME.py) else (echo FALTA: HOME.py)
if exist "src_loader.py" (echo OK: src_loader.py) else (echo FALTA: src_loader.py)
if exist "config.ini" (echo OK: config.ini) else (echo FALTA: config.ini)
if exist "src\__init__.py" (echo OK: src\__init__.py) else (echo FALTA: src\__init__.py)
if exist "src\__pycache__" (echo OK: src\__pycache__) else (echo FALTA: src\__pycache__)

echo.
echo [5] Config.ini:
type config.ini

echo.
echo [6] Logs de erro (se existirem):
if exist "launcher_log.txt" (
    echo --- launcher_log.txt ---
    type launcher_log.txt
) else (
    echo launcher_log.txt: nao existe ainda
)
echo.
if exist "streamlit_err.txt" (
    echo --- streamlit_err.txt ---
    type streamlit_err.txt
) else (
    echo streamlit_err.txt: nao existe ainda
)

echo.
echo [7] Teste de import (arquivo externo):
python diagnostico_test.py

echo.
echo [8] Iniciando Streamlit ao vivo (feche esta janela para parar):
python -m streamlit run HOME.py --global.developmentMode=false

:fim
echo.
echo ============================================
pause
