from flask import Flask, request, jsonify
import sqlite3, time

app = Flask(__name__)

# === FUNGSI DATABASE ===
def init_db():
    conn = sqlite3.connect("deteksi.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hasil_deteksi (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id    TEXT,
            hasil        TEXT,
            waktu_simpan TEXT
        )
    """)
    conn.commit()
    conn.close()

# === ENDPOINT 1: Raspberry Pi kirim data ===
@app.route("/deteksi", methods=["POST"])
def terima_deteksi():
    data = request.get_json()

    # Simpan ke database
    conn = sqlite3.connect("deteksi.db")
    cursor = conn.execute("""
        INSERT INTO hasil_deteksi (device_id, hasil, waktu_simpan)
        VALUES (?, ?, ?)
    """, (
        data["device_id"],
        data["hasil"],
        time.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    id_baru = cursor.lastrowid
    conn.close()

    # Balas konfirmasi ke Raspberry Pi
    return jsonify({
        "status" : "TERSIMPAN",
        "id"     : id_baru,
        "pesan"  : f"Data berhasil disimpan dengan ID {id_baru}"
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

    hasil = [dict(row) for row in rows]
    return jsonify(hasil), 200


# === JALANKAN SERVER ===
if __name__ == "__main__":
    init_db()
    app.run(debug=True)