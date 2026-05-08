import os
import boto3
import pymysql
from flask import Flask, render_template, request, redirect, session, url_for, flash

app = Flask(__name__)
app.secret_key = "suwargol_secret_key_sangat_rahasia"

# ==========================================
# KONFIGURASI AWS & DB 
# ==========================================
S3_BUCKET = "suwargol-storage-152022087"
CLOUDFRONT_DOMAIN = ""
DB_HOST = "suwargol-db.ct2c2ki8ox9c.ap-southeast-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "admin1231"
DB_NAME = "suwargol_db"

def get_db_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)

# --- FITUR 1: AUTENTIKASI ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('warga_dashboard'))
        else:
            flash("Username atau Password salah!")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'warga')", (username, password))
            conn.commit()
            flash("Registrasi berhasil! Silakan login.")
            return redirect(url_for('login'))
        except:
            flash("Username sudah digunakan!")
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- FITUR 2: PEMBUATAN LAPORAN & UPLOAD S3 (WARGA) ---
@app.route('/')
def warga_dashboard():
    if 'user_id' not in session or session['role'] != 'warga':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM laporan_pengaduan WHERE user_id=%s ORDER BY tanggal_lapor DESC", (session['user_id'],))
        laporan = cursor.fetchall()
    conn.close()
    
    return render_template('warga.html', reports=laporan, cf_domain=CLOUDFRONT_DOMAIN)

@app.route('/submit_laporan', methods=['POST'])
def submit_laporan():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    nama = request.form['nama']
    isi = request.form['laporan']
    file = request.files['foto']
    
    if file:
        filename = file.filename
        # Upload S3
        s3 = boto3.client('s3')
        s3.upload_fileobj(file, S3_BUCKET, filename)
        
        # Simpan nama file ke RDS (nanti digabung dengan CloudFront di HTML)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO laporan_pengaduan (user_id, nama_pelapor, isi_laporan, foto_url) VALUES (%s, %s, %s, %s)", 
                           (session['user_id'], nama, isi, filename))
        conn.commit()
        conn.close()
        
    return redirect(url_for('warga_dashboard'))

# --- FITUR 3: DASHBOARD TRACKING ADMIN ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM laporan_pengaduan ORDER BY tanggal_lapor DESC")
        laporan = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', reports=laporan, cf_domain=CLOUDFRONT_DOMAIN)

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    status_baru = request.form['status']
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE laporan_pengaduan SET status=%s WHERE id=%s", (status_baru, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Buat Tabel Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('warga', 'admin') DEFAULT 'warga'
                )
            """)
            # 2. Buat Tabel Laporan
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS laporan_pengaduan (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    nama_pelapor VARCHAR(100) NOT NULL,
                    isi_laporan TEXT NOT NULL,
                    foto_url VARCHAR(255),
                    status ENUM('Menunggu', 'Diproses', 'Selesai') DEFAULT 'Menunggu',
                    tanggal_lapor TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            # 3. Buat akun Admin bawaan (untuk testing)
            cursor.execute("""
                INSERT IGNORE INTO users (username, password, role) 
                VALUES ('admin', 'admin123', 'admin')
            """)
        conn.commit()
        conn.close()
        print("Database berhasil diinisialisasi!")
    except Exception as e:
        print(f"Gagal menginisialisasi database: {e}")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)