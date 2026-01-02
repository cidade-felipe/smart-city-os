def create_tables(conn_info, sql_file, schema):
    import psycopg as psy
    try:
        with psy.connect(conn_info) as conn:
            with conn.cursor() as cur:

                # Tabelas existentes antes
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = '{}'
                """.format(schema))
                before_tables = {row[0] for row in cur.fetchall()}

                # Executa o script
                with open(sql_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read())

                conn.commit()

                # Tabelas existentes depois
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = '{}'
                """.format(schema))
                after_tables = {row[0] for row in cur.fetchall()}

                # Apenas as novas
                created_tables = sorted(after_tables - before_tables)

                return created_tables

    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

if __name__ == "__main__":
    from conect_db import connect_to_db
    file = r"C:\Users\felip\OneDrive\git_work\smart-city-os\sql\create_tables.sql"
    conn_info = connect_to_db()
    created = create_tables(conn_info, file,'public')
    print(f"Created tables: {created}")

