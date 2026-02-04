#!/usr/bin/env python3
"""
Script de configuração e verificação da GUI do SmartCityOS
Verifica dependências, configuração do banco e inicia a interface
"""

import sys
import os
import subprocess
from dotenv import load_dotenv

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    required_packages = [
        'PySide6',
        'psycopg', 
        'python-dotenv',
        'pandas',
        'tabulate'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PySide6':
                import PySide6
            elif package == 'psycopg':
                import psycopg
            elif package == 'python-dotenv':
                import dotenv
            elif package == 'pandas':
                import pandas
            elif package == 'tabulate':
                import tabulate
                
            print(f"✅ {package} - OK")
            
        except ImportError:
            print(f"❌ {package} - FALTANDO")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Pacotes faltando: {', '.join(missing_packages)}")
        print("📦 Instale com: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ Todas as dependências estão instaladas!")
    return True

def check_env_config():
    """Verifica configuração das variáveis de ambiente"""
    print("\n🔧 Verificando configuração do ambiente...")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    required_env_vars = [
        'DB_NAME',
        'DB_USER', 
        'DB_PASSWORD',
        'DB_HOST'
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            # Mascarar senha para exibição
            if var == 'DB_PASSWORD':
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"✅ {var} = {display_value}")
        else:
            print(f"❌ {var} - NÃO CONFIGURADO")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("📝 Crie um arquivo .env baseado no .env.example")
        return False
    
    print("✅ Configuração do ambiente OK!")
    return True

def test_database_connection():
    """Testa a conexão com o banco de dados"""
    print("\n🗄️ Testando conexão com o banco de dados...")
    
    try:
        import psycopg as psy
        from dotenv import load_dotenv
        
        load_dotenv()
        
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT', '5432')
        
        conn_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
        
        with psy.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"✅ Conectado ao PostgreSQL!")
                print(f"📊 Versão: {version.split(',')[0]}")
                
                # Verificar se as tabelas existem
                cur.execute("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cur.fetchone()[0]
                print(f"📋 Tabelas encontradas: {table_count}")
                
                return True
                
    except Exception as e:
        print(f"❌ Erro de conexão: {str(e)}")
        print("\n💡 Verifique:")
        print("   - Se o PostgreSQL está rodando")
        print("   - Se o banco de dados existe")
        print("   - Se as credenciais estão corretas")
        print("   - Se o arquivo .env está configurado")
        return False

def create_env_file():
    """Cria arquivo .env se não existir"""
    if not os.path.exists('.env'):
        print("\n📝 Criando arquivo .env de exemplo...")
        
        example_content = """# Configurações do Banco de Dados PostgreSQL
DB_NAME=smart_city_os
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432

# URL de conexão completa (opcional)
DB_POOL_URL=postgresql+psycopg2://postgres:sua_senha_aqui@localhost:5432/smart_city_os

# Configurações da Aplicação
SECRET_KEY=chave-secreta-da-aplicacao
FLASK_DEBUG=True
FLASK_ENV=development
"""
        
        with open('.env', 'w') as f:
            f.write(example_content)
            
        print("✅ Arquivo .env criado!")
        print("⚠️ Edite o arquivo .env com suas configurações do PostgreSQL")
        return False
    
    return True

def main():
    """Função principal"""
    print("🚀 SmartCityOS GUI - Configuração")
    print("=" * 50)
    
    # Verificar dependências
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n❌ Dependências faltando. Instale-as primeiro.")
        input("Pressione Enter para sair...")
        return
    
    # Criar arquivo .env se necessário
    env_created = create_env_file()
    if not env_created:
        input("\nPressione Enter para sair e editar o arquivo .env...")
        return
    
    # Verificar configuração do ambiente
    env_ok = check_env_config()
    if not env_ok:
        print("\n❌ Configure as variáveis de ambiente primeiro.")
        input("Pressione Enter para sair...")
        return
    
    # Testar conexão com banco
    db_ok = test_database_connection()
    if not db_ok:
        print("\n❌ Não foi possível conectar ao banco de dados.")
        input("Pressione Enter para sair...")
        return
    
    print("\n✅ Tudo pronto para iniciar a GUI!")
    print("🖥️ Iniciando interface gráfica...")
    
    # Iniciar a GUI
    try:
        from gui.qt_app import run
        run()
        
    except Exception as e:
        print(f"❌ Erro ao iniciar GUI: {str(e)}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
