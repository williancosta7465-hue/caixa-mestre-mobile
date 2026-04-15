# 📱 Como Gerar o APK Android

## Opção 1: Automática (Recomendada)

### Passo 1: Execute o script automatizado
1. Localize o arquivo: `GERAR_APK.bat`
2. Clique com **botão direito** → **"Executar como Administrador"**
3. Siga as instruções na tela
4. O computador irá **reiniciar automaticamente**

### Passo 2: Após o reinício
1. Aguarde o Ubuntu instalar (pode demorar alguns minutos)
2. Quando abrir o Ubuntu pela primeira vez, defina:
   - Nome de usuário: `caixamestre` (ou qualquer um)
   - Senha: (escolha uma senha fácil de lembrar)
3. No terminal Ubuntu, execute:
   ```bash
   bash /mnt/c/Users/PLANEJAMENTO/continuar_build.sh
   ```

### Passo 3: Aguarde o build
- **Primeira vez:** 30-40 minutos
- **Builds seguintes:** 10-15 minutos
- O APK será gerado em: `mobile/bin/caixamestremobile-*.apk`

---

## Opção 2: Manual (Se a automática falhar)

### 1. Instalar WSL + Ubuntu
Abra **PowerShell como Administrador**:
```powershell
wsl --install --distribution Ubuntu
```

### 2. Reiniciar o computador
```powershell
Restart-Computer
```

### 3. Configurar Ubuntu
Após reiniciar, abra **Ubuntu** (menu Iniciar):
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv git zip unzip \
    openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev
```

### 4. Instalar Buildozer
```bash
# Criar ambiente virtual
python3 -m venv ~/buildozer_env
source ~/buildozer_env/bin/activate

# Instalar buildozer
pip install buildozer cython
```

### 5. Build do APK
```bash
# Navegar para pasta do projeto
cd /mnt/c/Users/PLANEJAMENTO/Desktop/DOWN/sistema_almoxarifado/mobile

# Build
buildozer -v android debug
```

---

## Opção 3: Usar Serviço Online (Buildozer Cloud)

Se não conseguir instalar localmente:

### Usando GitHub Actions (Gratuito)
1. Crie um repositório no GitHub
2. Envie os arquivos do `mobile/`
3. Configure GitHub Actions para build automático
4. Baixe o APK gerado

### Usando Docker
Se tiver Docker Desktop:
```bash
docker run -it --rm \
  -v "$(pwd):/home/user/hostcwd" \
  kivy/buildozer \
  buildozer android debug
```

---

## 📋 Checklist Pré-Build

Antes de começar, verifique:
- [ ] 20GB+ de espaço livre em disco
- [ ] 8GB+ de RAM disponível
- [ ] Conexão com internet estável
- [ ] Windows 10/11 atualizado
- [ ] Privilégios de Administrador

---

## 🐛 Solução de Problemas

### "WSL não está instalado"
Execute no PowerShell como Admin:
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
```

### "Falta de espaço em disco"
Libere espaço ou use:
```bash
# Build apenas para uma arquitetura (economiza espaço)
# Edite buildozer.spec:
android.archs = arm64-v8a
```

### "Build falhou com erro de memória"
Feche outros programas ou use:
```bash
# Limpar cache
buildozer android clean
rm -rf ~/.buildozer/
```

### "App trava no celular"
Verifique no logcat:
```bash
adb logcat | grep python
```

---

## ✅ Após Gerar o APK

### Instalar no celular:
1. Copie o APK para o celular (USB, Drive, Bluetooth)
2. No celular, vá em **Configurações > Segurança**
3. Habilite **"Fontes desconhecidas"**
4. Abra o arquivo APK e toque em **Instalar**

### Testar:
- [ ] App abre sem crash
- [ ] Login funciona (PIN: 1234)
- [ ] Dashboard carrega
- [ ] Adicionar material funciona
- [ ] Sincronização entre 2 celulares funciona

---

## 📞 Precisa de Ajuda?

Se encontrar problemas:
1. Verifique `BUILD_ANDROID.md` para detalhes completos
2. Verifique os logs de erro no terminal
3. Certifique-se de ter reiniciado após instalar WSL

---

**Tempo total estimado:** 45-60 minutos (incluindo downloads e instalações)
