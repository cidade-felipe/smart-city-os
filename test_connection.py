#!/usr/bin/env python3
"""
Teste simples de conexão com o banco de dados
"""

import os
import sys
from dotenv import load_dotenv
import psycopg as psy

# Carregar variáveis de ambiente
load_dotenv()

def test_connection():
    """Testa a conexão usando a mesma lógica da GUI"""
    try:
        # Obter configurações (mesma lógica do connect_to_db)
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        
        print("🔍 Verificando configurações...")
        print(f"   DB_NAME: {'✅' if DB_NAME else '❌'} {DB_NAME or 'NÃO CONFIGURADO'}")
        print(f"   DB_USER: {'✅' if DB_USER else '❌'} {DB_USER or 'NÃO CONFIGURADO'}")
        print(f"   DB_HOST: {'✅' if DB_HOST else '❌'} {DB_HOST or 'NÃO CONFIGURADO'}")
        print(f"   DB_PASSWORD: {'✅' if DB_PASSWORD else '❌'} {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'NÃO CONFIGURADO'}")
        
        if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST]):
            print("\n❌ Variáveis de ambiente faltando!")
            return False
        
        # String de conexão (mesma lógica)
        conn_info = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST}"
        print(f"\n📡 String de conexão: {conn_info.replace(DB_PASSWORD, '*' * len(DB_PASSWORD))}")
        
        # Testar conexão
        print("\n🗄️ Testando conexão...")
        with psy.connect(conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"✅ Conectado com sucesso!")
                print(f"📊 Versão PostgreSQL: {version.split(',')[0]}")
                
                # Verificar tabelas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cur.fetchall()]
                print(f"📋 Tabelas encontradas ({len(tables)}): {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
                
                return True
                
    except Exception as e:
        print(f"\n❌ Erro de conexão: {str(e)}")
        print("\n💡 Verifique:")
        print("   1. Se o PostgreSQL está rodando")
        print("   2. Se o banco de dados existe")
        print("   3. Se as credenciais estão corretas")
        print("   4. Se o arquivo .env está configurado")
        return False

if __name__ == "__main__":
    print("🚀 SmartCityOS - Teste de Conexão")
    print("=" * 50)
    
    success = test_connection()
    
    if success:
        print("\n✅ Conexão testada com sucesso! A GUI deve funcionar.")
    else:
        print("\n❌ Problemas encontrados. Corrija antes de usar a GUI.")
    
    input("\nPressione Enter para sair...")
