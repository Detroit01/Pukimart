from flask import Flask, render_template, request, session, redirect, url_for, flash
import json
import datetime

app = Flask(__name__)
app.secret_key = "kunci_rahasia_pukimart"

# Database User
USERS = {
    "bos": {"password": "123", "role": "Kepala Toko"},
    "kasir1": {"password": "123", "role": "Kasir"}
}

# Variabel Global Keuangan & Analisis (Disimpan di RAM Server)
LAPORAN = {
    "total_pendapatan": 0,
    "jumlah_transaksi": 0
}
PRODUK_TERJUAL = {}  # Format: {"Nama Barang": JumlahTerjual}
RIWAYAT_TRANSAKSI = []  # Format: [{"waktu": ..., "items": ..., "total": ...}]

# Database Barang dengan Sistem Stok & Kategori Baru
BARANG = {
    "Makanan Ringan": [
        {"nama": "Indomie Goreng", "harga": 3500, "icon": "🍜", "stok": 50},
        {"nama": "Silverqueen", "harga": 15000, "icon": "🍫", "stok": 30},
        {"nama": "Chitato BBQ", "harga": 10000, "icon": "🥔", "stok": 40},
        {"nama": "Taro Snack", "harga": 6000, "icon": "🥨", "stok": 25},
        {"nama": "Fitbar Multigrain", "harga": 5000, "icon": "🥜", "stok": 20},
        {"nama": "Beng-Beng", "harga": 2500, "icon": "🍫", "stok": 60},
    ],
    "Minuman": [
        {"nama": "Aqua 600ml", "harga": 5000, "icon": "💧", "stok": 100},
        {"nama": "Teh Pucuk Harum", "harga": 4000, "icon": "🍵", "stok": 80},
        {"nama": "Pocari Sweat", "harga": 8000, "icon": "💦", "stok": 45},
        {"nama": "Susu L-Men", "harga": 12000, "icon": "🥛", "stok": 15},
        {"nama": "Kopi Kapsul", "harga": 10000, "icon": "☕", "stok": 35},
        {"nama": "Coca-Cola", "harga": 6000, "icon": "🥤", "stok": 50},
    ],
    "Alat Kesehatan": [
        {"nama": "Kondom Sutra", "harga": 12000, "icon": "🛡️", "stok": 20},
        {"nama": "Insto Obat Mata", "harga": 16000, "icon": "👁️", "stok": 25},
        {"nama": "Panadol Biru", "harga": 10000, "icon": "💊", "stok": 50},
        {"nama": "Koyo Salonpas", "harga": 8000, "icon": "🩹", "stok": 40},
        {"nama": "Hansaplast", "harga": 2000, "icon": "🩹", "stok": 100},
        {"nama": "Betadine 5ml", "harga": 15000, "icon": "🩸", "stok": 15},
    ],
    "Alkohol": [
        {"nama": "Azul Tequila", "harga": 3500000, "icon": "🍾", "stok": 5},
        {"nama": "Jack Daniels", "harga": 750000, "icon": "🥃", "stok": 12},
        {"nama": "Jagermeister", "harga": 650000, "icon": "🧪", "stok": 15},
        {"nama": "Baileys Irish Cream", "harga": 600000, "icon": "🍹", "stok": 10},
        {"nama": "Smirnoff Vodka", "harga": 380000, "icon": "🍸", "stok": 18},
        {"nama": "Bir Bintang", "harga": 35000, "icon": "🍺", "stok": 48},
    ]
}

def dapatkan_best_seller():
    if not PRODUK_TERJUAL:
        return "Belum ada produk terjual"
    terlaris = max(PRODUK_TERJUAL, key=PRODUK_TERJUAL.get)
    return f"{terlaris} ({PRODUK_TERJUAL[terlaris]} pcs)"

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('kasir'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            session['role'] = USERS[username]['role']
            return redirect(url_for('kasir'))
        else:
            flash("Username atau Password salah!")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/kasir')
def kasir():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    return render_template(
        'kasir.html', 
        barang=BARANG, 
        role=session['role'], 
        user=session['user'], 
        laporan=LAPORAN, 
        best_seller=dapatkan_best_seller(),
        riwayat=RIWAYAT_TRANSAKSI
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================= MANAJEMEN STOK & BARANG (KHUSUS BOS) =================
@app.route('/tambah_barang', methods=['POST'])
def tambah_barang():
    if 'user' in session and session.get('role') == 'Kepala Toko':
        kategori = request.form.get('kategori')
        nama = request.form.get('nama')
        harga = int(request.form.get('harga'))
        stok = int(request.form.get('stok'))
        icon = request.form.get('icon')
        
        if kategori in BARANG:
            BARANG[kategori].append({"nama": nama, "harga": harga, "icon": icon, "stok": stok})
            
    return redirect(url_for('kasir'))

@app.route('/update_stok', methods=['POST'])
def update_stok():
    if 'user' in session and session.get('role') == 'Kepala Toko':
        nama_barang = request.form.get('nama_barang')
        aksi = request.form.get('aksi')  # 'tambah' atau 'kurang'
        jumlah = int(request.form.get('jumlah'))
        
        for kategori, daftar in BARANG.items():
            for item in daftar:
                if item['nama'] == nama_barang:
                    if aksi == 'tambah':
                        item['stok'] += jumlah
                    elif aksi == 'kurang':
                        item['stok'] = max(0, item['stok'] - jumlah)
                    break
                    
    return redirect(url_for('kasir'))

# ================= PENCATATAN TRANSAKSI =================
@app.route('/catat_transaksi', methods=['POST'])
def catat_transaksi():
    total_belanja = int(request.form.get('total'))
    items_raw = request.form.get('items')
    items = json.loads(items_raw) if items_raw else []

    LAPORAN['total_pendapatan'] += total_belanja
    LAPORAN['jumlah_transaksi'] += 1

    nama_terbeli = []
    for item_beli in items:
        nama = item_beli['nama']
        nama_terbeli.append(nama)
        
        # 1. Update Analisis Best Seller
        PRODUK_TERJUAL[nama] = PRODUK_TERJUAL.get(nama, 0) + 1
        
        # 2. Potong Stok Terjual di Server
        for kategori, daftar in BARANG.items():
            for item in daftar:
                if item['nama'] == nama:
                    item['stok'] = max(0, item['stok'] - 1)
                    break

    # 3. Catat ke Histori Penjualan
    waktu_skrg = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    RIWAYAT_TRANSAKSI.append({
        "waktu": waktu_skrg,
        "items": ", ".join(nama_terbeli),
        "total": total_belanja
    })
    
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)