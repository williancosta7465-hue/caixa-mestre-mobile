"""
Sync Manager - Caixa Mestre Mobile
Gerenciamento de sincronização P2P entre dispositivos.
"""

import json
import time
import threading
import socket
import struct
import uuid
from datetime import datetime


class SyncManager:
    """Gerenciador de sincronização P2P."""
    
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    HTTP_PORT = 5008
    MAX_PEERS = 5
    
    def __init__(self, db_manager, device_id=None):
        self.db = db_manager
        self.device_id = device_id or self._generate_device_id()
        self.is_syncing = False
        self.peers = {}  # {ip: {'last_seen': timestamp, 'device_id': id}}
        self.running = False
        self.server_thread = None
        
        print(f"[SYNC] Dispositivo ID: {self.device_id}")
    
    def _generate_device_id(self):
        """Gera ID único do dispositivo."""
        return str(uuid.uuid4())[:8]
    
    def start(self):
        """Inicia serviços de sincronização."""
        self.running = True
        
        # Thread de descoberta
        threading.Thread(target=self._discovery_loop, daemon=True).start()
        
        # Thread do servidor HTTP
        threading.Thread(target=self._start_server, daemon=True).start()
        
        print("[SYNC] Serviços iniciados")
    
    def stop(self):
        """Para serviços."""
        self.running = False
        print("[SYNC] Serviços parados")
    
    def _discovery_loop(self):
        """Loop de descoberta de dispositivos na rede."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.MCAST_PORT))
        
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(2)
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode())
                
                if msg.get('type') == 'discovery' and msg.get('device_id') != self.device_id:
                    peer_ip = addr[0]
                    if peer_ip not in self.peers:
                        print(f"[DISCOVERY] Novo peer: {peer_ip} ({msg.get('device_id')})")
                    
                    self.peers[peer_ip] = {
                        'last_seen': time.time(),
                        'device_id': msg.get('device_id')
                    }
                    
                    # Responder
                    self._send_discovery_response(peer_ip)
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[DISCOVERY] Erro: {e}")
        
        sock.close()
    
    def _send_discovery_response(self, peer_ip):
        """Responde para peer nos descobrir."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = json.dumps({
                'type': 'discovery_response',
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            sock.sendto(msg.encode(), (peer_ip, self.MCAST_PORT))
            sock.close()
        except:
            pass
    
    def broadcast_discovery(self):
        """Broadcast para descobrir dispositivos."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            msg = json.dumps({
                'type': 'discovery',
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            
            sock.sendto(msg.encode(), (self.MCAST_GRP, self.MCAST_PORT))
            sock.close()
            print("[DISCOVERY] Broadcast enviado")
        except Exception as e:
            print(f"[DISCOVERY] Erro broadcast: {e}")
    
    def _start_server(self):
        """Inicia servidor HTTP para receber sincronizações."""
        try:
            from flask import Flask, request, jsonify
            
            app = Flask(__name__)
            
            @app.route('/sync/push', methods=['POST'])
            def receive_sync():
                """Recebe dados de sincronização."""
                try:
                    data = request.json
                    return self._process_sync_data(data)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @app.route('/sync/status', methods=['GET'])
            def sync_status():
                """Retorna status."""
                return jsonify({
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'peers': len(self.peers)
                })
            
            # Silenciar logs Flask
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            app.run(host='0.0.0.0', port=self.HTTP_PORT, threaded=True, debug=False)
            
        except Exception as e:
            print(f"[SERVER] Erro: {e}")
    
    def _process_sync_data(self, data):
        """Processa dados recebidos."""
        from flask import jsonify
        
        try:
            materiais = data.get('materiais', [])
            device_id = data.get('device_id', 'unknown')
            
            records_synced = 0
            
            for mat in materiais:
                try:
                    self._merge_material(mat)
                    records_synced += 1
                except Exception as e:
                    print(f"[MERGE] Erro em material {mat.get('id')}: {e}")
            
            # Log
            self._log_sync(device_id, 'received', records_synced, 'success')
            
            return jsonify({
                'success': True,
                'records_synced': records_synced
            })
            
        except Exception as e:
            print(f"[PROCESS] Erro: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def _merge_material(self, mat):
        """Faz merge de um material recebido."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se material existe localmente
        cursor.execute('SELECT sync_version, sync_timestamp FROM materiais WHERE id = ?', (mat['id'],))
        local = cursor.fetchone()
        
        if local:
            local_version, local_ts = local
            remote_version = mat.get('sync_version', 0)
            remote_ts = mat.get('sync_timestamp', '')
            
            # Se versão remota é maior ou timestamp mais recente
            if remote_version > local_version or remote_ts > local_ts:
                cursor.execute('''
                    UPDATE materiais 
                    SET nome=?, codigo=?, descricao=?, quantidade=?, 
                        quantidade_minima=?, unidade=?, localizacao=?, categoria=?,
                        sync_version=?, sync_timestamp=?, deleted=?
                    WHERE id=?
                ''', (
                    mat['nome'], mat['codigo'], mat['descricao'], mat['quantidade'],
                    mat['quantidade_minima'], mat['unidade'], mat['localizacao'],
                    mat['categoria'], mat['sync_version'], mat['sync_timestamp'],
                    mat.get('deleted', 0), mat['id']
                ))
        else:
            # Novo material
            cursor.execute('''
                INSERT INTO materiais (id, codigo, nome, descricao, quantidade,
                                       quantidade_minima, unidade, localizacao, categoria,
                                       sync_version, sync_timestamp, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                mat['id'], mat['codigo'], mat['nome'], mat['descricao'],
                mat['quantidade'], mat['quantidade_minima'], mat['unidade'],
                mat['localizacao'], mat['categoria'], mat['sync_version'],
                mat['sync_timestamp'], mat.get('deleted', 0)
            ))
        
        conn.commit()
        conn.close()
    
    def _log_sync(self, device_id, sync_type, records, status):
        """Registra operação de sync."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sync_log (device_id, sync_type, records_synced, status)
                VALUES (?, ?, ?, ?)
            ''', (device_id, sync_type, records, status))
            conn.commit()
            conn.close()
        except:
            pass
    
    def sync_to_peer(self, peer_ip, callback=None):
        """Sincroniza com um peer."""
        if self.is_syncing:
            if callback:
                callback(False, "Sync em andamento")
            return
        
        self.is_syncing = True
        
        try:
            # Obter dados locais
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codigo, nome, descricao, quantidade, quantidade_minima,
                       unidade, localizacao, categoria, sync_version, sync_timestamp, deleted
                FROM materiais WHERE deleted = 0
            ''')
            
            colunas = [desc[0] for desc in cursor.description]
            materiais = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            # Enviar
            data = {
                'device_id': self.device_id,
                'timestamp': time.time(),
                'materiais': materiais
            }
            
            import requests
            response = requests.post(
                f'http://{peer_ip}:{self.HTTP_PORT}/sync/push',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    records = result.get('records_synced', 0)
                    self._log_sync(peer_ip, 'sent', records, 'success')
                    if callback:
                        callback(True, f"{records} registros sincronizados")
                else:
                    raise Exception(result.get('error', 'Erro desconhecido'))
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[SYNC] Erro: {e}")
            if callback:
                callback(False, str(e))
        finally:
            self.is_syncing = False
    
    def sync_all(self, callback=None):
        """Sincroniza com todos os peers."""
        # Limpar peers antigos (> 5 minutos)
        now = time.time()
        self.peers = {ip: data for ip, data in self.peers.items() 
                      if now - data['last_seen'] < 300}
        
        peers = list(self.peers.keys())
        
        if not peers:
            if callback:
                callback(False, "Nenhum dispositivo encontrado")
            return
        
        if len(peers) > self.MAX_PEERS:
            peers = peers[:self.MAX_PEERS]
        
        success_count = 0
        for peer_ip in peers:
            self.sync_to_peer(peer_ip)
            success_count += 1
        
        if callback:
            callback(True, f"Sincronizado com {success_count} dispositivo(s)")
