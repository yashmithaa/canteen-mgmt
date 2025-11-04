import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st
from contextlib import contextmanager
import config

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        yield conn
    except Error as e:
        st.error(f" Database connection error: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

def fetch_query(query, params=None):
    try:
        with get_db_connection() as conn:
            df = pd.read_sql(query, conn, params=params)
            return df
    except Error as e:
        st.error(f" Query execution error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f" Unexpected error: {e}")
        return pd.DataFrame()

def execute_query(query, params=None, fetch_results=False):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_results:
                results = cursor.fetchall()
                conn.commit()
                cursor.close()
                return results
            
            conn.commit()
            cursor.close()
            return True
    except Error as e:
        st.error(f" Query execution error: {e}")
        return False
    except Exception as e:
        st.error(f" Unexpected error: {e}")
        return False

def call_procedure(proc_name, params=None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.callproc(proc_name, params or ())
            
            # Fetch all result sets
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            
            conn.commit()
            cursor.close()
            return results
    except Error as e:
        st.error(f" Procedure call error: {e}")
        return None
    except Exception as e:
        st.error(f" Unexpected error: {e}")
        return None

def call_function(func_name, params):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build function call
            placeholders = ', '.join(['%s'] * len(params))
            query = f"SELECT {func_name}({placeholders})"
            
            cursor.execute(query, params)
            result = cursor.fetchone()[0]
            cursor.close()
            return result
    except Error as e:
        st.error(f" Function call error: {e}")
        return None
    except Exception as e:
        st.error(f" Unexpected error: {e}")
        return None

def test_connection():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            return True, f"Connected to MariaDB version: {version}"
    except Error as e:
        return False, f"Connection failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def get_table_info(table_name):
    query = f"DESCRIBE {table_name}"
    return fetch_query(query)

def get_triggers():
    query = "SHOW TRIGGERS"
    return fetch_query(query)

def get_procedures():
    query = "SHOW PROCEDURE STATUS WHERE Db = %s"
    return fetch_query(query, (config.DB_NAME,))

def get_functions():
    query = "SHOW FUNCTION STATUS WHERE Db = %s"
    return fetch_query(query, (config.DB_NAME,))

def execute_file(file_path):
    try:
        with open(file_path, 'r') as f:
            sql_script = f.read()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Split and execute statements
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            conn.commit()
            cursor.close()
            return True
    except Exception as e:
        st.error(f" File execution error: {e}")
        return False
