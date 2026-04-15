# admin.py

from flask import Blueprint, request, redirect, url_for
from helpers import flash_msg, base  # FIX: ganti admin_base → base

admin_bp = Blueprint('admin', __name__)

# wrapper biar tetap ada "admin_base"
def admin_base(content, title="Admin"):
    return base(content, title)


@admin_bp.route('/admin')
def admin_home():
    content = """
    <h2>Admin Dashboard</h2>
    <a href='/admin/add'>Tambah Film</a>
    """
    return admin_base(content)


@admin_bp.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            price = request.form.get('price')

            if not title or not price:
                flash_msg("Semua field wajib diisi", "error")
                return redirect(url_for('admin.add_movie'))

            # TODO: simpan ke database
            # pastikan fungsi database lo aman (file ada / auto create)

            flash_msg("Film berhasil ditambahkan", "success")
            return redirect(url_for('admin.admin_home'))

        except Exception as e:
            print("ERROR ADD MOVIE:", e)  # debug log
            flash_msg("Terjadi error", "error")
            return redirect(url_for('admin.add_movie'))

    content = """
    <h2>Tambah Film</h2>
    <form method="POST">
        <input name="title" placeholder="Judul Film"><br>
        <input name="price" placeholder="Harga"><br>
        <button type="submit">Tambah</button>
    </form>
    """
    return admin_base(content)
