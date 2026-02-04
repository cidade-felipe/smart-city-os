def drop_tables(conn_info, schema):
    import psycopg
    from psycopg import sql

    try:
        with psycopg.connect(conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = %s;
                    """,
                    (schema,)
                )

                droped_tables ={row[0] for row in cur.fetchall()}

                for table_name in droped_tables:
                    query = sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE;").format(
                        sql.Identifier(schema),
                        sql.Identifier(table_name)
                    )
                    cur.execute(query)
                return list(droped_tables)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    
    from conect_db import connect_to_db
    
    conn_info = connect_to_db()
    delete_tables = drop_tables(conn_info,'public')
    for table in delete_tables:
        print(f"Dropping table: {table}")
