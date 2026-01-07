import re

def view_names_from_sql(file_path):
    import re
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        pattern = re.compile(
            r'CREATE\s+VIEW\s+("?[\w]+"?)',
            re.IGNORECASE
        )
        views = pattern.findall(sql)
        views = [t.replace('"', '') for t in views]
        return views
    except Exception as e:
        print(f"Erro ao ler o arquivo SQL: {e}")
        return None
def create_all_views(conn_info, file_path, schema):
    """
    Create database views for Smart City OS
    """
    
    try:
        import psycopg as psy
        from psycopg.rows import dict_row
        with psy.connect(conn_info, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Read and execute trigger_functions.sql
                with open(file_path, 'r') as f:
                    cur.execute(f.read().replace('SCHEMA_NAME', schema))

                cur.execute("""
                SELECT viewname
                FROM pg_views
                WHERE schemaname = '{}';
                """.format(schema))
                views = {row['viewname'] for row in cur.fetchall()}
                return list(views)     
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\wiews.sql"
    conn_info = connect_to_db()
    views = create_all_views(conn_info, file, 'db')
    for view in views:
      print(f"Created view: {view}")