def triggers_names(file_path): 
    import re
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()
        pattern = re.compile(
            r'CREATE\s+TRIGGER\s+IF\s+NOT\s+EXISTS\s+("?[\w]+"?)',
            re.IGNORECASE
        )
        triggers = pattern.findall(sql)
        triggers = [t.replace('"', '') for t in triggers]
        return triggers
    except Exception as e:
        print(f"Erro ao ler o arquivo SQL: {e}")
        return None

def create_all_triggers(conn_info,file_path_func,file_path_trig, schema):
    """
    Create database triggers for Smart City OS
    """
    try:
        import psycopg as psy
        from psycopg.rows import dict_row
        with psy.connect(conn_info, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                with open(file_path_func, 'r') as f:
                    functions = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(functions)
                with open(file_path_trig, 'r') as f: 
                    triggers = f.read().replace('SCHEMA_NAME', schema)
                cur.execute(triggers)
                return triggers_names(file_path_trig)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file_func = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\trigger_functions.sql"
    file_trig = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\triggers.sql"
    conn_info = connect_to_db()
    print(create_all_triggers(conn_info, file_func, file_trig, 'db'))

