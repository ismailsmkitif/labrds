import os
import socket
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import get_connection, test_connection, init_db, DB_HOST, DB_NAME, DB_PORT

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aws-learner-lab-secret-key-2026")

def get_server_metadata():
    """Mengambil metadata lokal instance EC2 untuk keperluan monitoring/display."""
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "db_host": DB_HOST,
        "db_port": DB_PORT,
        "db_name": DB_NAME
    }

@app.context_processor
def inject_metadata():
    return {"meta": get_server_metadata()}

# ----------------- READ (List Products) -----------------
@app.route("/")
def index():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    try:
        conn = get_connection(include_database=True)
        with conn.cursor() as cursor:
            query = "SELECT * FROM products WHERE 1=1"
            params = []

            if keyword:
                query += " AND (name LIKE %s OR sku LIKE %s OR description LIKE %s)"
                term = f"%{keyword}%"
                params.extend([term, term, term])

            if category:
                query += " AND category = %s"
                params.append(category)

            query += " ORDER BY id DESC"
            cursor.execute(query, params)
            products = cursor.fetchall()

            # Ambil daftar kategori unik untuk filter
            cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
            categories = [row["category"] for row in cursor.fetchall() if row.get("category")]

        conn.close()
        return render_template("index.html", products=products, categories=categories, selected_category=category, keyword=keyword)
    except Exception as e:
        error_msg = f"Koneksi ke RDS Gagal atau Tabel Belum Diinisialisasi: {str(e)}"
        return render_template("index.html", products=[], categories=[], error=error_msg)

# ----------------- CREATE -----------------
@app.route("/products/new", methods=["GET", "POST"])
def create_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", "0").strip()
        stock = request.form.get("stock", "0").strip()
        description = request.form.get("description", "").strip()

        if not name or not sku or not price:
            flash("Nama produk, SKU, dan harga wajib diisi!", "danger")
            return render_template("create.html")

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO products (name, sku, category, price, stock, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (name, sku, category, float(price), int(stock), description))
            conn.close()
            flash("Produk baru berhasil ditambahkan ke database RDS!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Gagal menambahkan produk: {str(e)}", "danger")
            return render_template("create.html")

    return render_template("create.html")

# ----------------- UPDATE -----------------
@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
        conn.close()

        if not product:
            flash("Produk tidak ditemukan!", "warning")
            return redirect(url_for("index"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            sku = request.form.get("sku", "").strip()
            category = request.form.get("category", "").strip()
            price = request.form.get("price", "0").strip()
            stock = request.form.get("stock", "0").strip()
            description = request.form.get("description", "").strip()

            conn = get_connection()
            with conn.cursor() as cursor:
                sql = """
                    UPDATE products
                    SET name=%s, sku=%s, category=%s, price=%s, stock=%s, description=%s
                    WHERE id=%s
                """
                cursor.execute(sql, (name, sku, category, float(price), int(stock), description, product_id))
            conn.close()
            flash("Data produk berhasil diperbarui!", "success")
            return redirect(url_for("index"))

        return render_template("edit.html", product=product)
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for("index"))

# ----------------- DELETE -----------------
@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.close()
        flash("Produk berhasil dihapus dari database!", "success")
    except Exception as e:
        flash(f"Gagal menghapus produk: {str(e)}", "danger")
    return redirect(url_for("index"))

# ----------------- HEALTH & SYSTEM ENDPOINTS -----------------
@app.route("/health")
def health_check():
    """Endpoint untuk health check dan audit konektivitas cloud."""
    db_ok, db_detail = test_connection()
    status = {
        "status": "healthy" if db_ok else "unhealthy",
        "ec2_instance": get_server_metadata(),
        "database": {
            "connected": db_ok,
            "version_or_error": db_detail,
            "rds_host": DB_HOST
        }
    }
    return jsonify(status), 200 if db_ok else 500

@app.route("/init-database", methods=["POST"])
def trigger_init_db():
    """Fasilitas untuk inisialisasi schema database langsung dari web UI."""
    success, message = init_db("schema.sql")
    if success:
        flash(f"Sukses Inisialisasi Database: {message}", "success")
    else:
        flash(f"Gagal Inisialisasi Database: {message}", "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Host 0.0.0.0 agar bisa diakses dari public IP EC2
    app.run(host="0.0.0.0", port=port, debug=False)

