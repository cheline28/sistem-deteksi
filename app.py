from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# === KONEKSI DATABASE ===
def get_db():
    url = os.environ.get("DATABASE_URL")
    print(f"[DEBUG] DATABASE_URL: {url}")
    return psycopg2.connect(url)

# === BUAT TABEL JIKA BELUM ADA ===
def init_db():
    conn = get_db()
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS hasil_deteksi (
            id           SERIAL PRIMARY KEY,
            timestamp    TEXT,
            label        TEXT,
            total        INTEGER,
            teks_lengkap TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# === ENDPOINT 1: Raspberry Pi kirim data ===
@app.route("/deteksi", methods=["POST"])
def terima_deteksi():
    data = request.get_json()

    now          = datetime.now()
    tanggal      = f"{now.day}-{now.month}-{now.year}"
    jam          = now.strftime("%H.%M.%S")
    teks_lengkap = f"{tanggal}, {jam}, {data['label']} - total: {data['total']}"

    conn   = get_db()
    cur    = conn.cursor()
    cur.execute("""
        INSERT INTO hasil_deteksi (timestamp, label, total, teks_lengkap)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (f"{tanggal}, {jam}", data["label"], data["total"], teks_lengkap))
    id_baru = cur.fetchone()[0]
    conn.commit()
    conn.close()

    print(f"[TERSIMPAN] {teks_lengkap}")

    return jsonify({
        "status"      : "TERSIMPAN",
        "id"          : id_baru,
        "teks_lengkap": teks_lengkap
    }), 201


# === ENDPOINT 2: Ambil semua data ===
@app.route("/deteksi", methods=["GET"])
def ambil_semua():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM hasil_deteksi ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200


# === ENDPOINT 3: Dashboard Web ===
@app.route("/")
def dashboard():
    return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HamaSense — Dashboard Deteksi Hama</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f4f8; color: #333; }
        .header {
            background: #1a5c2e;
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 22px; }
        .header span { font-size: 13px; opacity: 0.8; }
        .container { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .stat-card .angka { font-size: 36px; font-weight: bold; color: #1a5c2e; }
        .stat-card .label { font-size: 13px; color: #666; margin-top: 4px; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .card h2 { font-size: 16px; margin-bottom: 16px; color: #1a5c2e; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { background: #1a5c2e; color: white; padding: 10px 14px; text-align: left; }
        td { padding: 10px 14px; border-bottom: 1px solid #eee; }
        tr:hover td { background: #f9f9f9; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            background: #d4edda;
            color: #155724;
        }
        .refresh { font-size: 12px; color: #888; text-align: right; margin-bottom: 10px; }
        .empty { text-align: center; color: #aaa; padding: 40px; }
    </style>
</head>
<body>
<div class="header">
    <h1>🌿 HamaSense — Dashboard Deteksi Hama</h1>
    <span id="waktu">Memuat...</span>
</div>
<div class="container">
    <div class="stats">
        <div class="stat-card">
            <div class="angka" id="total-deteksi">-</div>
            <div class="label">Total Deteksi</div>
        </div>
        <div class="stat-card">
            <div class="angka" id="total-jenis">-</div>
            <div class="label">Jenis Hama</div>
        </div>
        <div class="stat-card">
            <div class="angka" id="deteksi-terakhir">-</div>
            <div class="label">Deteksi Terakhir</div>
        </div>
    </div>
    <div class="card">
        <h2>📋 Riwayat Deteksi Hama</h2>
        <div class="refresh">Auto-refresh setiap 10 detik | <span id="last-update">-</span></div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Timestamp</th>
                    <th>Jenis Hama</th>
                    <th>Total</th>
                    <th>Catatan Lengkap</th>
                </tr>
            </thead>
            <tbody id="tabel-data">
                <tr><td colspan="5" class="empty">Memuat data...</td></tr>
            </tbody>
        </table>
    </div>
</div>
<script>
    function updateWaktu() {
        const now = new Date();
        document.getElementById('waktu').textContent =
            now.toLocaleDateString('id-ID') + ' ' + now.toLocaleTimeString('id-ID');
    }

    async function ambilData() {
        try {
            const res  = await fetch('/deteksi');
            const data = await res.json();

            document.getElementById('total-deteksi').textContent = data.length;
            const jenis = [...new Set(data.map(d => d.label))];
            document.getElementById('total-jenis').textContent = jenis.length;
            if (data.length > 0) {
                document.getElementById('deteksi-terakhir').textContent = data[0].label;
            }

            const tbody = document.getElementById('tabel-data');
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty">Belum ada data deteksi</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(row => `
                <tr>
                    <td>${row.id}</td>
                    <td>${row.timestamp}</td>
                    <td><span class="badge">${row.label}</span></td>
                    <td>${row.total}</td>
                    <td>${row.teks_lengkap}</td>
                </tr>
            `).join('');

            document.getElementById('last-update').textContent =
                'Update: ' + new Date().toLocaleTimeString('id-ID');
        } catch (err) {
            console.error('Gagal ambil data:', err);
        }
    }

    updateWaktu();
    ambilData();
    setInterval(ambilData, 10000);
    setInterval(updateWaktu, 1000);
</script>
</body>
</html>
    """)


if __name__ == "__main__":
    app.run(debug=True)