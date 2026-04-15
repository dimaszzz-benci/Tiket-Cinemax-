from flask import Blueprint, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
import os
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==========================
# CONFIG FILE
# ==========================

MOVIES_FILE = 'movies.json'
QR_FOLDER = 'static/qr'
QR_JSON = 'qr.json'

# Pastikan folder QR aman di Vercel
if not os.path.exists(QR_FOLDER):
    try:
        os.makedirs(QR_FOLDER)
    except:
        pass


# ==========================
# HELPER FUNCTIONS
# ==========================

def load_movies():
    if not os.path.exists(MOVIES_FILE):
        return []

    with open(MOVIES_FILE, 'r') as f:
        return json.load(f)


def save_movies(movies):
    with open(MOVIES_FILE, 'w') as f:
        json.dump(movies, f, indent=4)


def get_new_id(movies):
    if not movies:
        return 1
    return max(m['id'] for m in movies) + 1


def get_qr_image():
    if not os.path.exists(QR_JSON):
        return None

    with open(QR_JSON, 'r') as f:
        data = json.load(f)
        return data.get('qr_image')


# ==========================
# DASHBOARD ADMIN
# ==========================

@admin_bp.route('/')
def dashboard():
    movies = load_movies()
    qr_image = get_qr_image()

    return render_template(
        'admin/dashboard.html',
        movies=movies,
        qr_image=qr_image
    )


# ==========================
# CREATE MOVIE
# ==========================

@admin_bp.route('/add', methods=['GET', 'POST'])
def add_movie():

    if request.method == 'POST':

        movies = load_movies()

        new_movie = {
            "id": get_new_id(movies),
            "title": request.form['title'],
            "genre": request.form['genre'],
            "price": request.form['price'],
            "description": request.form['description']
        }

        movies.append(new_movie)
        save_movies(movies)

        flash('Film berhasil ditambahkan', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_movie.html')


# ==========================
# EDIT MOVIE
# ==========================

@admin_bp.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):

    movies = load_movies()

    movie = next(
        (m for m in movies if m['id'] == movie_id),
        None
    )

    if not movie:
        flash('Film tidak ditemukan', 'danger')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':

        movie['title'] = request.form['title']
        movie['genre'] = request.form['genre']
        movie['price'] = request.form['price']
        movie['description'] = request.form['description']

        save_movies(movies)

        flash('Film berhasil diperbarui', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template(
        'admin/edit_movie.html',
        movie=movie
    )


# ==========================
# DELETE MOVIE
# ==========================

@admin_bp.route('/delete/<int:movie_id>')
def delete_movie(movie_id):

    movies = load_movies()

    movies = [
        m for m in movies
        if m['id'] != movie_id
    ]

    save_movies(movies)

    flash('Film berhasil dihapus', 'warning')

    return redirect(url_for('admin.dashboard'))


# ==========================
# UPLOAD QR CODE
# ==========================

@admin_bp.route('/upload-qr', methods=['GET', 'POST'])
def upload_qr():

    if request.method == 'POST':

        if 'qr_image' not in request.files:
            flash('Tidak ada file', 'danger')
            return redirect(request.url)

        file = request.files['qr_image']

        if file.filename == '':
            flash('File kosong', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            QR_FOLDER,
            filename
        )

        file.save(filepath)

        qr_data = {
            "qr_image": filename
        }

        with open(QR_JSON, 'w') as f:
            json.dump(qr_data, f, indent=4)

        flash('QR berhasil diupload', 'success')

        return redirect(
            url_for('admin.dashboard')
        )

    return render_template(
        'admin/upload_qr.html'
        )
