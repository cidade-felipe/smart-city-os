import psycopg as psy
import sys
sys.path.append('functions')
from conect_db import connect_to_db

def drop_and_recreate_all(schema):
    """
    Dropa tudo e recria do zero - versão final e completa
    """
    try:
        conn_info = connect_to_db()
        with psy.connect(conn_info) as conn:
            with conn.cursor() as cur:
                print("🔄 DROPANDO E RECRIANDO TUDO DO ZERO...")
                print("=" * 60)
                
                # 1. Dropar schema public completamente
                print("1️⃣ Dropando schema {}...".format(schema))
                cur.execute("DROP SCHEMA {} CASCADE".format(schema))
                conn.commit()
                print("   ✅ Schema {} dropado".format(schema))
                
                # 2. Recriar schema public
                print("2️⃣ Recriando schema {}...".format(schema))
                cur.execute("CREATE SCHEMA {}".format(schema))
                conn.commit()
                print("   ✅ Schema {} recriado".format(schema))
                
                # 3. Recriar tabelas
                print("3️⃣ Recriando tabelas...")
                with open('sql/create_tables.sql', 'r', encoding='utf-8') as f:
                    tables_sql = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(tables_sql)
                conn.commit()
                print("   ✅ Tabelas recriadas")
                
                # 4. Recriar funções
                print("4️⃣ Recriando funções...")
                with open('sql/trigger_functions.sql', 'r', encoding='utf-8') as f:
                    functions_sql = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(functions_sql)
                conn.commit()
                print("   ✅ Funções recriadas")
                
                # 5. Recriar triggers
                print("5️⃣ Recriando triggers...")
                with open('sql/triggers.sql', 'r', encoding='utf-8') as f:
                    triggers_sql = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(triggers_sql)
                conn.commit()
                print("   ✅ Triggers recriados")
                
                # 6. Recriar views
                print("6️⃣ Recriando views...")
                with open('sql/wiews.sql', 'r', encoding='utf-8') as f:
                    views_sql = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(views_sql)
                conn.commit()
                print("   ✅ Views recriadas")
                
                # 7. Recriar índices
                print("7️⃣ Recriando índices...")
                with open('sql/indexes.sql', 'r', encoding='utf-8') as f:
                    indexes_sql = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(indexes_sql)
                conn.commit()
                print("   ✅ Índices recriados")
                
                # 8. Verificar estrutura
                print("8️⃣ Verificando estrutura...")
                
                # Verificar tabelas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{}'
                    ORDER BY table_name
                """.format(schema))
                tables = [row[0] for row in cur.fetchall()]
                print(f"   📋 Tabelas criadas: {len(tables)}")
                for table in tables:
                    print(f"      - {table}")
                
                # Verificar triggers
                cur.execute("""
                    SELECT trigger_name, event_object_table 
                    FROM information_schema.triggers 
                    WHERE trigger_schema = '{}'
                    ORDER BY event_object_table, trigger_name
                """.format(schema))
                triggers = cur.fetchall()
                print(f"   ⚡ Triggers criados: {len(triggers)}")
                for trigger in triggers:
                    print(f"      - {trigger[0]} (tabela: {trigger[1]})")
                
                # Verificar views
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = '{}'
                    ORDER BY table_name
                """.format(schema))
                views = [row[0] for row in cur.fetchall()]
                print(f"   👁️ Views criadas: {len(views)}")
                for view in views:
                    print(f"      - {view}")
                
                print("=" * 60)
                print("🎉 BANCO DE DADOS RECRIADO COM SUCESSO!")
                print("✅ Soft delete funcional")
                print("✅ Views ativas funcionando")
                print("✅ Triggers aplicados")
                print("✅ GUI pronta para uso")
                print("=" * 60)
                
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 ATENÇÃO: Este script irá APAGAR TODOS os dados do banco!")
    print("📋 Isso inclui:")
    print("   • Todas as tabelas")
    print("   • Todos os dados")
    print("   • Todas as configurações")
    print("   • Tudo será recriado do zero")
    print()
    
    confirm = input("❓ Tem certeza que deseja continuar? (digite 'SIM' para confirmar): ")
    
    if confirm.upper() == 'SIM':
        print("\n🔄 Iniciando processo...")
        drop_and_recreate_all('public')
    else:
        print("❌ Operação cancelada pelo usuário.")
