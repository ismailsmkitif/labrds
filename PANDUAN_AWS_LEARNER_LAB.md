# Panduan Lengkap Proyek CRUD Database 2-Tier di AWS Learner Lab
**Arsitektur:** Amazon VPC + EC2 (Public Subnet) + RDS MySQL (Private Subnet)  
**Studi Kasus:** Sistem Manajemen Katalog Produk E-Commerce  

---

## 1. Arsitektur Jaringan & Alur Sistem

Proyek ini menerapkan arsitektur *2-Tier Web Application* berstandar industri dengan prinsip *defense-in-depth*:
- **Web/Application Layer (EC2):** Diletakkan di **Public Subnet** agar dapat menerima lalu lintas web (HTTP port 80/5000) dari pengguna internet dan akses manajemen (SSH port 22).
- **Database Layer (RDS):** Diletakkan di **Private Subnet** tanpa alokasi Public IP dan tanpa Internet Gateway. RDS hanya dapat diakses secara internal melalui lalu lintas VPC oleh EC2 via port 3306.

```
                  [ PENGGUNA INTERNET ]
                            │ (HTTP :80 / SSH :22)
                            ▼
               [ Internet Gateway (IGW) ]
                            │
┌───────────────────────────┼────────────────────────────────────────┐
│ Amazon VPC (10.0.0.0/16)  │                                        │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ PUBLIC SUBNET 1 (10.0.1.0/24 - us-east-1a)                   │  │
│  │                                                              │  │
│  │   [ Amazon EC2 Instance (Web Server: Flask / Gunicorn) ]     │  │
│  │   • Security Group: ec2-web-sg                               │  │
│  │     - Inbound: HTTP (80), Port 5000, SSH (22) from anywhere  │  │
│  │     - Public IP: Ditugaskan otomatis                         │  │
│  └───────────────────────────────┬──────────────────────────────┘  │
│                                  │                                 │
│                    VPC Internal Routing                            │
│                    (MySQL Port 3306)                               │
│                                  │                                 │
│  ┌───────────────────────────────▼──────────────────────────────┐  │
│  │ PRIVATE SUBNET 1 (10.0.11.0/24 - us-east-1a)                 │  │
│  │ PRIVATE SUBNET 2 (10.0.12.0/24 - us-east-1b) [Subnet Group]  │  │
│  │                                                              │  │
│  │   [ Amazon RDS MySQL (db.t3.micro) ]                         │  │
│  │   • Security Group: rds-mysql-sg                             │  │
│  │     - Inbound: MySQL (3306) HANYA dari ec2-web-sg            │  │
│  │   • Publicly Accessible: NO (Terisolasi total dari Internet) │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Catatan Khusus Lingkungan AWS Learner Lab

> [!IMPORTANT]
> AWS Learner Lab memiliki batasan dan kebijakan khusus yang wajib dipahami agar saldo kredit \$100 tidak cepat habis dan pengerjaan tidak mengalami kendala:

1. **Aturan DB Subnet Group RDS:**
   AWS RDS mewajibkan minimal **2 Subnet pada Availability Zone (AZ) berbeda** dalam sebuah DB Subnet Group (contoh: satu di `us-east-1a` dan satu di `us-east-1b`). Jika hanya membuat 1 subnet private, pembuatan RDS akan ditolak.
2. **HINDARI Menggunakan NAT Gateway! (Hemat Biaya):**
   Di tutorial umum, subnet private sering dihubungkan ke NAT Gateway. Biaya NAT Gateway sekitar **\$0.045/jam (~\$32/bulan)**. Jika dibiarkan menyala di Learner Lab, saldo \$100 Anda akan terkuras dalam beberapa minggu!  
   *Kabar baik:* Database RDS **TIDAK memerlukan akses internet keluar (outbound internet)**. Komunikasi antara EC2 ke RDS berlangsung via internal routing VPC. Maka pilih **NAT Gateway: None**.
3. **Session Timeout 4 Jam:**
   Sesi Learner Lab otomatis berhenti (*stopped*) setelah 4 jam. Saat sesi di-*Start* kembali:
   - Public IP instance EC2 dapat berubah (kecuali menggunakan Elastic IP).
   - Pastikan cek kembali Public IPv4 EC2 Anda di AWS Console setelah memulai lab baru.
4. **IAM Role:**
   Learner Lab melarang pembuatan IAM Role baru secara bebas. Jika membutuhkan role pada EC2 atau layanan lain, selalu pilih role bawaan bernama **`LabRole`**.
5. **Pilihan Tipe Instance:**
   - EC2: Pilih `t2.micro` atau `t3.micro` (Amazon Linux 2023 atau Ubuntu 22.04 LTS).
   - RDS: Pilih `db.t3.micro` atau `db.t4g.micro`, Single-AZ (Jangan centang Multi-AZ untuk menghemat biaya).

---

## 3. Langkah-Langkah Pengerjaan (Step-by-Step)

### LANGKAH 1: Mempersiapkan Jaringan Amazon VPC

Gunakan fitur **VPC and more** pada konsol AWS untuk membuat seluruh topologi jaringan secara otomatis dalam 1 menit tanpa repot membuat subnet satu per satu:

1. Buka konsol **VPC** di AWS Learner Lab.
2. Klik tombol **Create VPC**.
3. Pilih opsi **VPC and more** (di bagian *Resources to create*).
4. Konfigurasikan form berikut:
   - **Name tag auto-generation:** `ecommerce-vpc`
   - **IPv4 CIDR block:** `10.0.0.0/16`
   - **Number of Availability Zones (AZs):** `2` (Pilih 2 AZ, misal `us-east-1a` dan `us-east-1b`)
   - **Number of public subnets:** `2`
   - **Number of private subnets:** `2`
   - **NAT gateways ($):** Pilih **None** *(Sangat penting untuk menghemat budget Learner Lab!)*
   - **VPC Endpoints:** Pilih **None**
   - **DNS hostnames:** Centang `Enable DNS hostnames`
   - **DNS resolution:** Centang `Enable DNS resolution`
5. Klik **Create VPC** dan tunggu proses pembuatan selesai.

---

### LANGKAH 2: Konfigurasi Security Group

Kita akan membuat 2 Security Group: satu untuk EC2 (Web) dan satu untuk RDS (Database).

#### A. Buat Security Group untuk EC2 (`ec2-web-sg`)
1. Di menu kiri konsol VPC, pilih **Security Groups** > Klik **Create security group**.
2. **Security group name:** `ec2-web-sg`
3. **Description:** `Security Group untuk Web Server EC2 E-Commerce`
4. **VPC:** Pilih `ecommerce-vpc` yang baru dibuat.
5. **Inbound rules:**
   - Rule 1: Type: `HTTP`, Port: `80`, Source: `Anywhere-IPv4` (`0.0.0.0/0`)
   - Rule 2: Type: `Custom TCP`, Port: `5000`, Source: `Anywhere-IPv4` (`0.0.0.0/0`) *(untuk testing langsung)*
   - Rule 3: Type: `SSH`, Port: `22`, Source: `Anywhere-IPv4` (`0.0.0.0/0`) atau `My IP`
6. **Outbound rules:** Biarkan default (`All traffic` ke `0.0.0.0/0`).
7. Klik **Create security group**.

#### B. Buat Security Group untuk RDS (`rds-mysql-sg`)
1. Klik **Create security group** lagi.
2. **Security group name:** `rds-mysql-sg`
3. **Description:** `Security Group untuk Database RDS MySQL di Private Subnet`
4. **VPC:** Pilih `ecommerce-vpc`.
5. **Inbound rules:**
   - Type: `MYSQL/Aurora`, Port: `3306`
   - Source: Klik kolom Source, ketik `sg-` lalu pilih **`ec2-web-sg`** (HANYA izinkan dari EC2 Security Group, **JANGAN** pilih 0.0.0.0/0!).
6. **Outbound rules:** Biarkan default.
7. Klik **Create security group**.

---

### LANGKAH 3: Pembuatan DB Subnet Group & RDS MySQL di Private Subnet

#### A. Buat DB Subnet Group
1. Buka layanan **RDS** pada AWS Console.
2. Pada menu kiri, pilih **Subnet groups** > Klik **Create DB subnet group**.
3. **Name:** `ecommerce-db-subnet-group`
4. **Description:** `Subnet group private untuk RDS MySQL`
5. **VPC:** Pilih `ecommerce-vpc`.
6. **Add subnets:**
   - **Availability Zones:** Pilih 2 AZ yang sesuai dengan VPC Anda (misal `us-east-1a` dan `us-east-1b`).
   - **Subnets:** Centang 2 subnet yang merupakan **Private Subnet** (Cek CIDR `10.0.11.0/24` dan `10.0.12.0/24` atau nama subnet private dari Langkah 1).
7. Klik **Create**.

#### B. Buat Instance RDS MySQL
1. Pada menu kiri RDS, pilih **Databases** > Klik **Create database**.
2. **Choose a database creation method:** `Standard create`.
3. **Engine options:** Pilih **MySQL** (Engine Version: `MySQL 8.0.x`).
4. **Templates:** Pilih **Free Tier**.
5. **Settings:**
   - **DB instance identifier:** `ecommerce-mysql-db`
   - **Master username:** `admin`
   - **Master password:** `Admin123456!` *(Catat password ini!)*
   - **Confirm password:** `Admin123456!`
6. **Instance configuration:**
   - **DB instance class:** `db.t3.micro` (atau `db.t4g.micro`)
7. **Storage:**
   - **Storage type:** `General Purpose SSD (gp2 atau gp3)`
   - **Allocated storage:** `20` GiB
   - **Storage autoscaling:** Matikan centang `Enable storage autoscaling` (opsional, untuk mencegah lonjakan biaya).
8. **Connectivity (SANGAT PENTING):**
   - **Virtual private cloud (VPC):** Pilih `ecommerce-vpc`.
   - **DB subnet group:** Pilih `ecommerce-db-subnet-group`.
   - **Public access:** Pilih **No** *(Memastikan database berada di private subnet dan tidak terekspos ke internet)*.
   - **VPC security group (firewall):**
     - Pilih **Choose existing**.
     - Hapus `default` security group.
     - Pilih **`rds-mysql-sg`**.
   - **Availability Zone:** No preference.
   - **Database port:** `3306`.
9. **Additional configuration:**
   - **Initial database name:** `ecommerce_db`
   - **Backup retention period:** Pilih `0 days` atau `1 day` (untuk Learner Lab agar hemat ruang storage).
   - **Enable deletion protection:** Jangan dicentang (agar mudah dihapus setelah praktikum selesai).
10. Klik **Create database**. Pembuatan RDS memakan waktu sekitar 5–10 menit hingga statusnya menjadi **Available**.
11. Setelah *Available*, klik database tersebut dan **salin nilai `Endpoint`** (contoh: `ecommerce-mysql-db.cxxxxxx.us-east-1.rds.amazonaws.com`).

---

### LANGKAH 4: Meluncurkan Instance EC2 di Public Subnet

1. Buka layanan **EC2** di AWS Console.
2. Klik **Launch instance**.
3. **Name:** `ecommerce-web-server`
4. **Application and OS Images:** Pilih **Amazon Linux 2023 AMI** (atau **Ubuntu 22.04 LTS**).
5. **Instance type:** `t2.micro` atau `t3.micro`.
6. **Key pair (login):**
   - Pilih `vockey` (key pair bawaan Learner Lab) atau buat key pair baru `.pem`.
7. **Network settings (Klik Edit):**
   - **VPC:** Pilih `ecommerce-vpc`.
   - **Subnet:** Pilih salah satu **Public Subnet** (misal `ecommerce-vpc-subnet-public1-us-east-1a`).
   - **Auto-assign public IP:** Pilih **Enable** *(Wajib agar instance memiliki IP publik)*.
   - **Firewall (security groups):** Pilih **Select existing security group**, lalu centang **`ec2-web-sg`**.
8. **Configure storage:** Default 8 GiB (Amazon Linux) atau 10 GiB (Ubuntu).
9. **Advanced details (Opsional):**
   - IAM instance profile: Pilih **`LabRole`** (jika ingin melampirkan role).
10. Klik **Launch instance**.

---

### LANGKAH 5: Menghubungkan EC2 dan Men-deploy Aplikasi CRUD

1. Di daftar instance EC2, pilih `ecommerce-web-server` lalu klik **Connect**.
2. Gunakan tab **EC2 Instance Connect** dan klik **Connect** (Anda akan masuk ke shell Linux di browser tanpa perlu software SSH tambahan).
3. Salin/clone file project CRUD ini ke EC2:

```bash
# Update sistem dan instal python serta git
sudo dnf update -y
sudo dnf install -y python3 python3-pip git

# Buat direktori project
mkdir -p ~/ecommerce
cd ~/ecommerce
```

4. Buat atau unggah file proyek (`app.py`, `db.py`, `schema.sql`, `requirements.txt`, `.env`, serta folder `templates/`):

```bash
# 1. Buat file requirements.txt
cat << 'EOF' > requirements.txt
flask==3.0.3
pymysql==1.1.0
cryptography==42.0.8
python-dotenv==1.0.1
gunicorn==22.0.0
EOF

# 2. Siapkan Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

5. Buat file `.env` dengan memasukkan **Endpoint RDS** yang telah Anda salin pada Langkah 3B:

```bash
cat << 'EOF' > .env
DB_HOST=ecommerce-mysql-db.cxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=Admin123456!
DB_NAME=ecommerce_db
FLASK_ENV=production
SECRET_KEY=kunci-rahasia-cloud-lab-2026
PORT=80
EOF
```
> *(Ganti nilai `DB_HOST` dengan Endpoint RDS Anda yang sebenarnya)*

6. Salin file `db.py`, `app.py`, `schema.sql`, dan folder `templates/` ke dalam folder `~/ecommerce`.

7. Inisialisasi Database Schema:
Jalankan script python sekali untuk membuat tabel `products` dan mengisi data awal (*seed data*):
```bash
python3 -c "import db; ok, msg = db.init_db('schema.sql'); print('Status:', ok, '| Pesan:', msg)"
```
*Output yang diharapkan:* `Status: True | Pesan: Database dan tabel berhasil diinisialisasi!`

8. Jalankan aplikasi web di background menggunakan Gunicorn pada Port 80 (atau port 5000):
```bash
# Menjalankan langsung dengan sudo gunicorn pada port 80:
sudo ./venv/bin/gunicorn -w 3 -b 0.0.0.0:80 app:app --daemon
```

---

### LANGKAH 6: Pengujian Aplikasi & Verifikasi Operasi CRUD

1. Buka browser web di komputer Anda.
2. Masukkan alamat **Public IPv4** instance EC2 Anda:
   ```text
   http://<EC2_PUBLIC_IP>
   ```
3. Lakukan pengujian 4 Operasi CRUD:
   - **Create:** Klik tombol **"Tambah Produk Baru"**, isi form (Nama, SKU, Kategori, Harga, Stok), lalu klik Simpan.
   - **Read:** Periksa apakah data produk yang baru ditambahkan langsung muncul di tabel katalog. Uji fitur pencarian dan filter kategori.
   - **Update:** Klik tombol **"Edit"** pada salah satu baris produk, ubah harga atau jumlah stok, lalu klik Simpan.
   - **Delete:** Klik tombol **"Hapus"** (ikon tong sampah), konfirmasi pada modal dialog, dan pastikan item terhapus.
4. **Verifikasi Health Check Endpoint:**
   Buka URL:
   ```text
   http://<EC2_PUBLIC_IP>/health
   ```
   Aplikasi akan mengembalikan response JSON yang mengonfirmasi:
   - Hostname dan Local IP instance EC2.
   - Status koneksi langsung dari EC2 ke RDS MySQL di private subnet (`"connected": true`).

---

### LANGKAH 7: Verifikasi Keamanan Private Subnet (Bukti Akademik)

Untuk membuktikan pada laporan tugas/praktikum bahwa RDS benar-benar terisolasi di Private Subnet:
1. Coba koneksikan MySQL Workbench atau DBeaver dari laptop pribadi Anda langsung ke Endpoint RDS:
   - Hasil: **Connection Timeout / Gagal terhubung** (Karena RDS tidak memiliki Public IP dan Security Group menolak traffic dari luar).
2. Dari dalam terminal EC2, lakukan koneksi ke RDS:
   - Hasil: **Berhasil terhubung** (Karena EC2 berada di dalam VPC yang sama dan memiliki izin di `rds-mysql-sg`).

---

## 4. Tips Menghemat Kredit AWS Learner Lab Saat Praktikum Berakhir

1. **Hentikan Instance EC2 saat tidak digunakan:**
   Pilih EC2 Instance > **Instance state** > **Stop instance**. (Hanya bayar EBS storage yang sangat kecil).
2. **Hentikan Database RDS:**
   Pilih RDS Database > **Actions** > **Stop temporarily**. (RDS dapat di-stop hingga 7 hari berturut-turut).
3. **Jika praktikum telah dinilai dan selesai sepenuhnya:**
   Hapus database RDS (*Delete database* tanpa final snapshot) dan Terminate instance EC2 untuk menghentikan pemakaian kredit 100%.

