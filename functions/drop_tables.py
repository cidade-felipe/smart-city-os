def table_names_from_sql(file_path):
    
    import re
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        pattern = re.compile(
            r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+("?[\w]+"?)',
            re.IGNORECASE
        )
        tables = pattern.findall(sql)
        tables = [t.replace('"', '') for t in tables]
        return tables
    except Exception as e:
        print(f"Erro ao ler o arquivo SQL: {e}")
        return None

def drop_tables(conn_info, table_names):
    
    import psycopg as psy
    try:
      with psy.connect(conn_info) as conn:
         with conn.cursor() as cur:
            table_names = ', '.join(table_names)
            query = 'DROP TABLE IF EXISTS {} CASCADE;'.format(table_names)
            cur.execute(query)
    except Exception as e:
      print(f"Error: {e}")
      import traceback
      traceback.print_exc()
      conn.rollback()

if __name__ == "__main__":
    
    from conect_db import connect_to_db
    
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\create_tables.sql"
    table_names = table_names_from_sql(file)
    conn_info = connect_to_db()
    drop_tables(conn_info, table_names)
