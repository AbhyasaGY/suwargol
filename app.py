from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Selamat Datang di Sistem Pengaduan SuWarGol (Suara Warga Regol)!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)