"""
CAIXA MESTRE MOBILE - VERSÃO COMPLETA
=====================================
Aplicativo Android para gestão de almoxarifado com sincronização P2P.

Versão: 1.0.0
Autor: Sistema CAIXA MESTRE
Data: Abril 2026

Requisitos:
- Python 3.8+
- Kivy 2.2+
- Flask
- Requests

Instalação:
    pip install kivy==2.2.1 flask requests pillow zeroconf

Build Android (requer Ubuntu/WSL):
    buildozer -v android debug
"""

import os
import sys

# Adicionar pasta screens ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from sync_manager import SyncManager
from screens import (
    LoginScreen,
    DashboardScreen,
    MateriaisScreen,
    MovimentacaoScreen,
    BuscaScreen,
    DetalheMaterialScreen
)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

# Configurações de janela
Window.clearcolor = (0.12, 0.19, 0.26, 1)


class CaixaMestreApp(App):
    """Aplicativo principal CAIXA MESTRE Mobile."""
    
    title = 'CAIXA MESTRE Mobile'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.sync = SyncManager(self.db)
    
    def build(self):
        """Constrói a interface do aplicativo."""
        # Configurar teclado Android
        Window.bind(on_keyboard=self._on_keyboard)
        
        # Criar gerenciador de telas
        sm = ScreenManager(transition=SlideTransition())
        
        # Adicionar todas as telas
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(self.db, self.sync, name='dashboard'))
        sm.add_widget(MateriaisScreen(self.db, name='materiais'))
        sm.add_widget(MovimentacaoScreen(self.db, name='movimentacao'))
        sm.add_widget(BuscaScreen(self.db, name='busca'))
        sm.add_widget(DetalheMaterialScreen(self.db, name='detalhe_material'))
        
        # Iniciar sincronização
        self.sync.start()
        
        # Broadcast de descoberta a cada 30 segundos
        Clock.schedule_interval(
            lambda dt: self.sync.broadcast_discovery(),
            30
        )
        
        return sm
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Captura tecla voltar (Android)."""
        if key == 27:  # ESC / Botão voltar
            sm = self.root
            if sm.current != 'dashboard' and sm.current != 'login':
                sm.current = 'dashboard'
                return True
        return False
    
    def on_pause(self):
        """Chamado quando app vai para background (Android)."""
        return True
    
    def on_resume(self):
        """Chamado quando app volta do background."""
        pass
    
    def on_stop(self):
        """Chamado ao fechar o app."""
        self.sync.stop()
        print("[APP] Aplicativo encerrado")


# ============== ENTRY POINT ==============

if __name__ == '__main__':
    # Verificar dependências
    dependencias_faltando = []
    
    try:
        import flask
    except ImportError:
        dependencias_faltando.append('flask')
    
    try:
        import requests
    except ImportError:
        dependencias_faltando.append('requests')
    
    try:
        import kivy
    except ImportError:
        dependencias_faltando.append('kivy')
    
    if dependencias_faltando:
        print("=" * 50)
        print("ERRO: Dependências faltando!")
        print("=" * 50)
        print("\nInstale com:")
        print(f"pip install {' '.join(dependencias_faltando)}")
        print("\nOu instale tudo:")
        print("pip install kivy==2.2.1 flask requests pillow zeroconf")
        print("=" * 50)
        sys.exit(1)
    
    # Iniciar aplicação
    print("=" * 50)
    print("CAIXA MESTRE MOBILE")
    print("=" * 50)
    print("Iniciando...")
    
    CaixaMestreApp().run()
