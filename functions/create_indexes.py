def create_all_indexes(conn_info, file_path):
    """
    Create database indexes for Smart City OS
    """
    
    try:
        import psycopg as psy
        from psycopg.rows import dict_row
        with psy.connect(conn_info, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Read and execute trigger_functions.sql
                with open(file_path, 'r') as f:
                    indexes = f.read()
                
                cur.execute(indexes)
    
        print("Database indexes created successfully")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\index.sql"
    conn_info = connect_to_db()
    create_all_indexes(conn_info, file)
