import os
import pymysql
from pymysql.constants import CLIENT
from dotenv import load_dotenv

# Muat environment variable dari file .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

def get_connection(include_database=True):
    """
    Membuka koneksi ke MySQL RDS.
    include_database=False digunakan saat inisialisasi database (sebelum database dibuat).
    """
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME if include_database else None,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            autocommit=True,
            client_flag=CLIENT.MULTI_STATEMENTS
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"[ERROR] Gagal terhubung ke database RDS ({DB_HOST}:{DB_PORT}): {e}")
        raise e

def test_connection():
    """Menguji koneksi ke server RDS dan mengembalikan status."""
    try:
        conn = get_connection(include_database=False)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version;")
            row = cursor.fetchone()
        conn.close()
        return True, row.get("version", "Unknown")
    except Exception as e:
        return False, str(e)

def init_db(sql_file_path="schema.sql"):
    """
    Mengeksekusi file schema.sql ke MySQL RDS untuk membuat database & tabel.
    """
    if not os.path.exists(sql_file_path):
        return False, f"File {sql_file_path} tidak ditemukan!"

    try:
        # Koneksi tanpa database name terlebih dahulu
        conn = get_connection(include_database=False)
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        with conn.cursor() as cursor:
            # PyMySQL dengan CLIENT.MULTI_STATEMENTS dapat mengeksekusi multiple SQL
            cursor.execute(sql_script)

        conn.close()
        return True, "Database dan tabel berhasil diinisialisasi!"
    except Exception as e:
        return False, str(e)

