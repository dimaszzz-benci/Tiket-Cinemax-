from flask import Blueprint, request, redirect, url_for, session, make_response
from werkzeug.utils import secure_filename
from helpers import admin_base, flash_msg, get_flashes
import os
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==========================
# CONFIG
# ==========================

MOVIES_FILE = 'movies.json'
QR_FOLDER = 'static/qr'
QR_JSON = 'qr.json'
POSTER_FOLDER = 'static/posters'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'cinemax2024'

for folder in [QR_FOLDER, POSTER_FOLDER]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except:
            pass


# ==========================
# HELPERS
# ==========================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


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


def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return func(*args, **kwargs)
    return wrapper


# ==========================
# LOGIN ADMIN
# ==========================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error = 'Username atau password salah.'

    content = f'''
    <div style="min-height:100vh;background:#090912;display:flex;align-items:center;justify-content:center;padding:1.5rem;">
      <div style="width:100%;max-width:400px;">
        <div style="text-align:center;margin-bottom:2rem;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;">🎬 CineMax</div>
          <div style="color:#8888aa;font-size:.9rem;margin-top:.25rem;">Admin Panel</div>
        </div>
        <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:20px;padding:2rem;">
          <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;letter-spacing:2px;margin-bottom:1.5rem;text-align:center;">LOGIN ADMIN</h2>
          {"" if not error else f'<div style="padding:.75rem 1rem;background:rgba(232,23,58,.12);border:1px solid rgba(232,23,58,.3);border-radius:10px;color:#f87171;font-size:.85rem;margin-bottom:1rem;">{error}</div>'}
          <form method="POST">
            <div class="form-group">
              <label>Username</label>
              <input type="text" name="username" placeholder="Masukkan username" required autofocus>
            </div>
            <div class="form-group">
              <label>Password</label>
              <input type="password" name="password" placeholder="Masukkan password" required>
            </div>
            <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;padding:.75rem;font-size:1rem;">Masuk →</button>
          </form>
        </div>
        <div style="text-align:center;margin-top:1.5rem;">
          <a href="/" style="color:#8888aa;font-size:.85rem;">← Kembali ke Website</a>
        </div>
      </div>
    </div>
    '''

    from helpers import base as user_base
    # Render tanpa sidebar admin (halaman login standalone)
    from flask import make_response
    return make_response(f'''<!DOCTYPE html><html lang="id"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Login Admin - CineMax</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#090912;color:#f0f0f8;font-family:'Outfit',sans-serif;min-height:100vh}}
a{{color:inherit;text-decoration:none}}
.btn{{display:inline-flex;align-items:center;gap:.5rem;padding:.6rem 1.4rem;border-radius:10px;border:none;font-family:'Outfit',sans-serif;font-size:.9rem;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s}}
.btn-red{{background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff}}
.btn-red:hover{{opacity:.85}}
input{{width:100%;background:#11111e;border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:10px;padding:.75rem 1rem;font-family:'Outfit',sans-serif;font-size:.95rem;outline:none;transition:border-color .2s}}
input:focus{{border-color:#e8173a}}
label{{display:block;font-size:.8rem;color:#8888aa;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem}}
.form-group{{margin-bottom:1.25rem}}
</style></head><body>{content}</body></html>''')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')


# ==========================
# DASHBOARD
# ==========================

@admin_bp.route('/')
@admin_required
def dashboard():
    movies = load_movies()
    qr_image = get_qr_image()

    # Stats
    total_movies = len(movies)

    # Bookings count
    bookings_file = 'bookings.json'
    total_bookings = 0
    total_revenue = 0
    if os.path.exists(bookings_file):
        with open(bookings_file, 'r') as f:
            try:
                bookings = json.load(f)
                total_bookings = len(bookings)
                total_revenue = sum(b.get('total_price', 0) for b in bookings if isinstance(b, dict))
            except:
                pass

    # Users count
    users_file = 'users.json'
    total_users = 0
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            try:
                users = json.load(f)
                total_users = len(users)
            except:
                pass

    def fmt(n):
        return f"Rp {int(n):,}".replace(",", ".")

    stats_html = f'''
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1rem;margin-bottom:2rem;">
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:.5rem;">🎬</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_movies}</div>
        <div style="color:#8888aa;font-size:.85rem;">Total Film</div>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:.5rem;">🎟️</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;background:linear-gradient(135deg,#059669,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_bookings}</div>
        <div style="color:#8888aa;font-size:.85rem;">Total Booking</div>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:.5rem;">👥</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;background:linear-gradient(135deg,#7c3aed,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_users}</div>
        <div style="color:#8888aa;font-size:.85rem;">Total User</div>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:.5rem;">💰</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;background:linear-gradient(135deg,#d97706,#fbbf24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{fmt(total_revenue)}</div>
        <div style="color:#8888aa;font-size:.85rem;">Total Pendapatan</div>
      </div>
    </div>
    '''

    # Movie table
    rows = ''
    for m in movies:
        poster = m.get('poster', '')
        poster_html = f'<img src="{poster}" style="width:40px;height:56px;object-fit:cover;border-radius:6px;" onerror="this.style.display=\'none\'">' if poster else '<div style="width:40px;height:56px;background:#2a2a3e;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🎬</div>'
        rows += f'''
        <tr>
          <td>{poster_html}</td>
          <td style="font-weight:600;">{m.get("title","")}</td>
          <td><span style="background:rgba(232,23,58,.15);color:#f87171;padding:.2rem .6rem;border-radius:6px;font-size:.8rem;">{m.get("genre","")}</span></td>
          <td style="color:#fbbf24;">Rp {int(m.get("price",0)):,}".replace(",",".")</td>
          <td>
            <a href="/admin/edit/{m["id"]}" class="btn btn-yellow btn-sm">✏️ Edit</a>
            <a href="/admin/delete/{m["id"]}" class="btn btn-danger btn-sm" onclick="return confirm('Hapus film ini?')">🗑️ Hapus</a>
          </td>
        </tr>'''

    qr_html = ''
    if qr_image:
        qr_html = f'''
        <div style="display:flex;align-items:flex-start;gap:1.5rem;flex-wrap:wrap;">
          <img src="/static/qr/{qr_image}" style="width:180px;height:180px;object-fit:contain;background:#fff;padding:.5rem;border-radius:12px;">
          <div>
            <div style="color:#34d399;font-size:.9rem;font-weight:600;margin-bottom:.5rem;">✅ QR aktif: {qr_image}</div>
            <a href="/admin/upload-qr" class="btn btn-ghost btn-sm">🔄 Ganti QR</a>
          </div>
        </div>'''
    else:
        qr_html = '''
        <div style="text-align:center;padding:2rem;color:#8888aa;">
          <div style="font-size:3rem;margin-bottom:.75rem;">📷</div>
          <div style="margin-bottom:1rem;">QR pembayaran belum diupload</div>
          <a href="/admin/upload-qr" class="btn btn-red">⬆️ Upload QR Sekarang</a>
        </div>'''

    content = f'''
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.75rem;">
      <div>
        <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;">Dashboard</h1>
        <div style="color:#8888aa;font-size:.85rem;">Selamat datang di panel admin CineMax</div>
      </div>
    </div>

    {stats_html}

    <div style="display:grid;grid-template-columns:1fr 320px;gap:1.5rem;align-items:start;">
      <div class="card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;">
          <h2 style="font-size:1.1rem;font-weight:700;">🎬 Daftar Film</h2>
          <a href="/admin/add" class="btn btn-red btn-sm">+ Tambah Film</a>
        </div>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr>
                <th>Poster</th><th>Judul</th><th>Genre</th><th>Harga</th><th>Aksi</th>
              </tr>
            </thead>
            <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;padding:2rem;color:#8888aa;">Belum ada film</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;">
          <h2 style="font-size:1.1rem;font-weight:700;">💳 QR Pembayaran</h2>
          <a href="/admin/upload-qr" class="btn btn-ghost btn-sm">⬆️ Upload</a>
        </div>
        {qr_html}
      </div>
    </div>
    '''

    return make_response(admin_base(content, 'dashboard'))


# ==========================
# ADD MOVIE
# ==========================

@admin_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_movie():
    if request.method == 'POST':
        movies = load_movies()

        # Handle poster: file upload atau URL
        poster_val = ''
        if 'poster_file' in request.files:
            f = request.files['poster_file']
            if f and f.filename != '' and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                # Tambah prefix id biar unik
                filename = f"poster_{get_new_id(movies)}_{filename}"
                f.save(os.path.join(POSTER_FOLDER, filename))
                poster_val = f'/static/posters/{filename}'

        if not poster_val:
            poster_val = request.form.get('poster_url', '').strip()

        showtimes_raw = request.form.get('showtimes', '')
        showtimes = [s.strip() for s in showtimes_raw.split(',') if s.strip()]

        new_movie = {
            "id": get_new_id(movies),
            "title": request.form.get('title', ''),
            "genre": request.form.get('genre', ''),
            "price": int(request.form.get('price', 0)),
            "description": request.form.get('description', ''),
            "poster": poster_val,
            "duration": request.form.get('duration', ''),
            "rating": request.form.get('rating', 'SU'),
            "score": request.form.get('score', '0.0'),
            "director": request.form.get('director', ''),
            "showtimes": showtimes,
        }

        movies.append(new_movie)
        save_movies(movies)
        flash_msg('success', f'Film "{new_movie["title"]}" berhasil ditambahkan!')
        return redirect('/admin')

    content = '''
    <div style="max-width:720px;">
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;">
        <a href="/admin" class="btn btn-ghost btn-sm">← Kembali</a>
        <div>
          <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;">Tambah Film Baru</h1>
          <div style="color:#8888aa;font-size:.85rem;">Isi data film yang akan ditampilkan</div>
        </div>
      </div>

      <form method="POST" enctype="multipart/form-data">
        <div class="card" style="margin-bottom:1.25rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">📝 Informasi Film</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
            <div class="form-group" style="grid-column:1/-1;">
              <label>Judul Film *</label>
              <input type="text" name="title" placeholder="Contoh: Avatar: The Way of Water" required>
            </div>
            <div class="form-group">
              <label>Genre *</label>
              <input type="text" name="genre" placeholder="Contoh: Action, Drama">
            </div>
            <div class="form-group">
              <label>Durasi</label>
              <input type="text" name="duration" placeholder="Contoh: 2j 42m">
            </div>
            <div class="form-group">
              <label>Harga Tiket (Rp) *</label>
              <input type="number" name="price" placeholder="Contoh: 50000" required>
            </div>
            <div class="form-group">
              <label>Rating Usia</label>
              <select name="rating">
                <option value="SU">SU - Semua Umur</option>
                <option value="13+">13+</option>
                <option value="17+">17+</option>
                <option value="21+">21+</option>
              </select>
            </div>
            <div class="form-group">
              <label>Skor (0.0 - 10.0)</label>
              <input type="text" name="score" placeholder="Contoh: 7.8" value="0.0">
            </div>
            <div class="form-group">
              <label>Sutradara</label>
              <input type="text" name="director" placeholder="Contoh: James Cameron">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Jam Tayang (pisahkan dengan koma)</label>
              <input type="text" name="showtimes" placeholder="Contoh: 10:00, 13:30, 19:00">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Deskripsi</label>
              <textarea name="description" placeholder="Sinopsis film..."></textarea>
            </div>
          </div>
        </div>

        <div class="card" style="margin-bottom:1.5rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">🖼️ Poster Film</h3>
          <div style="background:#11111e;border:2px dashed rgba(255,255,255,.1);border-radius:12px;padding:1.5rem;text-align:center;margin-bottom:1rem;" id="drop-area">
            <div style="font-size:2.5rem;margin-bottom:.5rem;">📤</div>
            <div style="font-weight:600;margin-bottom:.25rem;">Upload dari Penyimpanan</div>
            <div style="color:#8888aa;font-size:.85rem;margin-bottom:1rem;">JPG, PNG, WEBP (maks. 5MB)</div>
            <label for="poster_file" class="btn btn-ghost" style="cursor:pointer;">Pilih File</label>
            <input type="file" id="poster_file" name="poster_file" accept="image/*" style="display:none" onchange="previewPoster(this)">
          </div>
          <div id="poster-preview" style="display:none;margin-bottom:1rem;text-align:center;">
            <img id="preview-img" style="max-height:200px;border-radius:10px;border:1px solid rgba(255,255,255,.1);">
            <div style="margin-top:.5rem;font-size:.85rem;color:#34d399;">✅ File dipilih</div>
          </div>
          <div style="text-align:center;color:#8888aa;font-size:.85rem;margin-bottom:.75rem;">— atau gunakan URL —</div>
          <div class="form-group" style="margin:0;">
            <label>URL Poster (opsional jika sudah upload)</label>
            <input type="text" name="poster_url" placeholder="https://..." id="poster_url">
          </div>
        </div>

        <div style="display:flex;gap:1rem;">
          <button type="submit" class="btn btn-red" style="flex:1;justify-content:center;padding:.8rem;">🎬 Simpan Film</button>
          <a href="/admin" class="btn btn-ghost">Batal</a>
        </div>
      </form>
    </div>

    <script>
    function previewPoster(input) {
      const preview = document.getElementById('poster-preview');
      const img = document.getElementById('preview-img');
      const urlInput = document.getElementById('poster_url');
      if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          img.src = e.target.result;
          preview.style.display = 'block';
          urlInput.value = '';
        };
        reader.readAsDataURL(input.files[0]);
      }
    }
    </script>
    '''

    return make_response(admin_base(content, 'films'))


# ==========================
# EDIT MOVIE
# ==========================

@admin_bp.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    movies = load_movies()
    movie = next((m for m in movies if m['id'] == movie_id), None)

    if not movie:
        flash_msg('danger', 'Film tidak ditemukan')
        return redirect('/admin')

    if request.method == 'POST':
        # Handle poster baru
        poster_val = movie.get('poster', '')

        if 'poster_file' in request.files:
            f = request.files['poster_file']
            if f and f.filename != '' and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                filename = f"poster_{movie_id}_{filename}"
                f.save(os.path.join(POSTER_FOLDER, filename))
                poster_val = f'/static/posters/{filename}'

        new_url = request.form.get('poster_url', '').strip()
        if new_url:
            poster_val = new_url

        showtimes_ra = request.form.get('showtimes', '')
        showtimes = [s.strip() for s in showtimes_raw.split(',') if s.strip()]

        new_movie = {
            "id": get_new_id(movies),
            "title": request.form.get('title', ''),
            "genre": request.form.get('genre', ''),
            "price": int(request.form.get('price', 0)),
            "description": request.form.get('description', ''),
            "poster": poster_val,
            "duration": request.form.get('duration', ''),
            "rating": request.form.get('rating', 'SU'),
            "score": request.form.get('score', '0.0'),
            "director": request.form.get('director', ''),
            "showtimes": showtimes,
        }

        movies.append(new_movie)
        save_movies(movies)
        flash_msg('success', f'Film "{new_movie["title"]}" berhasil ditambahkan!')
        return redirect('/admin')

    content = '''
    <div style="max-width:720px;">
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;">
        <a href="/admin" class="btn btn-ghost btn-sm">← Kembali</a>
        <div>
          <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;">Tambah Film Baru</h1>
          <div style="color:#8888aa;font-size:.85rem;">Isi data film yang akan ditampilkan</div>
        </div>
      </div>

      <form method="POST" enctype="multipart/form-data">
        <div class="card" style="margin-bottom:1.25rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">📝 Informasi Film</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
            <div class="form-group" style="grid-column:1/-1;">
              <label>Judul Film *</label>
              <input type="text" name="title" placeholder="Contoh: Avatar: The Way of Water" required>
            </div>
            <div class="form-group">
              <label>Genre *</label>
              <input type="text" name="genre" placeholder="Contoh: Action, Drama">
            </div>
            <div class="form-group">
              <label>Durasi</label>
              <input type="text" name="duration" placeholder="Contoh: 2j 42m">
            </div>
            <div class="form-group">
              <label>Harga Tiket (Rp) *</label>
              <input type="number" name="price" placeholder="Contoh: 50000" required>
            </div>
            <div class="form-group">
              <label>Rating Usia</label>
              <select name="rating">
                <option value="SU">SU - Semua Umur</option>
                <option value="13+">13+</option>
                <option value="17+">17+</option>
                <option value="21+">21+</option>
              </select>
            </div>
            <div class="form-group">
              <label>Skor (0.0 - 10.0)</label>
              <input type="text" name="score" placeholder="Contoh: 7.8" value="0.0">
            </div>
            <div class="form-group">
              <label>Sutradara</label>
              <input type="text" name="director" placeholder="Contoh: James Cameron">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Jam Tayang (pisahkan dengan koma)</label>
              <input type="text" name="showtimes" placeholder="Contoh: 10:00, 13:30, 19:00">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Deskripsi</label>
              <textarea name="description" placeholder="Sinopsis film..."></textarea>
            </div>
          </div>
        </div>

        <div class="card" style="margin-bottom:1.5rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">🖼️ Poster Film</h3>
          <div style="background:#11111e;border:2px dashed rgba(255,255,255,.1);border-radius:12px;padding:1.5rem;text-align:center;margin-bottom:1rem;" id="drop-area">
            <div style="font-size:2.5rem;margin-bottom:.5rem;">📤</div>
            <div style="font-weight:600;margin-bottom:.25rem;">Upload dari Penyimpanan</div>
            <div style="color:#8888aa;font-size:.85rem;margin-bottom:1rem;">JPG, PNG, WEBP (maks. 5MB)</div>
            <label for="poster_file" class="btn btn-ghost" style="cursor:pointer;">Pilih File</label>
            <input type="file" id="poster_file" name="poster_file" accept="image/*" style="display:none" onchange="previewPoster(this)">
          </div>
          <div id="poster-preview" style="display:none;margin-bottom:1rem;text-align:center;">
            <img id="preview-img" style="max-height:200px;border-radius:10px;border:1px solid rgba(255,255,255,.1);">
            <div style="margin-top:.5rem;font-size:.85rem;color:#34d399;">✅ File dipilih</div>
          </div>
          <div style="text-align:center;color:#8888aa;font-size:.85rem;margin-bottom:.75rem;">— atau gunakan URL —</div>
          <div class="form-group" style="margin:0;">
            <label>URL Poster (opsional jika sudah upload)</label>
            <input type="text" name="poster_url" placeholder="https://..." id="poster_url">
          </div>
        </div>

        <div style="display:flex;gap:1rem;">
          <button type="submit" class="btn btn-red" style="flex:1;justify-content:center;padding:.8rem;">🎬 Simpan Film</button>
          <a href="/admin" class="btn btn-ghost">Batal</a>
        </div>
      </form>
    </div>

    <script>
    function previewPoster(input) {
      const preview = document.getElementById('poster-preview');
      const img = document.getElementById('preview-img');
      const urlInput = document.getElementById('poster_url');
      if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          img.src = e.target.result;
          preview.style.display = 'block';
          urlInput.value = '';
        };
        reader.readAsDataURL(input.files[0]);
      }
    }
    </script>
    '''

    return make_response(admin_base(content, 'films'))


# ==========================
# EDIT MOVIE
# ==========================

@admin_bp.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    movies = load_movies()
    movie = next((m for m in movies if m['id'] == movie_id), None)

    if not movie:
        flash_msg('danger', 'Film tidak ditemukan')
        return redirect('/admin')

    if request.method == 'POST':
        # Handle poster baru
        poster_val = movie.get('poster', '')

        if 'poster_file' in request.files:
            f = request.files['poster_file']
            if f and f.filename != '' and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                filename = f"poster_{movie_id}_{filename}"
                f.save(os.path.join(POSTER_FOLDER, filename))
                poster_val = f'/static/posters/{filename}'

        new_url = request.form.get('poster_url', '').strip()
        if new_url:
            poster_val = new_url

        showtimes_raw = request.form.get('showtimes', '')
        showtimes = [s.strip() for s in showtimes_raw.split(',') if s.strip()]

        movie['title'] = request.form.get('title', '')
        movie['genre'] = request.form.get('genre', '')
        movie['price'] = int(request.form.get('price', 0))
        movie['description'] = request.form.get('description', '')
        movie['poster'] = poster_val
        movie['duration'] = request.form.get('duration', '')
        movie['rating'] = request.form.get('rating', 'SU')
        movie['score'] = request.form.get('score', '0.0')
        movie['director'] = request.form.get('director', '')
        movie['showtimes'] = showtimes

        save_movies(movies)
        flash_msg('success', f'Film "{movie["title"]}" berhasil diperbarui!')
        return redirect('/admin')

    m = movie
    showtimes_str = ', '.join(m.get('showtimes', []))
    poster_preview = ''
    if m.get('poster'):
        poster_preview = f'''
        <div style="margin-bottom:1rem;text-align:center;">
          <div style="color:#8888aa;font-size:.8rem;margin-bottom:.5rem;text-transform:uppercase;letter-spacing:1px;">Poster Saat Ini</div>
          <img src="{m['poster']}" style="max-height:180px;border-radius:10px;border:1px solid rgba(255,255,255,.1);" onerror="this.style.display='none'">
        </div>'''

    rating_opts = ''
    for r in ['SU', '13+', '17+', '21+']:
        sel = 'selected' if m.get('rating') == r else ''
        rating_opts += f'<option value="{r}" {sel}>{r}</option>'

    content = f'''
    <div style="max-width:720px;">
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;">
        <a href="/admin" class="btn btn-ghost btn-sm">← Kembali</a>
        <div>
          <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;">Edit Film</h1>
          <div style="color:#8888aa;font-size:.85rem;">ID #{m["id"]} — {m["title"]}</div>
        </div>
      </div>

      <form method="POST" enctype="multipart/form-data">
        <div class="card" style="margin-bottom:1.25rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">📝 Informasi Film</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
            <div class="form-group" style="grid-column:1/-1;">
              <label>Judul Film *</label>
              <input type="text" name="title" value="{m.get('title','')}" required>
            </div>
            <div class="form-group">
              <label>Genre</label>
              <input type="text" name="genre" value="{m.get('genre','')}">
            </div>
            <div class="form-group">
              <label>Durasi</label>
              <input type="text" name="duration" value="{m.get('duration','')}">
            </div>
            <div class="form-group">
              <label>Harga Tiket (Rp) *</label>
              <input type="number" name="price" value="{m.get('price',0)}" required>
            </div>
            <div class="form-group">
              <label>Rating Usia</label>
              <select name="rating">{rating_opts}</select>
            </div>
            <div class="form-group">
              <label>Skor</label>
              <input type="text" name="score" value="{m.get('score','0.0')}">
            </div>
            <div class="form-group">
              <label>Sutradara</label>
              <input type="text" name="director" value="{m.get('director','')}">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Jam Tayang (pisahkan koma)</label>
              <input type="text" name="showtimes" value="{showtimes_str}">
            </div>
            <div class="form-group" style="grid-column:1/-1;">
              <label>Deskripsi</label>
              <textarea name="description">{m.get('description','')}</textarea>
            </div>
          </div>
        </div>

        <div class="card" style="margin-bottom:1.5rem;">
          <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">🖼️ Poster Film</h3>
          {poster_preview}
          <div style="background:#11111e;border:2px dashed rgba(255,255,255,.1);border-radius:12px;padding:1.25rem;text-align:center;margin-bottom:1rem;">
            <div style="font-size:2rem;margin-bottom:.25rem;">📤</div>
            <div style="font-size:.9rem;font-weight:600;margin-bottom:.25rem;">Upload Poster Baru</div>
            <div style="color:#8888aa;font-size:.8rem;margin-bottom:.75rem;">Biarkan kosong untuk pakai poster sebelumnya</div>
            <label for="poster_file" class="btn btn-ghost btn-sm" style="cursor:pointer;">Pilih File</label>
            <input type="file" id="poster_file" name="poster_file" accept="image/*" style="display:none" onchange="previewNew(this)">
          </div>
          <div id="new-preview" style="display:none;text-align:center;margin-bottom:1rem;">
            <img id="new-img" style="max-height:160px;border-radius:10px;border:1px solid rgba(255,255,255,.1);">
            <div style="margin-top:.5rem;font-size:.85rem;color:#34d399;">✅ File baru dipilih</div>
          </div>
          <div style="text-align:center;color:#8888aa;font-size:.85rem;margin-bottom:.75rem;">— atau ganti dengan URL —</div>
          <div class="form-group" style="margin:0;">
            <label>URL Poster Baru (opsional)</label>
            <input type="text" name="poster_url" placeholder="https://..." id="poster_url">
          </div>
        </div>

        <div style="display:flex;gap:1rem;">
          <button type="submit" class="btn btn-green" style="flex:1;justify-content:center;padding:.8rem;">💾 Simpan Perubahan</button>
          <a href="/admin" class="btn btn-ghost">Batal</a>
        </div>
      </form>
    </div>

    <script>
    function previewNew(input) {{
      const preview = document.getElementById('new-preview');
      const img = document.getElementById('new-img');
      if (input.files && input.files[0]) {{
        const reader = new FileReader();
        reader.onload = e => {{
          img.src = e.target.result;
          preview.style.display = 'block';
        }};
        reader.readAsDataURL(input.files[0]);
      }}
    }}
    </script>
    '''

    return make_response(admin_base(content, 'films'))


# ==========================
# DELETE MOVIE
# ==========================

@admin_bp.route('/delete/<int:movie_id>')
@admin_required
def delete_movie(movie_id):
    movies = load_movies()
    title = next((m['title'] for m in movies if m['id'] == movie_id), 'Film')
    movies = [m for m in movies if m['id'] != movie_id]
    save_movies(movies)
    flash_msg('warning', f'Film "{title}" berhasil dihapus.')
    return redirect('/admin')


# ==========================
# UPLOAD QR
# ==========================

@admin_bp.route('/upload-qr', methods=['GET', 'POST'])
@admin_required
def upload_qr():
    current_qr = get_qr_image()

    if request.method == 'POST':
        if 'qr_image' not in request.files:
            flash_msg('danger', 'Tidak ada file dipilih')
            return redirect(request.url)

        file = request.files['qr_image']
        if file.filename == '':
            flash_msg('danger', 'File kosong')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash_msg('danger', 'Format tidak didukung (gunakan JPG/PNG/WEBP)')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(QR_FOLDER, filename)
        file.save(filepath)

        with open(QR_JSON, 'w') as f:
            json.dump({"qr_image": filename}, f, indent=4)

        flash_msg('success', 'QR pembayaran berhasil diupload!')
        return redirect('/admin')

    current_qr_html = ''
    if current_qr:
        current_qr_html = f'''
        <div class="card" style="margin-bottom:1.5rem;text-align:center;">
          <div style="color:#8888aa;font-size:.8rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:1rem;">QR Aktif Saat Ini</div>
          <img src="/static/qr/{current_qr}" style="width:200px;height:200px;object-fit:contain;background:#fff;padding:.75rem;border-radius:12px;margin-bottom:.75rem;">
          <div style="color:#34d399;font-size:.9rem;font-weight:600;">✅ {current_qr}</div>
        </div>'''

    content = f'''
    <div style="max-width:500px;">
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;">
        <a href="/admin" class="btn btn-ghost btn-sm">← Kembali</a>
        <div>
          <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;">Upload QR Pembayaran</h1>
          <div style="color:#8888aa;font-size:.85rem;">QR QRIS/DANA untuk halaman pembayaran</div>
        </div>
      </div>

      {current_qr_html}

      <div class="card">
        <h3 style="font-size:1rem;font-weight:700;margin-bottom:1.25rem;color:#e8173a;">📷 {"Ganti" if current_qr else "Upload"} QR Code</h3>
        <form method="POST" enctype="multipart/form-data">
          <div style="background:#11111e;border:2px dashed rgba(255,255,255,.12);border-radius:14px;padding:2rem;text-align:center;margin-bottom:1.25rem;" id="qr-drop">
            <div style="font-size:3rem;margin-bottom:.75rem;">🖼️</div>
            <div style="font-weight:600;margin-bottom:.25rem;">Pilih file QR dari penyimpanan</div>
            <div style="color:#8888aa;font-size:.85rem;margin-bottom:1.25rem;">Format: JPG, PNG, WEBP</div>
            <label for="qr_file" class="btn btn-red" style="cursor:pointer;">📂 Buka Penyimpanan</label>
            <input type="file" id="qr_file" name="qr_image" accept="image/*" style="display:none" onchange="previewQR(this)">
          </div>
          <div id="qr-preview" style="display:none;text-align:center;margin-bottom:1.25rem;">
            <img id="qr-img" style="width:180px;height:180px;object-fit:contain;background:#fff;padding:.5rem;border-radius:12px;">
            <div style="margin-top:.75rem;color:#34d399;font-size:.9rem;font-weight:600;" id="qr-name">✅ Siap diupload</div>
          </div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;padding:.8rem;">⬆️ Upload QR</button>
        </form>
      </div>
    </div>

    <script>
    function previewQR(input) {{
      if (input.files && input.files[0]) {{
        const reader = new FileReader();
        reader.onload = e => {{
          document.getElementById('qr-img').src = e.target.result;
          document.getElementById('qr-preview').style.display = 'block';
          document.getElementById('qr-name').textContent = '✅ ' + input.files[0].name;
        }};
        reader.readAsDataURL(input.files[0]);
      }}
    }}
    </script>
    '''

    return make_response(admin_base(content, 'payment_settings'))
