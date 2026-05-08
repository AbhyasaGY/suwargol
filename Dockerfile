# Gunakan base image Python yang ringan
FROM python:3.9-slim

# Set working directory di dalam container
WORKDIR /app

# Salin file requirements dan install dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh source code ke dalam container
COPY . .

# Expose port yang akan digunakan aplikasi (misalnya port 5000 untuk Flask)
EXPOSE 5000

# Perintah untuk menjalankan aplikasi
CMD ["python", "app.py"]