#!/usr/bin/env python3
"""
Script para inicializar o banco de dados
"""

import sqlite3
import os

def init_database():
    print("=== Inicializando Banco de Dados ===")
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Criar tabela para tutoriais assistidos
        print("Criando tabela 'tutorials_watched'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutorials_watched (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tutorial_id TEXT NOT NULL,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Criar tabela para músicas masterizadas
        print("Criando tabela 'mastered_songs'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mastered_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                mastered_filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Criar tabela para downloads
        print("Criando tabela 'downloads'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Criar tabela para solicitações de ghost producer
        print("Criando tabela 'ghost_producer_requests'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ghost_producer_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                genre TEXT NOT NULL,
                description TEXT,
                budget REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Banco de dados inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    init_database()
