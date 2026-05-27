from flask import Flask, request, jsonify, render_template
from datetime import datetime
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# === KONEKSI DATABASE ===
def get_db():
    url = os.environ.get("DATABASE_URL")
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
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)