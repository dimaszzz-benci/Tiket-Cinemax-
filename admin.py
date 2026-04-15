from flask import Blueprint, request, redirect, url_for, render_template, flash from werkzeug.utils import secure_filename import os import json

admin_bp = Blueprint('admin', name, url_prefix='/admin')

File database JSON

MOVIES_FILE = 'movies.json' QR_FOLDER = 'static/qr'

Pastikan folder QR ada

os.makedirs(QR_FOLDER, exist_ok=True)

==========================

Helper Functions

==========================

def load_movies(): if not os.path.exists(MOVIES_FILE): return [] with open(MOVIES_FILE, 'r') as f: return json.load(f)

def save_movies(movies): with open(MOVIES_FILE, 'w') as f: json.dump(movies, f, indent=4)

==========================

DASHBOARD ADMIN

==========================

@admin_bp.route('/') def dashboard(): movies = load_movies() return render_template('admin/dashboard.html', movies=movies)

==========================

CREATE MOVIE / TIKET

==========================

@admin_bp.route('/add', methods=['GET', 'POST']) def add_movie(): if request.method == 'POST': movies = load_movies()

title = request.form['title']
    genre = request.form['genre']
    price = request.form['price']
    description = request.form['description']

    new_movie = {
        "id": len(movies) + 1,
        "title": title,
        "genre": genre,
        "price": price,
        "description": description
    }

    movies.append(new_movie)
    save_movies(movies)

    flash('Film berhasil ditambahkan', 'success')
    return redirect(url_for('admin.dashboard'))

return render_template('admin/add_movie.html')

==========================

UPDATE MOVIE

==========================

@admin_bp.route('/edit/int:movie_id', methods=['GET', 'POST']) def edit_movie(movie_id): movies = load_movies()

movie = next((m for m in movies if m['id'] == movie_id), None)

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

return render_template('admin/edit_movie.html', movie=movie)

==========================

DELETE MOVIE

==========================

@admin_bp.route('/delete/int:movie_id') def delete_movie(movie_id): movies = load_movies()

movies = [m for m in movies if m['id'] != movie_id]

save_movies(movies)

flash('Film berhasil dihapus', 'warning')
return redirect(url_for('admin.dashboard'))

==========================

UPLOAD QR CODE

==========================

@admin_bp.route('/upload-qr', methods=['GET', 'POST']) def upload_qr(): if request.method == 'POST':

if 'qr_image' not in request.files:
        flash('Tidak ada file dipilih', 'danger')
        return redirect(request.url)

    file = request.files['qr_image']

    if file.filename == '':
        flash('Nama file kosong', 'danger')
        return redirect(request.url)

    filename = secure_filename(file.filename)
    filepath = os.path.join(QR_FOLDER, filename)

    file.save(filepath)

    # Simpan nama QR di file JSON
    qr_data = {"qr_image": filename}

    with open('qr.json', 'w') as f:
        json.dump(qr_data, f, indent=4)

    flash('QR Code berhasil diupload', 'success')
    return redirect(url_for('admin.dashboard'))

return render_template('admin/upload_qr.html')

==========================

GET QR FOR PAYMENT METHOD

==========================

def get_qr_image(): if not os.path.exists('qr.json'): return None

with open('qr.json', 'r') as f:
    data = json.load(f)
    return data.get('qr_image')
