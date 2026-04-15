# 📱 Caixa Mestre Mobile - Build com GitHub Actions

## 🚀 Como Gerar seu APK (Mais Fácil)

### 1. Preparar Arquivos (LOCAL)

Execute no terminal do VS Code:

```bash
cd "c:\Users\PLANEJAMENTO\Desktop\DOWN\sistema_almoxarifado\mobile"

# Inicializar git
git init

# Adicionar todos os arquivos
git add .

# Primeiro commit
git commit -m "Versao inicial do app mobile"
```

---

### 2. Criar Repositório no GitHub (NAVEGADOR)

1. Acesse https://github.com
2. Crie conta ou faça login
3. Clique **"New"** (botão verde)
4. Nome: `caixa-mestre-mobile`
5. Selecione **"Public"**
6. Clique **"Create repository"**

---

### 3. Conectar e Enviar Código (LOCAL)

```bash
# Adicionar remote do GitHub
# Substitua SEU-USUARIO pelo seu nome de usuário do GitHub
git remote add origin https://github.com/SEU-USUARIO/caixa-mestre-mobile.git

# Enviar código
git branch -M main
git push -u origin main
```

---

### 4. Configurar GitHub Actions (NAVEGADOR)

1. No seu repositório GitHub, clique em **"Actions"**
2. Clique **"New workflow"**
3. Clique **"set up a workflow yourself"**
4. **APAGUE TUDO** e cole o código abaixo:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y python3-pip build-essential git \
          zip unzip openjdk-17-jdk autoconf libtool pkg-config \
          zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
          cmake libffi-dev libssl-dev
        pip3 install Cython buildozer
    
    - name: Build APK
      run: |
        cd mobile
        buildozer android debug
    
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: caixa-mestre-apk
        path: mobile/bin/*.apk
```

5. Clique **"Start commit"** → **"Commit new file"**

---

### 5. Iniciar Build (AUTOMÁTICO)

Assim que você fizer o commit do workflow, o build inicia automaticamente.

Para acompanhar:
1. Vá na aba **"Actions"**
2. Clique no workflow em execução
3. Aguarde ~10-15 minutos (círculo amarelo → check verde)

---

### 6. Baixar seu APK 🎉

1. Quando aparecer ✅ verde, clique no workflow
2. Role até **"Artifacts"**
3. Clique em **"caixa-mestre-apk"**
4. O APK será baixado como ZIP
5. Extraia o ZIP → Instale no celular!

---

## 🎯 Resumo em 3 Passos

```
1. git init → git add . → git commit → git push
2. Criar workflow no GitHub (copiar YAML acima)
3. Aguardar build → Baixar APK → Instalar no celular
```

---

## 📦 APK Gerado

O APK terá nome similar a:
```
caixamestremobile-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## 🐛 Se der erro no build

Verifique:
- ✅ Todos os arquivos foram commitados?
- ✅ O arquivo `buildozer.spec` existe na pasta mobile/?
- ✅ O workflow está na pasta `.github/workflows/`?

---

## 💡 Próximos Builds

Depois do primeiro, cada vez que você fizer:
```bash
git add .
git commit -m "Nova versao"
git push
```

Um novo APK será gerado automaticamente!

---

**Precisa de ajuda?** Me mande o erro que aparece no GitHub Actions.
