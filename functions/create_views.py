def create_all_views(conn_info, file_path):
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
                     views = f.read()
                
                cur.execute(views)
    
        print("Database views created successfully")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\wiews.sql"
    conn_info = connect_to_db()
    create_all_views(conn_info, file)