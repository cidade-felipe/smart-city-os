def insert_generic(conn_info,table,schema,values,return_columns=None):
    """
    Insert test data into the SmartCityOS database
    """
    try:
        
        import psycopg as psy
        with psy.connect(conn_info) as conn:
            with conn.cursor() as cur:
                # TODO: Implement test data insertion
                # Example: insert a test app_user
                cur.execute("""
                    INSERT INTO {}.{} (first_name, last_name, cpf, birth_date, email, phone, address, username, password_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING {}
                """.format(schema, table, ", ".join(return_columns) if return_columns else "*"), values)
                result = cur.fetchone()
                if return_columns:
                    print(f"Inserted test record with columns: {dict(zip(return_columns, result))}")
    except Exception as e:
        print(f"Error inserting test data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()






if __name__ == "__main__":
    from conect_db import connect_to_db 
    conn_info = connect_to_db()
    insert_test_data(conn_info, 'public')
