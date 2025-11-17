import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st
from contextlib import contextmanager
import config

def get_current_db_user():
    """Get the currently logged-in database user from session state"""
    if 'db_user' not in st.session_state:
        # Default to a view-only user until credentials are provided
        default_user = 'canteen_readonly'
        default_pwd = config.DB_USERS.get(default_user, {}).get('password', config.DB_PASSWORD)
        st.session_state.db_user = default_user
        st.session_state.db_password = default_pwd
    return st.session_state.db_user, st.session_state.db_password

def set_db_user(username, password):
    """Set the database user for the session"""
    st.session_state.db_user = username
    st.session_state.db_password = password


def verify_db_credentials(username, password, timeout=5):
    """Attempt to connect to the DB using the provided credentials.

    Returns (True, message) on success, (False, error_message) on failure.
    This does not modify session state.
    """
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=username,
            password=password,
            database=config.DB_NAME,
            port=config.DB_PORT,
            connection_timeout=timeout
        )
        if conn and conn.is_connected():
            conn.close()
            return True, f"Credentials valid for {username}"
        return False, "Unable to establish connection"
    except Error as e:
        # Provide clearer feedback for common auth errors
        return False, str(e)

def get_user_role():
    """Get the role of the current database user"""
    username, _ = get_current_db_user()
    
    # Map legacy 'admin' literal to canteen_admin for role lookup
    if username in ('admin', 'canteen_admin'):
        return config.ROLE_PERMISSIONS.get('canteen_admin', {})
    
    return config.ROLE_PERMISSIONS.get(username, {})

def check_permission(permission_type):
    """Check if current user has a specific permission"""
    role = get_user_role()
    return role.get(permission_type, False)

def get_allowed_pages():
    """Get list of pages the current user can access"""
    role = get_user_role()
    return role.get('pages', [])

@contextmanager
def get_db_connection():
    """Get database connection with current user credentials"""
    conn = None
    try:
        username, password = get_current_db_user()
        
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=username,
            password=password,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        yield conn
    except Error as e:
        st.error(f"Database connection error: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

def fetch_query(query, params=None):
    """Execute SELECT query and return results as DataFrame"""
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
    """Execute INSERT, UPDATE, DELETE queries"""
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
        st.error(f"Query execution error: {e}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return False

def call_procedure(proc_name, params=None):
    """Call stored procedure"""
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
        st.error(f"Procedure call error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def call_function(func_name, params):
    """Call stored function"""
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
        st.error(f"Function call error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # Get current user
            cursor.execute("SELECT CURRENT_USER()")
            current_user = cursor.fetchone()[0]
            
            cursor.close()
            return True, f"Connected as {current_user} | MariaDB {version}"
    except Error as e:
        return False, f"Connection failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def get_table_info(table_name):
    """Get table structure"""
    query = f"DESCRIBE {table_name}"
    return fetch_query(query)

def get_triggers():
    """Get all triggers"""
    query = "SHOW TRIGGERS"
    return fetch_query(query)

def get_procedures():
    """Get all procedures"""
    query = "SHOW PROCEDURE STATUS WHERE Db = %s"
    return fetch_query(query, (config.DB_NAME,))

def get_functions():
    """Get all functions"""
    query = "SHOW FUNCTION STATUS WHERE Db = %s"
    return fetch_query(query, (config.DB_NAME,))

def execute_file(file_path):
    """Execute SQL file"""
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
        st.error(f"File execution error: {e}")
        return False