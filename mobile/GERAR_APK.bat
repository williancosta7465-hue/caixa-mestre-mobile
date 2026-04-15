@echo off
echo ==========================================
echo CAIXA MESTRE MOBILE - Gerador de APK
echo ==========================================
echo.
echo Este script ira:
echo 1. Instalar WSL (Windows Subsystem for Linux)
echo 2. Instalar Ubuntu
echo 3. Configurar ambiente de build
echo 4. Gerar APK Android
echo.
echo IMPORTANTE:
echo - Execute como Administrador
echo - Pode levar 30-40 minutos total
echo - Requer reinicio do computador
echo.
pause

:: Verificar se é administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERRO: Execute como Administrador!
    echo Clique direito neste arquivo -^> "Executar como Administrador"
    pause
    exit /b 1
)

echo.
echo [1/4] Instalando WSL...
wsl --install --distribution Ubuntu --no-launch

echo.
echo [2/4] Criando script de continuacao...
(
echo #!/bin/bash
echo # Script de build para Ubuntu/WSL
echo.
echo clear
echo echo "=========================================="
echo echo "CAIXA MESTRE MOBILE - Build APK"
echo echo "=========================================="
echo echo ""
echo echo "[1/5] Atualizando sistema..."
echo sudo apt update ^&^& sudo apt upgrade -y
echo.
echo echo "[2/5] Instalando dependencias..."
echo sudo apt install -y python3 python3-pip python3-venv git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
echo.
echo echo "[3/5] Configurando ambiente Python..."
echo python3 -m venv ~/buildozer_env
echo source ~/buildozer_env/bin/activate
echo pip install --upgrade pip
echo pip install buildozer cython
echo.
echo echo "[4/5] Preparando projeto..."
echo cd /mnt/c/Users/PLANEJAMENTO/Desktop/DOWN/sistema_almoxarifado/mobile
echo.
echo echo "[5/5] Iniciando build do APK..."
echo echo "Isso pode levar 20-30 minutos na primeira vez!"
echo echo ""
echo buildozer -v android debug
echo.
echo echo "=========================================="
echo echo "BUILD FINALIZADO!"
echo echo "=========================================="
echo echo "APK gerado em: bin/caixamestremobile-*.apk"
echo echo ""
echo "Para instalar no celular:"
echo "1. Copie o APK para o celular"
echo "2. No celular, habilite 'Fontes desconhecidas'"
echo "3. Abra o APK e instale"
echo echo "=========================================="
echo read -p "Pressione ENTER para sair..."
) > "%USERPROFILE%\continuar_build.sh"

echo.
echo ==========================================
echo WSL instalado!
echo ==========================================
echo.
echo PROXIMOS PASSOS:
echo.
echo 1. REINICIE O COMPUTADOR agora
echo.
echo 2. Apos reiniciar:
echo    - Aguarde Ubuntu instalar (aparece no menu Iniciar)
echo    - Defina usuario e senha do Ubuntu
echo    - Execute no terminal Ubuntu:
echo.
echo      bash /mnt/c/Users/PLANEJAMENTO/continuar_build.sh
echo.
echo ==========================================
echo.
echo Deseja reiniciar agora? (S/N)
set /p resposta=
if /i "%resposta%"=="S" (
    echo Reiniciando em 5 segundos...
    timeout /t 5 /nobreak >nul
    shutdown /r /t 0
) else (
    echo.
    echo Reinicio adiado.
    echo Execute este script novamente apos reiniciar.
    pause
)
