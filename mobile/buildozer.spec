[app]
# Nome do aplicativo
name = Caixa Mestre Mobile
title = Caixa Mestre Mobile

# Nome do pacote (deve ser único)
package.name = caixamestremobile

# Domínio do pacote
package.domain = com.caixamestre

# Arquivo principal
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db,ttf

# Versão
version = 1.0.0

# Requisitos
requirements = python3,kivy==2.2.1,kivymd,pillow,sqlite3,flask,requests,zeroconf

# Orientação da tela (portrait, landscape, all)
orientation = portrait

# Ícone do aplicativo
icon.filename = %(source.dir)s/../icone.ico

# Permissões do Android (necessárias para rede e storage)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API Android alvo
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Arquiteturas suportadas
android.archs = arm64-v8a, armeabi-v7a

# Modo de depuração (0 = release, 1 = debug)
android.debug = 1

# Configurações de rede
android.useAndroidX = True

[buildozer]
# Caminho de log
log_dir = ./logs

# Modo de build
build_mode = debug

# Perfil de build
warn_on_root = 1
