import hashlib, os, base64
from flask import Blueprint, request, redirect, session, make_response
from helpers import flash_msg, admin_base
from database import get_db, save_db, get_movies, next_movie_id, fmt_rp

admin_bp = Blueprint('admin', __name__)

# Konfigurasi Folder Upload
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def admin_required():
    return session.get('role') == 'admin'

# ── ADMIN LOGIN & DASHBOARD ───────────────────────────────────────────────────
@admin_bp.route('/admin', methods=['GET','POST'])
def admin():
    if not admin_required():
        if request.method == 'POST':
            db = get_db()
            # Login check
            if request.form['username'] == db['admin']['username'] and \
               hashlib.md5(request.form['password'].encode()).hexdigest() == db['admin']['password']:
                session['role'] = 'admin'
                flash_msg('Login admin berhasil!', 'success')
                return redirect('/admin')
            flash_msg('Kredensial salah!', 'danger')
        
        # Template Login (Internal)
        return _render_login_page()

    db = get_db()
    total_rev = sum(b['total'] for b in db['bookings'])
    
    content = f'''
    <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:1.75rem;">📊 Dashboard</h1>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem;">
      <div class="card"><div style="color:#888;">Total Booking</div><div style="font-size:2rem;color:#e8173a;">{len(db['bookings'])}</div></div>
      <div class="card"><div style="color:#888;">Revenue</div><div style="font-size:1.5rem;color:#34d399;">{fmt_rp(total_rev)}</div></div>
      <div class="card"><div style="color:#888;">Film</div><div style="font-size:2rem;">{len(db['movies'])}</div></div>
      <div class="card"><div style="color:#888;">User</div><div style="font-size:2rem;">{len(db['users'])}</div></div>
    </div>
    <div class="card">
        <h2 style="font-family:'Bebas Neue';margin-bottom:1rem;">Aksi Cepat</h2>
        <div style="display:flex;gap:1rem;">
            <a href="/admin/films" class="btn btn-red">Kelola Film & Tiket</a>
            <a href="/admin/payment-settings" class="btn btn-yellow">Update QRIS</a>
        </div>
    </div>
    '''
    return make_response(admin_base(content, 'dashboard'))

# ── FITUR: KELOLA PEMBAYARAN (UPLOAD QR) ──────────────────────────────────────
@admin_bp.route('/admin/payment-settings', methods=['GET','POST'])
def admin_payment_settings():
    if not admin_required(): return redirect('/admin')

    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'upload':
            file = request.files.get('qr_file')
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in {'png', 'jpg', 'jpeg', 'webp'}:
                    filename = f"qris_latest.{ext}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    
                    # Konversi ke Base64 agar database tetap portable
                    with open(filepath, "rb") as f:
                        encoded_string = base64.b64encode(f.read()).decode()
                    
                    db['payment_settings'] = {'qris_image': f"data:image/{ext};base64,{encoded_string}"}
                    save_db(db)
                    flash_msg('QRIS Berhasil diperbarui!', 'success')
                else:
                    flash_msg('Format file tidak didukung.', 'danger')
        
        elif action == 'delete':
            db['payment_settings']['qris_image'] = ''
            save_db(db)
            flash_msg('QRIS dihapus.', 'success')

        return redirect('/admin/payment-settings')

    current_qr = db.get('payment_settings', {}).get('qris_image', '')
    content = f'''
    <h1 style="font-family:'Bebas Neue';font-size:2rem;margin-bottom:1.5rem;">⚙️ Pengaturan Pembayaran</h1>
    <div class="card">
        <h3>Upload QR Code (QRIS)</h3>
        <p style="color:#888; font-size:0.9rem; margin-bottom:1rem;">Gambar ini akan muncul di halaman checkout user.</p>
        
        <form method="POST" enctype="multipart/form-data" style="margin-bottom:1.5rem;">
            <input type="hidden" name="action" value="upload">
            <input type="file" name="qr_file" accept="image/*" onchange="previewImg(this)" style="margin-bottom:1rem; display:block;">
            <div id="pv_container" style="margin-bottom:1rem; {'display:none' if not current_qr else ''}">
                <img id="pv" src="{current_qr}" style="max-width:200px; border:4px solid #fff; border-radius:10px;">
            </div>
            <button type="submit" class="btn btn-green">Simpan QR Code</button>
        </form>

        {f'<form method="POST"><input type="hidden" name="action" value="delete"><button class="btn btn-ghost" style="color:#f87171">Hapus QR Sekarang</button></form>' if current_qr else ''}
    </div>
    <script>
    function previewImg(input) {{
        if (input.files && input.files[0]) {{
            var reader = new FileReader();
            reader.onload = function(e) {{
                document.getElementById('pv').src = e.target.result;
                document.getElementById('pv_container').style.display = 'block';
            }}
            reader.readAsDataURL(input.files[0]);
        }}
    }}
    </script>
    '''
    return make_response(admin_base(content, 'payment_settings'))

# ── FITUR: CRUD FILM (PENGATURAN TIKET) ────────────────────────────────────────
@admin_bp.route('/admin/films')
def admin_films():
    if not admin_required(): return redirect('/admin')
    db = get_db()
    movies = db.get('movies', [])
    
    rows = ''
    for m in movies:
        rows += f'''
        <tr>
            <td><img src="{m['poster']}" width="40" style="border-radius:4px;"></td>
            <td><b>{m['title']}</b></td>
            <td>{m['rating']}</td>
            <td>{", ".join(m['showtimes'])}</td>
            <td>
                <a href="/admin/films/edit/{m['id']}" class="btn btn-sm btn-yellow">Edit</a>
                <a href="/admin/films/delete/{m['id']}" class="btn btn-sm btn-danger" onclick="return confirm('Hapus film?')">Hapus</a>
            </td>
        </tr>'''

    content = f'''
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
        <h1 style="font-family:'Bebas Neue';font-size:2rem;">🎬 Kelola Film & Tiket</h1>
        <a href="/admin/films/add" class="btn btn-green">+ Tambah Film</a>
    </div>
    <div class="card">
        <table style="width:100%; text-align:left; border-collapse:collapse;">
            <thead>
                <tr style="color:#888; border-bottom:1px solid #333;">
                    <th>Poster</th><th>Judul</th><th>Rating</th><th>Jam Tayang</th><th>Aksi</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return make_response(admin_base(content, 'films'))

@admin_bp.route('/admin/films/add', methods=['GET', 'POST'])
@admin_bp.route('/admin/films/edit/<int:movie_id>', methods=['GET', 'POST'])
def admin_film_form(movie_id=None):
    if not admin_required(): return redirect('/admin')
    db = get_db()
    
    # Mode Edit atau Tambah
    movie = next((m for m in db['movies'] if m['id'] == movie_id), None) if movie_id else None

    if request.method == 'POST':
        data = {
            "id": movie_id if movie_id else next_movie_id(),
            "title": request.form.get('title'),
            "genre": request.form.get('genre'),
            "duration": request.form.get('duration'),
            "rating": request.form.get('rating'),
            "score": float(request.form.get('score', 0)),
            "poster": request.form.get('poster'),
            "description": request.form.get('description'),
            "showtimes": [t.strip() for t in request.form.get('showtimes').split(',')]
        }
        
        if movie_id:
            db['movies'] = [data if m['id'] == movie_id else m for m in db['movies']]
        else:
            db['movies'].append(data)
            
        save_db(db)
        flash_msg(f"Film {'diupdate' if movie_id else 'ditambahkan'}!", "success")
        return redirect('/admin/films')

    # Form UI
    content = f'''
    <h1 style="font-family:'Bebas Neue';">{'Edit' if movie_id else 'Tambah'} Film</h1>
    <div class="card">
        <form method="POST">
            <div class="fg"><label>Judul Film</label><input type="text" name="title" value="{movie['title'] if movie else ''}" required></div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                <div class="fg"><label>Genre</label><input type="text" name="genre" value="{movie['genre'] if movie else ''}"></div>
                <div class="fg"><label>Durasi</label><input type="text" name="duration" value="{movie['duration'] if movie else ''}"></div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                <div class="fg"><label>Rating Usia</label><input type="text" name="rating" value="{movie['rating'] if movie else 'SU'}"></div>
                <div class="fg"><label>Skor IMDb</label><input type="number" step="0.1" name="score" value="{movie['score'] if movie else '0'}"></div>
            </div>
            <div class="fg"><label>URL Poster</label><input type="text" name="poster" value="{movie['poster'] if movie else ''}"></div>
            <div class="fg"><label>Jam Tayang (Pisahkan dengan koma)</label><input type="text" name="showtimes" value="{', '.join(movie['showtimes']) if movie else '12:00, 15:00, 19:00'}"></div>
            <div class="fg"><label>Sinopsis</label><textarea name="description" style="width:100%; background:#111; color:#fff; border-radius:8px; padding:10px;">{movie['description'] if movie else ''}</textarea></div>
            <button type="submit" class="btn btn-red" style="width:100%">{ 'Update Data' if movie_id else 'Simpan Film' }</button>
        </form>
    </div>'''
    return make_response(admin_base(content, 'films'))

@admin_bp.route('/admin/films/delete/<int:movie_id>')
def admin_film_delete(movie_id):
    if not admin_required(): return redirect('/admin')
    db = get_db()
    db['movies'] = [m for m in db['movies'] if m['id'] != movie_id]
    save_db(db)
    flash_msg("Film berhasil dihapus.", "success")
    return redirect('/admin/films')

# ── ADMIN LOGOUT ──────────────────────────────────────────────────────────────
@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('role', None)
    return redirect('/admin')

def _render_login_page():
    # Fungsi pembantu untuk merender halaman login jika belum admin
    # (Kode CSS & HTML login tetap sama seperti file asli Anda)
    pass 
    
