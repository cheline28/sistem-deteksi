from flask import Flask, request, jsonify
import sqlite3, time
from datetime import datetime

app = Flask(__name__)

# === SETUP DATABASE ===
def init_db():
    conn = sqlite3.connect("deteksi.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hasil_deteksi (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT,
            label        TEXT,
            total        INTEGER,
            teks_lengkap TEXT
        )
    """)
    conn.commit()
    conn.close()

# === ENDPOINT 1: Raspberry Pi kirim data ===
@app.route("/deteksi", methods=["POST"])
def terima_deteksi():
    data = request.get_json()

    # Susun format teks lengkap
    # Contoh: 25-5-2026, 13.54.22, Wereng - total: 5
    now          = datetime.now()
    tanggal      = tanggal = f"{now.day}-{now.month}-{now.year}" 
    jam          = now.strftime("%H.%M.%S")      # 13.54.22
    teks_lengkap = f"{tanggal}, {jam}, {data['label']} - total: {data['total']}"

    # Simpan ke database
    conn   = sqlite3.connect("deteksi.db")
    cursor = conn.execute("""
        INSERT INTO hasil_deteksi (timestamp, label, total, teks_lengkap)
        VALUES (?, ?, ?, ?)
    """, (
        f"{tanggal}, {jam}",
        data["label"],
        data["total"],
        teks_lengkap
    ))
    conn.commit()
    id_baru = cursor.lastrowid
    conn.close()

    print(f"[TERSIMPAN] {teks_lengkap}")

    # Balas konfirmasi ke Raspberry Pi
    return jsonify({
        "status"      : "TERSIMPAN",
        "id"          : id_baru,
        "teks_lengkap": teks_lengkap
    }), 201


# === ENDPOINT 2: Dashboard ambil semua data ===
@app.route("/deteksi", methods=["GET"])
def ambil_semua():
    conn = sqlite3.connect("deteksi.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM hasil_deteksi
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows]), 200


init_db()

if __name__ == "__main__":
    app.run(debug=True)