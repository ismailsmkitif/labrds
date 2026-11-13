#!/bin/bash
# ==============================================================================
# Script Otomasi Deployment E-Commerce CRUD di AWS EC2
# Kompatibel dengan: Amazon Linux 2023 / Ubuntu 22.04 LTS
# ==============================================================================

set -e

echo "=== [1/5] Memperbarui Sistem & Menginstal Dependensi ==="
if [ -f /etc/amazon-linux-release ]; then
    echo "Terdeteksi Amazon Linux 2023"
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip git mariadb105
    CURRENT_USER="ec2-user"
elif [ -f /etc/lsb-release ]; then
    echo "Terdeteksi Ubuntu Linux"
    sudo apt update -y
    sudo apt install -y python3 python3-pip python3-venv git mysql-client
    CURRENT_USER="ubuntu"
else
    echo "OS tidak dikenali secara spesifik, menggunakan python3 default..."
    CURRENT_USER=$(whoami)
fi

echo "=== [2/5] Menyiapkan Python Virtual Environment ==="
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [3/5] Memeriksa File Konfigurasi .env ==="
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "File .env dibuat dari .env.example."
        echo "PERINGATAN: Pastikan mengedit .env dan mengisi DB_HOST dengan RDS Endpoint Anda!"
    fi
fi

echo "=== [4/5] Menguji Koneksi ke Database ==="
python3 -c "
import db
success, msg = db.test_connection()
if success:
    print('Koneksi ke RDS MySQL Berhasil! Versi MySQL:', msg)
else:
    print('PERHATIAN: Koneksi ke RDS gagal:', msg)
"

echo "=== [5/5] Selesai! ==="
echo "Untuk menjalankan server secara manual di port 5000:"
echo "   source venv/bin/activate && python3 app.py"
echo ""
echo "Atau jalankan di background port 80 dengan gunicorn:"
echo "   sudo ./venv/bin/gunicorn -w 3 -b 0.0.0.0:80 app:app"

