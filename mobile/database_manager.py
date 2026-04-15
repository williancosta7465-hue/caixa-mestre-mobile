"""
Database Manager - Caixa Mestre Mobile
Gerenciamento do banco SQLite local.
"""

import os
import sqlite3
from datetime import datetime
from kivy.utils import platform


class DatabaseManager:
    """Gerenciador do banco SQLite local."""
    
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_database()
        print(f"[DB] Banco: {self.db_path}")
    
    def _get_db_path(self):
        """Retorna caminho do banco baseado na plataforma."""
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), 'caixa_mestre.db')
        else:
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
                tipo TEXT NOT NULL,
                material_id INTEGER,
                quantidade REAL NOT NULL,
                responsavel TEXT,
                observacao TEXT,
                sync_version INTEGER DEFAULT 1,
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materiais(id)
            )
        ''')
        
        # Tabela de log de sincronização
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
        
        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_materiais_sync ON materiais(sync_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_sync ON movimentacoes(sync_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_materiais_nome ON materiais(nome)')
        
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
    
    def get_material_by_id(self, material_id):
        """Retorna material por ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM materiais WHERE id = ? AND deleted = 0",
            (material_id,)
        )
        
        row = cursor.fetchone()
        if row:
            colunas = [desc[0] for desc in cursor.description]
            resultado = dict(zip(colunas, row))
        else:
            resultado = None
        
        conn.close()
        return resultado
    
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
    
    def update_material(self, material_id, dados):
        """Atualiza dados do material."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE materiais 
            SET nome = ?, codigo = ?, descricao = ?, quantidade_minima = ?,
                unidade = ?, localizacao = ?, categoria = ?,
                sync_version = sync_version + 1,
                sync_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            dados.get('nome'),
            dados.get('codigo'),
            dados.get('descricao', ''),
            dados.get('quantidade_minima', 0),
            dados.get('unidade', 'UN'),
            dados.get('localizacao', ''),
            dados.get('categoria', 'Geral'),
            material_id
        ))
        
        conn.commit()
        conn.close()
    
    def update_quantidade(self, material_id, quantidade, tipo='ajuste', responsavel=''):
        """Atualiza quantidade e registra movimentação."""
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
        ''', (tipo, material_id, quantidade, responsavel or 'Sistema'))
        
        conn.commit()
        conn.close()
    
    def delete_material(self, material_id):
        """Marca material como deletado (soft delete)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE materiais 
            SET deleted = 1, sync_version = sync_version + 1,
                sync_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (material_id,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Retorna estatísticas rápidas."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM materiais WHERE deleted = 0")
        total_materiais = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM materiais 
            WHERE quantidade <= quantidade_minima AND deleted = 0
        ''')
        estoque_baixo = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM materiais 
            WHERE quantidade = 0 AND deleted = 0
        ''')
        estoque_critico = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(quantidade) FROM materiais WHERE deleted = 0")
        total_itens = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_materiais': total_materiais,
            'estoque_baixo': estoque_baixo,
            'estoque_critico': estoque_critico,
            'total_itens': int(total_itens)
        }
    
    def get_changes_since(self, timestamp):
        """Retorna alterações desde um timestamp (para sync)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM materiais 
            WHERE sync_timestamp > ?
            ORDER BY sync_timestamp
        ''', (timestamp,))
        
        colunas = [desc[0] for desc in cursor.description]
        materiais = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT * FROM movimentacoes 
            WHERE sync_timestamp > ?
            ORDER BY sync_timestamp
        ''', (timestamp,))
        
        colunas = [desc[0] for desc in cursor.description]
        movimentacoes = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'materiais': materiais,
            'movimentacoes': movimentacoes
        }
