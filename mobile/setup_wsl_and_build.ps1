# Script PowerShell para instalar WSL, Ubuntu e gerar APK Android
# Execute como Administrador

Write-Host "==========================================" -ForegroundColor Green
Write-Host "CAIXA MESTRE MOBILE - Setup de Build" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Verificar se é administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERRO: Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "Clique direito no arquivo -> 'Executar como Administrador'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Etapa 1/5: Instalando WSL..." -ForegroundColor Yellow
wsl --install --distribution Ubuntu --no-launch

Write-Host ""
Write-Host "Etapa 2/5: Reiniciando computador necessario..." -ForegroundColor Yellow
Write-Host "APOS O REINICIO, execute este script novamente!" -ForegroundColor Cyan
Write-Host ""

# Criar script de continuação
$continueScript = @'
#!/bin/bash
# Script de continuação para Ubuntu/WSL

echo "=========================================="
echo "CAIXA MESTRE MOBILE - Build Environment"
echo "=========================================="
echo ""

# Atualizar sistema
echo "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências
echo "Instalando dependencias..."
sudo apt install -y python3 python3-pip python3-venv git zip unzip \
    openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev

# Criar ambiente virtual
echo "Criando ambiente Python..."
python3 -m venv ~/buildozer_env
source ~/buildozer_env/bin/activate

# Instalar buildozer
echo "Instalando Buildozer..."
pip install buildozer cython

# Navegar para pasta do projeto
cd /mnt/c/Users/PLANEJAMENTO/Desktop/DOWN/sistema_almoxarifado/mobile

# Inicializar buildozer se necessario
if [ ! -f buildozer.spec ]; then
    echo "Inicializando buildozer..."
    buildozer init
fi

# Build do APK
echo ""
echo "=========================================="
echo "Iniciando build do APK..."
echo "Isso pode levar 20-30 minutos na primeira vez!"
echo "=========================================="
echo ""

buildozer -v android debug

echo ""
echo "=========================================="
echo "Build finalizado!"
echo "APK localizado em: bin/"
echo "=========================================="
'@

# Salvar script de continuação
$wslScriptPath = "$env:USERPROFILE\continue_build.sh"
$continueScript | Out-File -FilePath $wslScriptPath -Encoding UTF8

Write-Host "Script de continuacao criado: $wslScriptPath" -ForegroundColor Green
Write-Host ""
Write-Host "PROXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Reinicie o computador" -ForegroundColor White
Write-Host "2. Após reiniciar, abra Ubuntu (estara no menu Iniciar)" -ForegroundColor White
Write-Host "3. No Ubuntu, execute:" -ForegroundColor White
Write-Host "   bash /mnt/c/Users/PLANEJAMENTO/continue_build.sh" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ou execute este script novamente como Administrador apos o reinicio." -ForegroundColor Gray

Read-Host "Pressione ENTER para reiniciar..."
Restart-Computer
