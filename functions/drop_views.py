
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


def drop_views(conn_info, view_names):
   import psycopg as psy
   try:
      with psy.connect(conn_info) as conn:
         with conn.cursor() as cur:
            view_names = ', '.join(view_names)
            query = 'DROP VIEW {} CASCADE;'.format(view_names)
            cur.execute(query)
            conn.commit()
   except Exception as e:
      print(f"Error: {e}")
      import traceback
      traceback.print_exc()
      conn.rollback()

if __name__ == "__main__":
    
    from conect_db import connect_to_db
    
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\wiews.sql"
    view_names = view_names_from_sql(file)
    conn_info = connect_to_db()
    drop_views(conn_info, view_names)
