@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente Python.
        pause
        exit /b 1
    )
    call ".venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    if errorlevel 1 goto :install_error
    pip install -r requirements.txt
    if errorlevel 1 goto :install_error
) else (
    call ".venv\Scripts\activate.bat"
)

python -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo O aplicativo foi encerrado com erro.
    pause
)
goto :end

:install_error
echo.
echo Nao foi possivel instalar as dependencias. Verifique sua conexao com a internet e tente novamente.
pause
exit /b 1

:end
endlocal
