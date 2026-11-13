-- Buat database jika belum ada
CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- Buat tabel products
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    sku VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Masukkan data awal (Seed Data)
INSERT INTO products (name, category, price, stock, sku, description) VALUES
('Cloud Architecture Book 2026', 'Buku', 250000.00, 35, 'BOK-CLD-001', 'Panduan lengkap mendesain arsitektur cloud AWS berstandar industri.'),
('Wireless Mechanical Keyboard', 'Elektronik', 780000.00, 15, 'ELE-KEY-002', 'Keyboard mekanik 75% dengan konektivitas Bluetooth 5.2 dan 2.4Ghz.'),
('Ergonomic Laptop Stand', 'Aksesoris', 185000.00, 50, 'ACC-STN-003', 'Stand aluminium kokoh dengan ventilasi pendingin untuk laptop hingga 16 inci.'),
('AWS DevOps Coffee Mug', 'Merchandise', 65000.00, 100, 'MER-MUG-004', 'Cangkir keramik anti panas dengan sablon AWS Certified Solutions Architect.'),
('USB-C 7-in-1 Hub Multiport', 'Elektronik', 320000.00, 20, 'ELE-HUB-005', 'Adaptor USB Type-C dengan port 4K HDMI, 3x USB 3.0, SD Card Reader, dan 100W PD.');

