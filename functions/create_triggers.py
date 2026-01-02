def create_all_triggers(conn_info,file_path_func,file_path_trig):
    """
    Create database triggers for Smart City OS
    """
    try:
        import psycopg as psy
        from psycopg.rows import dict_row
        with psy.connect(conn_info, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Read and execute trigger_functions.sql
                with open(file_path_func, 'r') as f:
                    trigger_functions_sql = f.read()
                
                # Read and execute triggers.sql
                with open(file_path_trig, 'r') as f: 
                    triggers_sql = f.read()
                
                # Execute the SQL statements
                cur.execute(trigger_functions_sql)
                cur.execute(triggers_sql)
        
        print("Database triggers created successfully")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        conn.rollback()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file_func = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\trigger_functions.sql"
    file_trig = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\triggers.sql"
    conn_info = connect_to_db()
    create_all_triggers(conn_info, file_func, file_trig)

