
import urllib.parse

sqlserver_config = {
    "server": "host",
    "database": "your_db_name",
    "user": "your_db_user",
    "password": "your_db_password"
}

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={sqlserver_config['server']};"
    f"DATABASE={sqlserver_config['database']};"
    f"UID={sqlserver_config['user']};"
    f"PWD={sqlserver_config['password']}"
)

DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

# --- SMTP Configuration ---
SMTP_SERVER = "smtp_server"
SMTP_PORT = 25
SMTP_USERNAME = "user@email.email"
SMTP_USE_TLS = False

# --- Report Configuration ---
RECIPIENT_EMAIL = "your.email@email.email"
SENDER_EMAIL = SMTP_USERNAME
