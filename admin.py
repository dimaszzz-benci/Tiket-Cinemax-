from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db, save_db
from functools import wraps
import uuid
import hashlib

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ========================
# 🔐 CONFIG ADMIN
# ========================
ADMIN_USERNAME = "admin"
# password: admin123
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()


# ========================
# 🔐 AUTH DECORATOR
# ========================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Harus login dulu!", "error")
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return wrapper


# ========================
# 🔧 HELPER
# ========================
def generate_id():
    return str(uuid.uuid4())


def find_movie(db, movie_id):
    return next((m for m in db["movies"] if m["id"] == movie_id), None)


# ========================
# 🔐 LOGIN
# ========================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        hashed = hashlib.sha256(password.encode()).hexdigest()

        if username == ADMIN_USERNAME and hashed == ADMIN_PASSWORD_HASH:
            session["admin_logged_in"] = True
            flash("Login berhasil!", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Username atau password salah!", "error")

    return render_template("admin/login.html")


# ========================
# 🚪 LOGOUT
# ========================
@admin_bp.route('/logout')
def logout():
    session.clear()
    flash("Logout berhasil!", "success")
    return redirect(url_for('admin.login'))


# ========================
# 🎬 DASHBOARD
# ========================
@admin_bp.route('/')
@admin_required
def dashboard():
    db = get_db()
    movies = db.get("movies", [])
    return render_template("admin/dashboard.html", movies=movies)


# ========================
# ➕ TAMBAH FILM
# ========================
@admin_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_movie():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        duration = request.form.get('duration', '').strip()

        if not title or not duration:
            flash("Judul dan durasi wajib diisi!", "error")
            return redirect(url_for('admin.add_movie'))

        db = get_db()

        new_movie = {
            "id": generate_id(),
            "title": title,
            "description": description,
            "duration": duration,
            "showtimes": []
        }

        db["movies"].append(new_movie)
        save_db(db)

        flash("Film berhasil ditambahkan!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template("admin/add_movie.html")


# ========================
# ✏️ EDIT FILM
# ========================
@admin_bp.route('/edit/<movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    db = get_db()
    movie = find_movie(db, movie_id)

    if not movie:
        flash("Film tidak ditemukan!", "error")
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        duration = request.form.get('duration', '').strip()

        if not title or not duration:
            flash("Judul dan durasi wajib diisi!", "error")
            return redirect(url_for('admin.edit_movie', movie_id=movie_id))

        movie["title"] = title
        movie["description"] = description
        movie["duration"] = duration

        save_db(db)

        flash("Film berhasil diupdate!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template("admin/edit_movie.html", movie=movie)


# ========================
# ❌ HAPUS FILM
# ========================
@admin_bp.route('/delete/<movie_id>', methods=['POST'])
@admin_required
def delete_movie(movie_id):
    db = get_db()
    movie = find_movie(db, movie_id)

    if not movie:
        flash("Film tidak ditemukan!", "error")
        return redirect(url_for('admin.dashboard'))

    db["movies"].remove(movie)
    save_db(db)

    flash("Film berhasil dihapus!", "success")
    return redirect(url_for('admin.dashboard'))


# ========================
# 🕒 TAMBAH JADWAL
# ========================
@admin_bp.route('/<movie_id>/add_showtime', methods=['POST'])
@admin_required
def add_showtime(movie_id):
    db = get_db()
    movie = find_movie(db, movie_id)

    if not movie:
        flash("Film tidak ditemukan!", "error")
        return redirect(url_for('admin.dashboard'))

    time = request.form.get('time', '').strip()

    if not time:
        flash("Waktu tayang wajib diisi!", "error")
        return redirect(url_for('admin.dashboard'))

    if time in movie["showtimes"]:
        flash("Jadwal sudah ada!", "warning")
        return redirect(url_for('admin.dashboard'))

    movie["showtimes"].append(time)
    save_db(db)

    flash("Jadwal berhasil ditambahkan!", "success")
    return redirect(url_for('admin.dashboard'))


# ========================
# ❌ HAPUS JADWAL
# ========================
@admin_bp.route('/<movie_id>/delete_showtime', methods=['POST'])
@admin_required
def delete_showtime(movie_id):
    db = get_db()
    movie = find_movie(db, movie_id)

    if not movie:
        flash("Film tidak ditemukan!", "error")
        return redirect(url_for('admin.dashboard'))

    time = request.form.get('time')

    if time in movie["showtimes"]:
        movie["showtimes"].remove(time)
        save_db(db)
        flash("Jadwal berhasil dihapus!", "success")
    else:
        flash("Jadwal tidak ditemukan!", "error")

    return redirect(url_for('admin.dashboard'))
