import sqlite3
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.fetchall()
        conn.close()
        return result
    
    def execute_insert(self, query: str, params: tuple = ()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

def init_db(db_path: str):
    """Initialise la base de données"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table pour les fichiers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            total_size INTEGER NOT NULL,
            block_count INTEGER NOT NULL,
            block_size INTEGER NOT NULL,
            status TEXT DEFAULT 'distributed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table pour les blocs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            block_number INTEGER NOT NULL,
            block_hash TEXT NOT NULL,
            block_size INTEGER NOT NULL,
            machine_url TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            status TEXT DEFAULT 'stored',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
    ''')
    
    # Table pour les machines
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table pour les paramètres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

class FileModel:
    def __init__(self, db: Database):
        self.db = db
    
    def create_file(self, original_name: str, file_hash: str, total_size: int, 
                   block_count: int, block_size: int) -> Optional[int]:
        return self.db.execute_insert('''
            INSERT INTO files (original_name, file_hash, total_size, block_count, block_size) 
            VALUES (?, ?, ?, ?, ?)
        ''', (original_name, file_hash, total_size, block_count, block_size))
    
    def get_all_files(self) -> List[Dict]:
        rows = self.db.execute_query('SELECT * FROM files ORDER BY created_at DESC')
        return [
            {
                'id': row[0], 'original_name': row[1], 'file_hash': row[2],
                'total_size': row[3], 'block_count': row[4], 'block_size': row[5],
                'status': row[6], 'created_at': row[7]
            }
            for row in rows
        ]
    
    def get_file_by_id(self, file_id: int) -> Optional[Dict]:
        rows = self.db.execute_query('SELECT * FROM files WHERE id = ?', (file_id,))
        if rows:
            row = rows[0]
            return {
                'id': row[0], 'original_name': row[1], 'file_hash': row[2],
                'total_size': row[3], 'block_count': row[4], 'block_size': row[5],
                'status': row[6], 'created_at': row[7]
            }
        return None
    
    def update_file_status(self, file_id: int, status: str):
        self.db.execute_query('UPDATE files SET status = ? WHERE id = ?', (status, file_id))
    
    def delete_file(self, file_id: int):
        self.db.execute_query('DELETE FROM files WHERE id = ?', (file_id,))

class BlockModel:
    def __init__(self, db: Database):
        self.db = db
    
    def create_block(self, file_id: int, block_number: int, block_hash: str, 
                    block_size: int, machine_url: str, storage_path: str) -> Optional[int]:
        return self.db.execute_insert('''
            INSERT INTO blocks (file_id, block_number, block_hash, block_size, machine_url, storage_path) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_id, block_number, block_hash, block_size, machine_url, storage_path))
    
    def get_blocks_by_file_id(self, file_id: int) -> List[Dict]:
        rows = self.db.execute_query('''
            SELECT * FROM blocks WHERE file_id = ? ORDER BY block_number
        ''', (file_id,))
        return [
            {
                'id': row[0], 'file_id': row[1], 'block_number': row[2],
                'block_hash': row[3], 'block_size': row[4], 'machine_url': row[5],
                'storage_path': row[6], 'status': row[7], 'created_at': row[8]
            }
            for row in rows
        ]
    
    def delete_blocks_by_file_id(self, file_id: int):
        self.db.execute_query('DELETE FROM blocks WHERE file_id = ?', (file_id,))

class MachineModel:
    def __init__(self, db: Database):
        self.db = db
    
    def create_machine(self, name: str, url: str, storage_path: str) -> Optional[int]:
        return self.db.execute_insert('''
            INSERT INTO machines (name, url, storage_path) 
            VALUES (?, ?, ?)
        ''', (name, url, storage_path))
    
    def get_all_machines(self) -> List[Dict]:
        rows = self.db.execute_query('SELECT * FROM machines ORDER BY name')
        return [
            {
                'id': row[0], 'name': row[1], 'url': row[2],
                'storage_path': row[3], 'is_active': row[4], 'last_check': row[5]
            }
            for row in rows
        ]
    
    def get_active_machines(self) -> List[Dict]:
        rows = self.db.execute_query('SELECT * FROM machines WHERE is_active = TRUE ORDER BY name')
        return [
            {
                'id': row[0], 'name': row[1], 'url': row[2],
                'storage_path': row[3], 'is_active': row[4], 'last_check': row[5]
            }
            for row in rows
        ]
    
    def update_machine(self, machine_id: int, name: str, url: str, storage_path: str):
        self.db.execute_query('''
            UPDATE machines SET name = ?, url = ?, storage_path = ? 
            WHERE id = ?
        ''', (name, url, storage_path, machine_id))
    
    def toggle_machine_status(self, machine_id: int):
        self.db.execute_query('''
            UPDATE machines SET is_active = NOT is_active WHERE id = ?
        ''', (machine_id,))
    
    def delete_machine(self, machine_id: int):
        self.db.execute_query('DELETE FROM machines WHERE id = ?', (machine_id,))

class SettingsModel:
    def __init__(self, db: Database):
        self.db = db
    
    def get_setting(self, key: str, default_value: str) -> str:
        rows = self.db.execute_query('SELECT value FROM settings WHERE key = ?', (key,))
        if rows:
            return rows[0][0]
        return default_value
    
    def set_setting(self, key: str, value: str):
        # Essayer de mettre à jour d'abord
        self.db.execute_query('DELETE FROM settings WHERE key = ?', (key,))
        self.db.execute_query('''
            INSERT INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
    
    def get_block_size(self) -> int:
        value = self.get_setting('block_size', '20971520')  # 20MB par défaut
        return int(value)
    
    def set_block_size(self, size: int):
        self.set_setting('block_size', str(size))