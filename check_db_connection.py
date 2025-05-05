import os
import sys
import psycopg2
from urllib.parse import urlparse

def check_database_connection():
    """
    Test the database connection using the DATABASE_URL environment variable
    """
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        return False
    
    # Fix common URL format issues
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Testing connection to: {database_url[:10]}...{database_url[-10:]}")
    
    try:
        # Parse the connection string
        result = urlparse(database_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        
        print(f"Connecting to hostname: {hostname}")
        print(f"Using database: {database}")
        print(f"With username: {username}")
        print(f"Port: {port}")
        
        # Try to connect
        connection = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port,
            connect_timeout=10,
            sslmode="require"
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        connection.close()
        
        print(f"SUCCESS: Connected to {database} - PostgreSQL version: {db_version[0]}")
        return True
    
    except Exception as e:
        print(f"ERROR: Database connection failed - {str(e)}")
        return False

if __name__ == "__main__":
    success = check_database_connection()
    sys.exit(0 if success else 1)
