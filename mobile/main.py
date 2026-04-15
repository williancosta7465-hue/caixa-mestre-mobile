"""
CAIXA MESTRE MOBILE
===================
Aplicativo Android para gestão de almoxarifado com sincronização P2P.

Recursos:
- Banco SQLite local
- Sincronização automática entre dispositivos na mesma rede
- Até 5 dispositivos
- Funciona 100% offline
- UI otimizada para celular

Autor: Sistema CAIXA MESTRE
Versão: 1.0.0
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock, mainthread
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

# Configurações globais
Window.clearcolor = (0.17, 0.24, 0.31, 1)  # Cor de fundo azul escuro


class DatabaseManager:
    """Gerenciador do banco SQLite local."""
    
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_database()
    
    def _get_db_path(self):
        """Retorna caminho do banco de dados baseado na plataforma."""
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), 'caixa_mestre.db')
        else:
            # Desktop (desenvolvimento)
            return 'caixa_mestre_mobile.db'
    
    def _init_database(self):
        """Inicializa schema do banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de materiais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT NOT NULL,
                descricao TEXT,
                quantidade REAL DEFAULT 0,
                quantidade_minima REAL DEFAULT 0,
                unidade TEXT DEFAULT 'UN',
                localizacao TEXT,
                categoria TEXT,
                sync_version INTEGER DEFAULT 1,
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de movimentações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,  -- 'entrada', 'saida', 'ajuste'
                material_id INTEGER,
                quantidade REAL NOT NULL,
                responsavel TEXT,
                observacao TEXT,
                sync_version INTEGER DEFAULT 1,
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materiais(id)
            )
        ''')
        
        # Tabela de sincronização
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                sync_type TEXT,
                records_synced INTEGER,
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_materiais_sync ON materiais(sync_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_sync ON movimentacoes(sync_timestamp)')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Retorna conexão com o banco."""
        return sqlite3.connect(self.db_path)
    
    def get_materiais(self, busca=None, categoria=None):
        """Retorna lista de materiais."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM materiais WHERE deleted = 0"
        params = []
        
        if busca:
            query += " AND (nome LIKE ? OR codigo LIKE ? OR descricao LIKE ?)"
            params.extend([f'%{busca}%', f'%{busca}%', f'%{busca}%'])
        
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        
        query += " ORDER BY nome"
        
        cursor.execute(query, params)
        colunas = [desc[0] for desc in cursor.description]
        resultados = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        
        conn.close()
        return resultados
    
    def add_material(self, dados):
        """Adiciona novo material."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO materiais (codigo, nome, descricao, quantidade, 
                                   quantidade_minima, unidade, localizacao, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('codigo'),
            dados['nome'],
            dados.get('descricao', ''),
            dados.get('quantidade', 0),
            dados.get('quantidade_minima', 0),
            dados.get('unidade', 'UN'),
            dados.get('localizacao', ''),
            dados.get('categoria', 'Geral')
        ))
        
        material_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return material_id
    
    def update_quantidade(self, material_id, quantidade, tipo='ajuste', responsavel=''):
        """Atualiza quantidade de material e registra movimentação."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Atualizar material
        cursor.execute('''
            UPDATE materiais 
            SET quantidade = ?, sync_version = sync_version + 1,
                sync_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (quantidade, material_id))
        
        # Registrar movimentação
        cursor.execute('''
            INSERT INTO movimentacoes (tipo, material_id, quantidade, responsavel)
            VALUES (?, ?, ?, ?)
        ''', (tipo, material_id, quantidade, responsavel))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Retorna estatísticas rápidas."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM materiais WHERE deleted = 0")
        total_materiais = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM materiais WHERE quantidade <= quantidade_minima AND deleted = 0")
        estoque_baixo = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(quantidade) FROM materiais WHERE deleted = 0")
        total_itens = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_materiais': total_materiais,
            'estoque_baixo': estoque_baixo,
            'total_itens': int(total_itens)
        }


class SyncManager:
    """Gerenciador de sincronização P2P."""
    
    def __init__(self, db_manager, device_id=None):
        self.db = db_manager
        self.device_id = device_id or self._generate_device_id()
        self.is_syncing = False
        self.peers = {}  # {ip: last_seen}
        self.server_thread = None
        self.running = False
    
    def _generate_device_id(self):
        """Gera ID único do dispositivo."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def start(self):
        """Inicia serviço de sincronização."""
        self.running = True
        # Iniciar thread de descoberta
        threading.Thread(target=self._discovery_loop, daemon=True).start()
        # Iniciar servidor HTTP para receber sync
        threading.Thread(target=self._start_server, daemon=True).start()
        print(f"[SYNC] Iniciado com ID: {self.device_id}")
    
    def stop(self):
        """Para serviço de sincronização."""
        self.running = False
    
    def _discovery_loop(self):
        """Loop de descoberta de dispositivos na rede."""
        import socket
        import struct
        
        # Configurar socket multicast para descoberta
        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = 5007
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MCAST_PORT))
        
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1)
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode())
                
                if msg.get('type') == 'discovery' and msg.get('device_id') != self.device_id:
                    peer_ip = addr[0]
                    self.peers[peer_ip] = time.time()
                    print(f"[DISCOVERY] Peer encontrado: {peer_ip} ({msg.get('device_id')})")
                    
                    # Responder para o peer saber de nós também
                    self._send_discovery_response(peer_ip)
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[DISCOVERY] Erro: {e}")
        
        sock.close()
    
    def _send_discovery_response(self, peer_ip):
        """Responde para peer descobrir este dispositivo."""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = json.dumps({
                'type': 'discovery_response',
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            sock.sendto(msg.encode(), (peer_ip, 5007))
            sock.close()
        except:
            pass
    
    def broadcast_discovery(self):
        """Broadcast para descobrir dispositivos."""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            msg = json.dumps({
                'type': 'discovery',
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            
            sock.sendto(msg.encode(), ('224.1.1.1', 5007))
            sock.close()
            print("[DISCOVERY] Broadcast enviado")
        except Exception as e:
            print(f"[DISCOVERY] Erro broadcast: {e}")
    
    def _start_server(self):
        """Inicia servidor HTTP para receber sincronizações."""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/sync/push', methods=['POST'])
        def receive_sync():
            """Recebe dados de sincronização de outro dispositivo."""
            try:
                data = request.json
                return self._process_sync_data(data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/sync/status', methods=['GET'])
        def sync_status():
            """Retorna status para verificação."""
            return jsonify({
                'device_id': self.device_id,
                'timestamp': time.time()
            })
        
        # Rodar em thread separada
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        app.run(host='0.0.0.0', port=5008, threaded=True, debug=False)
    
    def _process_sync_data(self, data):
        """Processa dados recebidos de outro dispositivo."""
        from flask import jsonify
        
        try:
            materiais = data.get('materiais', [])
            movimentacoes = data.get('movimentacoes', [])
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            records_synced = 0
            
            # Processar materiais
            for mat in materiais:
                cursor.execute('''
                    SELECT sync_version, sync_timestamp FROM materiais WHERE id = ?
                ''', (mat['id'],))
                
                local = cursor.fetchone()
                
                if local:
                    local_version, local_ts = local
                    # Se versão remota é maior ou timestamp mais recente
                    if mat.get('sync_version', 0) > local_version or \
                       mat.get('sync_timestamp', '') > local_ts:
                        cursor.execute('''
                            UPDATE materiais 
                            SET nome=?, descricao=?, quantidade=?, quantidade_minima=?,
                                unidade=?, localizacao=?, categoria=?, sync_version=?,
                                sync_timestamp=?, deleted=?
                            WHERE id=?
                        ''', (mat['nome'], mat['descricao'], mat['quantidade'],
                              mat['quantidade_minima'], mat['unidade'], mat['localizacao'],
                              mat['categoria'], mat['sync_version'], mat['sync_timestamp'],
                              mat.get('deleted', 0), mat['id']))
                        records_synced += 1
                else:
                    # Novo registro
                    cursor.execute('''
                        INSERT INTO materiais (id, codigo, nome, descricao, quantidade,
                                               quantidade_minima, unidade, localizacao,
                                               categoria, sync_version, sync_timestamp, deleted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (mat['id'], mat['codigo'], mat['nome'], mat['descricao'],
                          mat['quantidade'], mat['quantidade_minima'], mat['unidade'],
                          mat['localizacao'], mat['categoria'], mat['sync_version'],
                          mat['sync_timestamp'], mat.get('deleted', 0)))
                    records_synced += 1
            
            conn.commit()
            conn.close()
            
            # Registrar sync
            self._log_sync(data.get('device_id'), 'received', records_synced, 'success')
            
            return jsonify({
                'success': True,
                'records_synced': records_synced
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def _log_sync(self, device_id, sync_type, records, status):
        """Registra operação de sync no log."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sync_log (device_id, sync_type, records_synced, status)
            VALUES (?, ?, ?, ?)
        ''', (device_id, sync_type, records, status))
        conn.commit()
        conn.close()
    
    def sync_to_peer(self, peer_ip, callback=None):
        """Sincroniza dados com um peer específico."""
        if self.is_syncing:
            if callback:
                callback(False, "Sincronização já em andamento")
            return
        
        self.is_syncing = True
        
        try:
            # Obter dados locais
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codigo, nome, descricao, quantidade, quantidade_minima,
                       unidade, localizacao, categoria, sync_version, sync_timestamp, deleted
                FROM materiais
            ''')
            colunas = [desc[0] for desc in cursor.description]
            materiais = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT * FROM movimentacoes 
                WHERE sync_timestamp > datetime('now', '-7 days')
            ''')
            colunas = [desc[0] for desc in cursor.description]
            movimentacoes = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            # Enviar para peer
            data = {
                'device_id': self.device_id,
                'timestamp': time.time(),
                'materiais': materiais,
                'movimentacoes': movimentacoes
            }
            
            # Fazer request HTTP
            import requests
            response = requests.post(
                f'http://{peer_ip}:5008/sync/push',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                records_synced = result.get('records_synced', 0)
                self._log_sync(peer_ip, 'sent', records_synced, 'success')
                
                if callback:
                    callback(True, f"{records_synced} registros sincronizados")
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[SYNC] Erro: {e}")
            if callback:
                callback(False, str(e))
        finally:
            self.is_syncing = False
    
    def sync_all(self, callback=None):
        """Sincroniza com todos os peers conhecidos."""
        peers = list(self.peers.keys())
        
        if not peers:
            if callback:
                callback(False, "Nenhum dispositivo encontrado na rede")
            return
        
        results = []
        for peer_ip in peers:
            self.sync_to_peer(peer_ip, lambda success, msg: results.append((peer_ip, success, msg)))
        
        if callback:
            success_count = sum(1 for _, s, _ in results if s)
            callback(True, f"Sincronizado com {success_count}/{len(peers)} dispositivos")


# ============== TELAS KIVY ==============

class LoginScreen(Screen):
    """Tela de login simplificada para mobile."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Logo
        layout.add_widget(Label(
            text='📦',
            font_size='60sp',
            size_hint_y=None,
            height=80
        ))
        
        # Título
        layout.add_widget(Label(
            text='CAIXA MESTRE',
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1)
        ))
        
        layout.add_widget(Label(
            text='Gestão de Estoque',
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=30
        ))
        
        # Espaço
        layout.add_widget(Label(size_hint_y=None, height=30))
        
        # Campos de login (simplificado - apenas PIN ou direto)
        layout.add_widget(Label(
            text='PIN de Acesso:',
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=30
        ))
        
        self.pin_input = TextInput(
            multiline=False,
            password=True,
            input_type='number',
            font_size='20sp',
            size_hint_y=None,
            height=50,
            halign='center'
        )
        layout.add_widget(self.pin_input)
        
        # Botão entrar
        btn_entrar = Button(
            text='ENTRAR',
            font_size='18sp',
            size_hint_y=None,
            height=50,
            background_color=(0.16, 0.53, 0.72, 1)  # Azul #2980b9
        )
        btn_entrar.bind(on_press=self.do_login)
        layout.add_widget(btn_entrar)
        
        # Botão modo offline
        btn_offline = Button(
            text='MODO OFFLINE',
            font_size='14sp',
            size_hint_y=None,
            height=40,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_offline.bind(on_press=self.go_offline)
        layout.add_widget(btn_offline)
        
        # Status
        self.lbl_status = Label(
            text='',
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.lbl_status)
        
        self.add_widget(layout)
    
    def do_login(self, instance):
        pin = self.pin_input.text
        if pin == '1234':  # PIN simples para mobile
            self.manager.current = 'dashboard'
        else:
            self.lbl_status.text = 'PIN incorreto'
    
    def go_offline(self, instance):
        self.manager.current = 'dashboard'


class DashboardScreen(Screen):
    """Tela principal com resumo do estoque."""
    
    def __init__(self, db_manager, sync_manager, **kwargs):
        super().__init__(**kwargs)
        self.db = db_manager
        self.sync = sync_manager
        self.build_ui()
        Clock.schedule_interval(self.update_stats, 5)  # Atualizar a cada 5s
    
    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(
            size_hint_y=None,
            height=60,
            padding=10
        )
        with header.canvas.before:
            Color(0.12, 0.19, 0.26, 1)
            Rectangle(pos=header.pos, size=header.size)
        
        header.add_widget(Label(
            text='📦 CAIXA MESTRE',
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_x=0.7
        ))
        
        # Botão sync
        self.btn_sync = Button(
            text='🔄',
            font_size='20sp',
            size_hint_x=0.15,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.btn_sync.bind(on_press=self.do_sync)
        header.add_widget(self.btn_sync)
        
        # Botão menu
        btn_menu = Button(
            text='☰',
            font_size='20sp',
            size_hint_x=0.15,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        btn_menu.bind(on_press=self.show_menu)
        header.add_widget(btn_menu)
        
        main_layout.add_widget(header)
        
        # Stats cards
        stats_layout = GridLayout(cols=2, padding=10, spacing=10, size_hint_y=None, height=150)
        
        # Card 1: Total materiais
        self.card_total = self.create_card('Total Itens', '0', (0.16, 0.53, 0.72, 1))
        stats_layout.add_widget(self.card_total)
        
        # Card 2: Estoque baixo
        self.card_baixo = self.create_card('Estoque Baixo', '0', (0.9, 0.3, 0.3, 1))
        stats_layout.add_widget(self.card_baixo)
        
        # Card 3: Total em estoque
        self.card_estoque = self.create_card('Em Estoque', '0', (0.2, 0.7, 0.4, 1))
        stats_layout.add_widget(self.card_estoque)
        
        # Card 4: Status sync
        self.card_sync = self.create_card('Sync', 'Online', (0.6, 0.6, 0.6, 1))
        stats_layout.add_widget(self.card_sync)
        
        main_layout.add_widget(stats_layout)
        
        # Ações rápidas
        actions_label = Label(
            text='AÇÕES RÁPIDAS',
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None,
            height=30
        )
        main_layout.add_widget(actions_label)
        
        actions_layout = GridLayout(cols=2, padding=10, spacing=10, size_hint_y=None, height=200)
        
        actions = [
            ('📦\nMateriais', 'materiais', (0.16, 0.53, 0.72, 1)),
            ('➕\nEntrada', 'entrada', (0.2, 0.7, 0.4, 1)),
            ('➖\nSaída', 'saida', (0.9, 0.5, 0.2, 1)),
            ('🔍\nBuscar', 'buscar', (0.5, 0.5, 0.5, 1)),
        ]
        
        for text, action, color in actions:
            btn = Button(
                text=text,
                font_size='16sp',
                background_color=color,
                halign='center'
            )
            btn.bind(on_press=lambda x, a=action: self.do_action(a))
            actions_layout.add_widget(btn)
        
        main_layout.add_widget(actions_layout)
        
        # Lista de alertas
        alert_label = Label(
            text='ALERTAS',
            font_size='14sp',
            color=(0.9, 0.3, 0.3, 1),
            size_hint_y=None,
            height=30
        )
        main_layout.add_widget(alert_label)
        
        self.alerts_list = Label(
            text='Sem alertas',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=100
        )
        main_layout.add_widget(self.alerts_list)
        
        self.add_widget(main_layout)
    
    def create_card(self, title, value, color):
        """Cria um card de estatística."""
        card = BoxLayout(orientation='vertical', padding=10)
        with card.canvas.before:
            Color(*color)
            Rectangle(pos=card.pos, size=card.size)
        
        card.bind(pos=self._update_rect, size=self._update_rect)
        
        card.add_widget(Label(
            text=title,
            font_size='12sp',
            color=(1, 1, 1, 0.8),
            size_hint_y=0.4
        ))
        
        lbl_value = Label(
            text=value,
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=0.6
        )
        card.lbl_value = lbl_value  # Guardar referência
        card.add_widget(lbl_value)
        
        return card
    
    def _update_rect(self, instance, value):
        """Atualiza retângulo de fundo."""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*instance.background_color if hasattr(instance, 'background_color') else (0.5, 0.5, 0.5, 1))
            Rectangle(pos=instance.pos, size=instance.size)
    
    def update_stats(self, dt):
        """Atualiza estatísticas."""
        try:
            stats = self.db.get_stats()
            
            self.card_total.lbl_value.text = str(stats['total_materiais'])
            self.card_baixo.lbl_value.text = str(stats['estoque_baixo'])
            self.card_estoque.lbl_value.text = str(stats['total_itens'])
            
            # Verificar peers
            peers_count = len(self.sync.peers)
            if peers_count > 0:
                self.card_sync.lbl_value.text = f'{peers_count} peers'
                self.card_sync.lbl_value.color = (0.2, 0.8, 0.4, 1)
            else:
                self.card_sync.lbl_value.text = 'Offline'
                self.card_sync.lbl_value.color = (0.8, 0.8, 0.8, 1)
            
            # Atualizar alertas
            if stats['estoque_baixo'] > 0:
                self.alerts_list.text = f'⚠️ {stats["estoque_baixo"]} itens com estoque baixo!'
                self.alerts_list.color = (0.9, 0.3, 0.3, 1)
            else:
                self.alerts_list.text = '✓ Estoque OK'
                self.alerts_list.color = (0.2, 0.8, 0.4, 1)
                
        except Exception as e:
            print(f"[DASHBOARD] Erro ao atualizar stats: {e}")
    
    def do_sync(self, instance):
        """Inicia sincronização."""
        self.btn_sync.text = '⏳'
        self.sync.broadcast_discovery()
        
        Clock.schedule_once(lambda dt: self._do_sync_delayed(), 2)
    
    def _do_sync_delayed(self):
        """Executa sync após descoberta."""
        def on_complete(success, message):
            Clock.schedule_once(lambda dt: self._update_sync_btn(success, message), 0)
        
        self.sync.sync_all(on_complete)
    
    @mainthread
    def _update_sync_btn(self, success, message):
        """Atualiza botão após sync."""
        self.btn_sync.text = '🔄' if success else '❌'
        # Mostrar toast ou popup com mensagem
        print(f"[SYNC] {message}")
    
    def show_menu(self, instance):
        """Mostra menu lateral."""
        # TODO: Implementar menu com configurações, sobre, logout
        pass
    
    def do_action(self, action):
        """Executa ação do botão."""
        if action == 'materiais':
            self.manager.current = 'materiais'
        elif action == 'entrada':
            self.manager.current = 'movimentacao'
            self.manager.get_screen('movimentacao').set_tipo('entrada')
        elif action == 'saida':
            self.manager.current = 'movimentacao'
            self.manager.get_screen('movimentacao').set_tipo('saida')
        elif action == 'buscar':
            self.manager.current = 'buscar'


class MateriaisScreen(Screen):
    """Tela de listagem de materiais."""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db = db_manager
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(size_hint_y=None, height=50, padding=5)
        header.add_widget(Label(
            text='📦 MATERIAIS',
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1)
        ))
        layout.add_widget(header)
        
        # Busca
        search_box = BoxLayout(size_hint_y=None, height=50, padding=5)
        self.search_input = TextInput(
            hint_text='Buscar material...',
            multiline=False,
            size_hint_x=0.8
        )
        btn_search = Button(
            text='🔍',
            size_hint_x=0.2,
            background_color=(0.16, 0.53, 0.72, 1)
        )
        btn_search.bind(on_press=self.do_search)
        search_box.add_widget(self.search_input)
        search_box.add_widget(btn_search)
        layout.add_widget(search_box)
        
        # Lista
        scroll = ScrollView()
        self.list_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        scroll.add_widget(self.list_container)
        layout.add_widget(scroll)
        
        # Botão voltar
        btn_voltar = Button(
            text='← VOLTAR',
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(btn_voltar)
        
        self.add_widget(layout)
        
        # Carregar dados
        self.load_materiais()
    
    def load_materiais(self, busca=None):
        """Carrega lista de materiais."""
        self.list_container.clear_widgets()
        
        materiais = self.db.get_materiais(busca=busca)
        
        for mat in materiais:
            btn = Button(
                text=f"{mat['nome']}\nQtd: {mat['quantidade']} {mat['unidade']}",
                halign='left',
                size_hint_y=None,
                height=60,
                background_color=(0.2, 0.3, 0.4, 1)
            )
            btn.bind(on_press=lambda x, m=mat: self.show_material_detail(m))
            self.list_container.add_widget(btn)
    
    def do_search(self, instance):
        """Executa busca."""
        self.load_materiais(self.search_input.text)
    
    def show_material_detail(self, material):
        """Mostra detalhes do material."""
        # TODO: Abrir tela de detalhes
        pass
    
    def on_enter(self):
        """Chamado quando entra na tela."""
        self.load_materiais()


class CaixaMestreApp(App):
    """Aplicativo principal."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.sync = SyncManager(self.db)
    
    def build(self):
        # Configurar janela
        Window.bind(on_keyboard=self._on_keyboard)
        
        # Criar screen manager
        sm = ScreenManager(transition=SlideTransition())
        
        # Telas
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(self.db, self.sync, name='dashboard'))
        sm.add_widget(MateriaisScreen(self.db, name='materiais'))
        # TODO: Adicionar mais telas (movimentacao, buscar, etc.)
        
        # Iniciar sync
        self.sync.start()
        Clock.schedule_interval(lambda dt: self.sync.broadcast_discovery(), 30)  # Broadcast a cada 30s
        
        return sm
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Captura tecla voltar no Android."""
        if key == 27:  # ESC / Botão voltar Android
            # Verificar se pode voltar
            screen = self.root.current_screen
            if self.root.current != 'dashboard':
                self.root.current = 'dashboard'
                return True
        return False
    
    def on_stop(self):
        """Chamado ao fechar app."""
        self.sync.stop()


# ============== ENTRY POINT ==============

if __name__ == '__main__':
    # Verificar dependências
    try:
        import flask
    except ImportError:
        print("ERRO: Flask não instalado. Instale com: pip install flask")
        sys.exit(1)
    
    try:
        import requests
    except ImportError:
        print("ERRO: requests não instalado. Instale com: pip install requests")
        sys.exit(1)
    
    # Iniciar app
    CaixaMestreApp().run()
