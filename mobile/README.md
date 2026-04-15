# 📱 CAIXA MESTRE MOBILE

Aplicativo Android para gestão de almoxarifado com sincronização P2P (peer-to-peer).

## ✨ Recursos

- 📦 **Cadastro de materiais** com código, nome, quantidade, localização
- ➕ **Entrada e saída** de estoque com registro de movimentações
- 🔍 **Busca rápida** de itens
- 🔄 **Sincronização automática** entre dispositivos na mesma rede WiFi
- 📊 **Dashboard** com estatísticas em tempo real
- 🔒 **Acesso por PIN** (offline, sem necessidade de servidor)
- 🌐 **Até 5 dispositivos** sincronizados simultaneamente

---

## 🏗️ Arquitetura

### Sincronização P2P

```
Dispositivo A (Celular 1)          Dispositivo B (Celular 2)
        │                                   │
        │    WiFi (mesma rede)             │
        │◄────────────────────────────────►│
        │                                   │
   ┌────┴────┐                      ┌────┴────┐
   │ SQLite  │◄──── Sync HTTP ────►│ SQLite  │
   │  Local  │    (Flask API)      │  Local  │
   └─────────┘                      └─────────┘
```

**Como funciona:**
1. Cada celular tem seu próprio banco SQLite
2. Ao conectar na mesma rede WiFi, os dispositivos se descobrem automaticamente
3. Dados são sincronizados via HTTP (API Flask embutida)
4. Conflitos resolvidos por timestamp (último a editar vence)

---

## 📋 Requisitos

### Para Desenvolvimento
- Python 3.8+
- Kivy 2.2+
- Flask
- Requests

### Para Build (Android)
- Ubuntu 20.04+ (ou WSL no Windows)
- Buildozer
- Android SDK
- ~10GB de espaço em disco

---

## 🚀 Instalação (Desenvolvimento Desktop)

```bash
# 1. Navegar até a pasta mobile
cd sistema_almoxarifado/mobile

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install kivy==2.2.1 flask requests zeroconf pillow

# 4. Executar
python main.py
```

---

## 📱 Build para Android

### Usando Buildozer (Ubuntu/WSL)

```bash
# 1. Instalar buildozer
pip install buildozer

# 2. Navegar até a pasta mobile
cd sistema_almoxarifado/mobile

# 3. Inicializar buildozer (primeira vez)
buildozer init

# 4. Fazer build debug
buildozer -v android debug

# 5. APK gerado em:
# ./bin/caixamestremobile-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Instalar no celular

```bash
# Enviar APK para celular (via ADB ou outro método)
adb install bin/caixamestremobile-1.0.0-*.apk

# Ou copiar APK manualmente e instalar
```

---

## 📖 Como Usar

### Primeira Execução

1. Abra o app
2. Digite o PIN: `1234` (padrão, pode ser configurado)
3. Você está no modo **Offline**

### Sincronizar com Outros Dispositivos

1. Conecte todos os celulares na **mesma rede WiFi**
2. No app, toque no botão 🔄 (sincronizar)
3. Aguarde alguns segundos
4. Pronto! Os dispositivos estão sincronizados

### Funcionalidades

| Tela | Descrição |
|------|-----------|
| **Dashboard** | Estatísticas rápidas, ações principais |
| **Materiais** | Lista todos os itens, busca |
| **Entrada** | Adicionar itens ao estoque |
| **Saída** | Registrar retirada de itens |
| **Buscar** | Pesquisa rápida por nome/código |

---

## ⚙️ Configuração

### Alterar PIN
Edite o arquivo `main.py`:
```python
# Na classe LoginScreen
def do_login(self, instance):
    pin = self.pin_input.text
    if pin == '1234':  # ← Altere aqui
        self.manager.current = 'dashboard'
```

### Portas de Rede
- Descoberta: Porta 5007 (UDP multicast)
- Sync HTTP: Porta 5008 (TCP)

### Limitações
- Máximo: 5 dispositivos na mesma rede
- Sync apenas na mesma rede WiFi local
- Não funciona via internet (P2P local apenas)

---

## 🔧 Solução de Problemas

### Dispositivos não se encontram
- Verifique se estão na mesma rede WiFi
- Verifique firewall (portas 5007 e 5008)
- Reinicie o app em ambos os dispositivos

### Sync lento
- Reduza número de materiais (delete antigos)
- Sincronize em horários de menor uso

### App não instala
- Habilitar "Fontes desconhecidas" no Android
- Verificar se APK foi transferido corretamente

---

## 🗺️ Roadmap

- [ ] Scanner de código de barras
- [ ] Fotos dos itens
- [ ] Notificações push (estoque baixo)
- [ ] Backup para nuvem (opcional)
- [ ] Relatórios PDF no celular
- [ ] Multi-almoxarifado (sync seletivo)

---

## 📝 Notas Técnicas

### Banco de Dados
- SQLite local em cada dispositivo
- Schema compatível com versão desktop
- Caminho: `/data/data/com.caixamestre.caixamestremobile/files/caixa_mestre.db`

### Protocolo de Sync
1. **Discovery**: Multicast UDP para encontrar peers
2. **Handshake**: HTTP GET /sync/status para verificar disponibilidade
3. **Push**: HTTP POST /sync/push com dados comprimidos
4. **Merge**: Resolução de conflitos por timestamp

### Segurança
- Sync apenas na rede local (não exposto na internet)
- Sem criptografia (rede local confiável)
- PIN simples (pode ser melhorado com biometria)

---

## 📞 Suporte

Para dúvidas ou problemas:
- Verifique o log: `adb logcat | grep python`
- Ou execute em modo debug: `buildozer android debug deploy run logcat`

---

**Versão:** 1.0.0  
**Data:** Abril 2026  
**Compatibilidade:** Android 5.0+ (API 21+)
