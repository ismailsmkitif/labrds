# Project E-Commerce Catalog CRUD (AWS 2-Tier Architecture)

Project aplikasi web manajemen katalog produk e-commerce berbasis **Python (Flask)** dan **MySQL** yang dirancang khusus untuk deployment di **AWS Learner Lab** menggunakan arsitektur 2-Tier:
- **Web Layer:** Amazon EC2 di Public Subnet
- **Database Layer:** Amazon RDS MySQL di Private Subnet
- **Network Layer:** Amazon VPC dengan 2 Public Subnet & 2 Private Subnet (Multi-AZ DB Subnet Group)

---

## Struktur File Project

```
ecommerce/
├── app.py                      # Aplikasi utama Flask (Routing CRUD, API health check)
├── db.py                       # Modul koneksi PyMySQL & inisialisasi schema
├── schema.sql                  # Skrip SQL tabel products & seed data awal
├── requirements.txt            # Daftar dependensi Python
├── .env.example                # Contoh konfigurasi environment variable
├── ecommerce.service           # File konfigurasi systemd service untuk EC2
├── PANDUAN_AWS_LEARNER_LAB.md  # Panduan step-by-step lengkap di AWS Console
├── scripts/
│   └── deploy.sh               # Skrip otomasi deployment di EC2
└── templates/
    ├── base.html               # Layout dasar (Bootstrap 5 + Cloud Info Header)
    ├── index.html              # Tampilan daftar produk (Read, Search, Filter, Delete)
    ├── create.html             # Form tambah produk baru (Create)
    └── edit.html               # Form edit data produk (Update)
```

---

## Fitur Utama

1. **Operasi CRUD Lengkap:**
   - **Create:** Input produk baru dengan validasi SKU unik.
   - **Read:** Menampilkan katalog produk dengan pencarian real-time dan filter kategori.
   - **Update:** Mengubah nama, harga, stok, dan deskripsi produk.
   - **Delete:** Menghapus produk dengan modal konfirmasi keamanan.
2. **Cloud Architecture Monitoring Banner:**
   - Menampilkan EC2 Hostname, Private IP, dan Endpoint RDS langsung di navbar.
3. **Health Check API (`/health`):**
   - Mengembalikan status kesehatan server dan konektivitas RDS dalam format JSON.
4. **Auto DB Initializer (`/init-database`):**
   - Inisialisasi schema database dan seed data melalui tombol satu klik di antarmuka web.

---

## Panduan Pengerjaan di AWS Learner Lab

Buka dan ikuti panduan lengkap pada:
👉 **[PANDUAN_AWS_LEARNER_LAB.md](file:///e:/2026/Materi/cloud%20computing/ecommerce/PANDUAN_AWS_LEARNER_LAB.md)**

# labrds
