# 📱 BUILD ANDROID - CAIXA MESTRE MOBILE

## 🚀 Guia Completo para Gerar APK

---

## 📋 Requisitos

### Sistema
- **Ubuntu 20.04+** (ou WSL2 no Windows)
- **20GB+** de espaço em disco
- **8GB+** de RAM
- Conexão com internet

### Ferramentas
```bash
# Python e dependências
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git zip unzip openjdk-17-jdk

# Dependências de build
sudo apt install -y autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

---

## 🔧 Instalação do Buildozer

```bash
# Criar ambiente virtual
python3 -m venv ~/buildozer_env
source ~/buildozer_env/bin/activate

# Instalar buildozer
pip install buildozer cython

# Verificar instalação
buildozer --version
```

---

## 📁 Estrutura do Projeto

```
mobile/
├── main_complete.py          # Entry point
├── database_manager.py         # Banco SQLite
├── sync_manager.py            # Sincronização P2P
├── buildozer.spec             # Configuração build
├── buildozer.spec.example     # Exemplo completo
├── screens/                   # Telas do app
│   ├── __init__.py
│   ├── login_screen.py
│   ├── dashboard_screen.py
│   ├── materiais_screen.py
│   ├── movimentacao_screen.py
│   ├── busca_screen.py
│   └── detalhe_material_screen.py
└── BUILD_ANDROID.md           # Este arquivo
```

---

## ⚙️ Configurar buildozer.spec

O arquivo `buildozer.spec` já está configurado. Verifique:

```ini
[app]
name = Caixa Mestre Mobile
package.name = caixamestremobile
package.domain = com.caixamestre

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db,ttf,md

version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd,pillow,sqlite3,flask,requests,zeroconf

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

android.archs = arm64-v8a, armeabi-v7a
```

---

## 🏗️ Gerar APK Debug

### Passo 1: Navegar até pasta mobile
```bash
cd /caminho/para/sistema_almoxarifado/mobile
```

### Passo 2: Inicializar buildozer (primeira vez)
```bash
# Se não tiver buildozer.spec
buildozer init

# Editar buildozer.spec conforme configuração acima
```

### Passo 3: Build
```bash
# Build debug (mais rápido)
buildozer -v android debug

# OU build release (para distribuição)
buildozer -v android release
```

⏱️ **Tempo estimado:** 15-30 minutos (primeira vez)
10-15 minutos (builds subsequentes)

---

## 📥 Instalar no Celular

### Via ADB (Android Debug Bridge)
```bash
# Conectar celular via USB (modo desenvolvedor ativado)
adb devices

# Instalar APK
adb install bin/caixamestremobile-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Via transferência de arquivo
1. Copie o APK para o celular (USB, Bluetooth, Drive, etc.)
2. No celular, habilite: **Configurações > Segurança > Fontes desconhecidas**
3. Abra o arquivo APK e instale

---

## 🐛 Solução de Problemas

### Erro: "Command failed: gradlew"
```bash
# Limpar cache
buildozer android clean
rm -rf .buildozer/

# Tentar novamente
buildozer -v android debug
```

### Erro: "No module named 'kivy'"
```bash
# Verificar requirements.txt ou buildozer.spec
pip list | grep kivy

# Adicionar explicitamente no spec:
# requirements = python3,kivy==2.2.1,...
```

### Erro: Out of memory
```bash
# Build apenas para uma arquitetura (economiza memória)
# Editar buildozer.spec:
android.archs = arm64-v8a
```

### App trava ao abrir
```bash
# Ver logs do Android
adb logcat | grep python

# Ou com buildozer
buildozer android logcat
```

### Sincronização não funciona
Verifique no logcat:
- Porta 5007 (UDP multicast) está liberada?
- Porta 5008 (TCP HTTP) está liberada?
- Dispositivos estão na mesma rede WiFi?

---

## 📊 Comandos Úteis

```bash
# Limpar tudo
buildozer distclean

# Build apenas para debug rápido
buildozer android debug deploy run

# Ver logs em tempo real
buildozer android logcat | grep -i "caixa\|sync\|error"

# Reinstalar app
adb uninstall com.caixamestre.caixamestremobile
adb install bin/*.apk

# Ver dispositivos conectados
adb devices
```

---

## 🔒 Preparação para Release

### 1. Gerar keystore
```bash
keytool -genkey -v -keystore caixamestre.keystore -alias caixamestre \
    -keyalg RSA -keysize 2048 -validity 10000
```

### 2. Configurar no buildozer.spec
```ini
android.release_artifact = apk
android.sign = True
android.keystore = caixamestre.keystore
android.keystore_alias = caixamestre
```

### 3. Build release
```bash
buildozer android release
```

---

## 📱 Testes Recomendados

### Antes de distribuir:
- [ ] App abre sem crash
- [ ] Login funciona (PIN: 1234)
- [ ] Dashboard mostra estatísticas
- [ ] Adicionar material funciona
- [ ] Registrar entrada/saída funciona
- [ ] Busca funciona
- [ ] **Sincronização entre 2 dispositivos funciona**
- [ ] App funciona offline
- [ ] Botão voltar do Android funciona
- [ ] Rotação de tela não quebra layout

---

## 🚀 Distribuição

### Opções:
1. **Google Play Store** (requer conta de desenvolvedor)
2. **APK direto** (enviar arquivo)
3. **Internal Testing** (Firebase App Distribution)

### APK Gerado:
```
bin/caixamestremobile-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique logs: `adb logcat | grep python`
2. Limpe e reconstrua: `buildozer distclean && buildozer android debug`
3. Verifique versões compatíveis de dependências

---

**Data:** Abril 2026  
**Versão App:** 1.0.0  
**Versão Buildozer:** 1.5.0+
