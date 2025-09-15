#!/usr/bin/env python3
"""
Script de teste para verificar o banco de dados
"""

import sqlite3
import os

def test_database():
    print("=== Teste do Banco de Dados ===")
    
    # Verificar se o arquivo existe
    if not os.path.exists('users.db'):
        print("❌ Arquivo users.db não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        print("\n📋 Tabelas existentes:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ Nenhuma tabela encontrada!")
            return False
        
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        # Verificar estrutura da tabela users
        print("\n👥 Estrutura da tabela 'users':")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar se há usuários
        print("\n👤 Usuários cadastrados:")
        cursor.execute("SELECT id, nome, email FROM users")
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"  - ID: {user[0]}, Nome: {user[1]}, Email: {user[2]}")
        else:
            print("  ℹ️  Nenhum usuário cadastrado")
        
        # Verificar outras tabelas
        for table_name in ['tutorials_watched', 'mastered_songs', 'downloads', 'ghost_producer_requests']:
            if table_name in [t[0] for t in tables]:
                print(f"\n📊 Dados da tabela '{table_name}':")
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - Total de registros: {count}")
                    
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        sample = cursor.fetchall()
                        print(f"  - Amostra dos dados:")
                        for row in sample:
                            print(f"    {row}")
                except Exception as e:
                    print(f"  ❌ Erro ao consultar {table_name}: {str(e)}")
        
        conn.close()
        print("\n✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao testar banco de dados: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_database()
