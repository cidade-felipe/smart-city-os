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

def create_tables(conn_info, sql_file, schema):
    import psycopg as psy
    try:
        with psy.connect(conn_info) as conn:
            with conn.cursor() as cur:
                with open(sql_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read().replace('SCHEMA_NAME', schema))
                
                # Tabelas existentes antes
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = '{}'
                """.format(schema))
                created_tables = {row[0] for row in cur.fetchall()}

                return list(created_tables)

    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import re
    from conect_db import connect_to_db
    file = r"sql\create_tables.sql"
    conn_info = connect_to_db()
    created_tables = create_tables(conn_info, file,'public')
    for table in created_tables:
        print(f'Creating table: {table}')
    

