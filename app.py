import os
import boto3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Konfigurasi AWS S3 (Silakan sesuaikan dengan nama bucket Anda)
S3_BUCKET = "suwargol-storage-152022087"
CLOUDFRONT_URL = "https://[ID_CLOUDFRONT_ANDA].cloudfront.net" # Ganti nanti jika verif selesai

s3_client = boto3.client('s3')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    nama = request.form.get('nama')
    laporan = request.form.get('laporan')
    file = request.files['foto']

    if file:
        filename = file.filename
        # Upload ke Amazon S3 
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Logika simpan teks ke RDS seharusnya di sini [cite: 44]
        print(f"Laporan dari {nama} diterima: {laporan}")
        
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)