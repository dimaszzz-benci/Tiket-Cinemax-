import hashlib, os, base64
from flask import Blueprint, request, redirect, session, make_response
from helpers import flash_msg, admin_base
from database import get_db, save_db, get_movies, next_movie_id, fmt_rp

admin_bp = Blueprint('admin', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def admin_required():
    return session.get('role') == 'admin'


# ── ADMIN LOGIN / DASHBOARD ───────────────────────────────────────────────────
@admin_bp.route('/admin', methods=['GET','POST'])
def admin():
    if not admin_required():
        if request.method == 'POST':
            db = get_db()
            if request.form['username'] == db['admin']['username'] and \
               hashlib.md5(request.form['password'].encode()).hexdigest() == db['admin']['password']:
                session['role'] = 'admin'
                flash_msg('Login admin berhasil! Selamat datang.', 'success')
                return redirect('/admin')
            flash_msg('Username atau password admin salah!', 'danger')
        flashes_raw = session.pop('_flashes', [])
        session.modified = True
        flash_html = ''
        for cat, msg in flashes_raw:
            colors = {'success':'#34d399','danger':'#f87171'}
            bgs = {'success':'rgba(16,185,129,0.12)','danger':'rgba(232,23,58,0.12)'}
            c = colors.get(cat,'#fff'); bg = bgs.get(cat,'rgba(255,255,255,.1)')
            flash_html += f'<div style="padding:.75rem 1.25rem;margin:.5rem 0;border-radius:10px;background:{bg};color:{c};font-size:.9rem;font-weight:500;">{msg}</div>'
        return make_response(f'''<!DOCTYPE html><html lang="id"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Admin Login - CineMax</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#090912;color:#f0f0f8;font-family:'Outfit',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;background-image:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(232,23,58,.1),transparent);}}
input{{width:100%;background:#11111e;border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:10px;padding:.75rem 1rem;font-family:'Outfit',sans-serif;font-size:.95rem;outline:none;}}
input:focus{{border-color:#e8173a}}label{{display:block;font-size:.8rem;color:#8888aa;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem}}.fg{{margin-bottom:1.25rem}}</style></head>
<body><div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:24px;padding:2.5rem;width:100%;max-width:420px;">
  <div style="text-align:center;margin-bottom:2rem;">
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🔐 Admin Panel</div>
    <p style="color:#8888aa;font-size:.9rem;margin-top:.3rem;">CineMax Dashboard</p>
  </div>
  {flash_html}
  <form method="POST" style="margin-top:1rem;">
    <div class="fg"><label>Username Admin</label><input type="text" name="username" placeholder="Masukkan username" required/></div>
    <div class="fg"><label>Password Admin</label><input type="password" name="password" placeholder="Masukkan password" required/></div>
    <button type="submit" style="width:100%;background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff;border:none;border-radius:10px;padding:.8rem;font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;cursor:pointer;margin-top:.5rem;">Masuk ke Dashboard →</button>
  </form>
  <div style="margin-top:1.5rem;background:rgba(255,215,0,.08);border:1px solid rgba(255,215,0,.2);border-radius:10px;padding:1rem;">
    <p style="color:#ffd700;font-size:.85rem;font-weight:600;margin-bottom:.5rem;">🔑 Kredensial Default:</p>
    <p style="color:#aaa;font-size:.85rem;">Username: <strong style="color:#fff;">admin</strong></p>
    <p style="color:#aaa;font-size:.85rem;">Password: <strong style="color:#fff;">admin123</strong></p>
  </div>
  <p style="text-align:center;margin-top:1rem;"><a href="/" style="color:#8888aa;font-size:.85rem;">← Kembali ke Website</a></p>
</div></body></html>''')

    # Dashboard
    db = get_db()
    movies = db.get('movies', [])
    total_rev = sum(b['total'] for b in db['bookings'])
    recent = list(reversed(db['bookings']))[:5]
    recent_rows = ''.join(
        f'<tr><td style="font-family:monospace;font-size:.8rem;color:#8888aa;">{b["id"][:15]}...</td>'
        f'<td>{b["user"]}</td><td>{b["movie"][:20]}</td>'
        f'<td style="color:#e8173a;font-weight:700;">{fmt_rp(b["total"])}</td></tr>'
        for b in recent
    ) or '<tr><td colspan="4" style="text-align:center;color:#8888aa;padding:1rem;">Belum ada booking</td></tr>'

    qris_img = db.get('payment_settings', {}).get('qris_image', '')
    qris_status = f'<span style="color:#34d399;font-weight:600;">✅ QR Code sudah diatur</span>' if qris_img else f'<span style="color:#f87171;">❌ QR Code belum diatur</span>'

    content = f'''
    <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:1.75rem;">📊 Dashboard</h1>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem;">
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total Booking</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(db['bookings'])}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total User</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(db['users'])}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Film Tayang</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(movies)}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total Revenue</div><div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{fmt_rp(total_rev)}</div></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 320px;gap:1.5rem;margin-bottom:2rem;">
      <div class="card">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1rem;">🎟️ Booking Terbaru</h2>
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr><th>ID</th><th>User</th><th>Film</th><th>Total</th></tr></thead>
          <tbody>{recent_rows}</tbody>
        </table>
        <div style="margin-top:1rem;"><a href="/admin/bookings" class="btn btn-ghost btn-sm">Lihat Semua →</a></div>
      </div>
      <div class="card">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1rem;">💳 Status QRIS</h2>
        <p style="color:#8888aa;font-size:.9rem;margin-bottom:1rem;">{qris_status}</p>
        {'<img src="' + qris_img + '" style="width:100%;max-width:160px;border-radius:8px;display:block;margin-bottom:1rem;" onerror="this.style.display=\'none\'"/>' if qris_img else '<div style="width:120px;height:120px;border:2px dashed rgba(255,255,255,.1);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#8888aa;font-size:.8rem;text-align:center;margin-bottom:1rem;">QR Belum<br>diatur</div>'}
        <a href="/admin/payment-settings" class="btn btn-yellow btn-sm">⚙️ Atur QR Code</a>
      </div>
    </div>'''
    return make_response(admin_base(content, 'dashboard'))


# ── ADMIN: PENGATURAN PEMBAYARAN (QR CODE) ────────────────────────────────────
@admin_bp.route('/admin/payment-settings', methods=['GET','POST'])
def admin_payment_settings():
    if not admin_required():
        return redirect('/admin')

    db = get_db()
    if 'payment_settings' not in db:
        db['payment_settings'] = {'qris_image': ''}

    if request.method == 'POST':
        action = request.form.get('action', 'url')

        if action == 'url':
            # Simpan dari URL langsung
            qr_url = request.form.get('qr_url', '').strip()
            if qr_url:
                db['payment_settings']['qris_image'] = qr_url
                save_db(db)
                flash_msg('QR Code QRIS berhasil diperbarui dari URL!', 'success')
            else:
                flash_msg('URL gambar tidak boleh kosong!', 'danger')

        elif action == 'upload':
            # Upload file gambar
            file = request.files.get('qr_file')
            if file and file.filename:
                allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext not in allowed_ext:
                    flash_msg('Format file tidak didukung! Gunakan PNG/JPG/GIF/WEBP.', 'danger')
                else:
                    filename = f'qris_code.{ext}'
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    # Simpan sebagai base64 data URL agar portabel
                    with open(filepath, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode()
                    mime = f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
                    db['payment_settings']['qris_image'] = f'data:{mime};base64,{b64}'
                    save_db(db)
                    flash_msg('QR Code QRIS berhasil diupload!', 'success')
            else:
                flash_msg('Pilih file gambar terlebih dahulu!', 'danger')

        elif action == 'delete':
            db['payment_settings']['qris_image'] = ''
            save_db(db)
            flash_msg('QR Code QRIS berhasil dihapus.', 'success')

        return redirect('/admin/payment-settings')

    qris_img = db['payment_settings'].get('qris_image', '')
    preview_html = ''
    if qris_img:
        preview_html = f'''
        <div style="margin-top:1.5rem;padding:1.5rem;background:#11111e;border-radius:12px;text-align:center;">
          <p style="color:#8888aa;font-size:.8rem;margin-bottom:1rem;">Preview QR Code saat ini:</p>
          <img src="{qris_img}" style="max-width:200px;max-height:200px;object-fit:contain;border-radius:8px;background:white;padding:8px;" onerror="this.parentElement.innerHTML='<p style=color:#f87171>Gambar tidak bisa dimuat</p>'"/>
          <div style="margin-top:1rem;">
            <form method="POST" style="display:inline;">
              <input type="hidden" name="action" value="delete"/>
              <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Hapus QR Code ini?')">🗑️ Hapus QR Code</button>
            </form>
          </div>
        </div>'''

    content = f'''
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.75rem;">
      <a href="/admin" class="btn btn-ghost btn-sm">← Kembali</a>
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;">💳 Pengaturan Pembayaran</h1>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;">

      <!-- Upload File -->
      <div class="card">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:.5rem;">📁 Upload Gambar QR Code</h2>
        <p style="color:#8888aa;font-size:.85rem;margin-bottom:1.5rem;">Upload file gambar QR Code QRIS dari storage/perangkat kamu. File disimpan sebagai base64 di server.</p>
        <form method="POST" enctype="multipart/form-data">
          <input type="hidden" name="action" value="upload"/>
          <div class="form-group">
            <label>Pilih File Gambar</label>
            <input type="file" name="qr_file" accept="image/png,image/jpeg,image/jpg,image/gif,image/webp" id="fileInput" onchange="previewFile(this)" style="cursor:pointer;"/>
            <p style="color:#8888aa;font-size:.75rem;margin-top:.4rem;">Format: PNG, JPG, GIF, WEBP. Disarankan: ukuran 300×300px ke atas.</p>
          </div>
          <div id="filePreview" style="display:none;text-align:center;margin-bottom:1rem;">
            <img id="previewImg" src="" style="max-width:180px;max-height:180px;border-radius:8px;background:white;padding:8px;"/>
          </div>
          <button type="submit" class="btn btn-green" style="width:100%;justify-content:center;">⬆️ Upload QR Code</button>
        </form>
      </div>

      <!-- Dari URL -->
      <div class="card">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:.5rem;">🔗 Gunakan URL Gambar</h2>
        <p style="color:#8888aa;font-size:.85rem;margin-bottom:1.5rem;">Masukkan link langsung ke gambar QR Code QRIS yang sudah dihosting (Google Drive, Imgur, ImgBB, dsb).</p>
        <form method="POST">
          <input type="hidden" name="action" value="url"/>
          <div class="form-group">
            <label>URL Gambar QR Code</label>
            <input type="url" name="qr_url" placeholder="https://i.imgur.com/xxxxx.png" value="{qris_img if not qris_img.startswith('data:') else ''}" oninput="previewUrl(this.value)"/>
            <p style="color:#8888aa;font-size:.75rem;margin-top:.4rem;">Pastikan URL langsung ke file gambar (berakhiran .png/.jpg dll), bukan halaman web.</p>
          </div>
          <div id="urlPreview" style="display:none;text-align:center;margin-bottom:1rem;">
            <img id="urlPreviewImg" src="" style="max-width:180px;max-height:180px;border-radius:8px;background:white;padding:8px;" onerror="document.getElementById('urlPreview').style.display='none'"/>
          </div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;">💾 Simpan URL QR Code</button>
        </form>
      </div>
    </div>

    {preview_html}

    <div class="card" style="margin-top:1.5rem;background:rgba(59,130,246,.06);border-color:rgba(59,130,246,.2);">
      <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#93c5fd;margin-bottom:.75rem;">ℹ️ Cara Penggunaan</h3>
      <ul style="color:#8888aa;font-size:.875rem;line-height:1.9;list-style:none;padding:0;">
        <li>• QR Code yang diatur di sini akan tampil otomatis di halaman pembayaran tiket saat customer memilih metode <strong style="color:#ffd700;">QRIS</strong>.</li>
        <li>• Jika belum diatur, metode QRIS tetap tersedia tapi tanpa gambar QR.</li>
        <li>• Untuk <strong style="color:#fff;">ImgBB</strong>: upload foto → klik kanan → "Buka gambar di tab baru" → copy URL-nya.</li>
        <li>• Untuk <strong style="color:#fff;">Google Drive</strong>: share file → ganti link ke format <code style="color:#93c5fd;">https://drive.google.com/uc?export=view&id=FILE_ID</code>.</li>
      </ul>
    </div>

    <script>
    function previewFile(input) {{
      const preview = document.getElementById('filePreview');
      const img = document.getElementById('previewImg');
      if(input.files && input.files[0]) {{
        const reader = new FileReader();
        reader.onload = e => {{ img.src = e.target.result; preview.style.display = 'block'; }};
        reader.readAsDataURL(input.files[0]);
      }}
    }}
    function previewUrl(url) {{
      const preview = document.getElementById('urlPreview');
      const img = document.getElementById('urlPreviewImg');
      if(url) {{ img.src = url; preview.style.display = 'block'; }}
      else {{ preview.style.display = 'none'; }}
    }}
    </script>'''
    return make_response(admin_base(content, 'payment_settings'))


# ── ADMIN: KELOLA FILM ────────────────────────────────────────────────────────
@admin_bp.route('/admin/films')
def admin_films():
    if not admin_required(): return redirect('/admin')
    db = get_db()
    movies = db.get('movies', [])
    rows = ''
    for m in movies:
        poster = m.get('poster','')
        rows += f'''<tr>
          <td><img src="{poster}" style="width:45px;height:60px;object-fit:cover;border-radius:6px;" onerror="this.src='https://placehold.co/45x60/1a1a2e/e94560?text=?'"/></td>
          <td style="font-weight:600;">{m['title']}</td>
          <td style="color:#8888aa;">{m['genre']}</td>
          <td>{m['duration']}</td>
          <td><span style="background:rgba(255,215,0,.15);color:#ffd700;padding:.2rem .5rem;border-radius:6px;font-size:.8rem;">⭐ {m['score']}</span></td>
          <td style="color:#8888aa;">{m['rating']}</td>
          <td>
            <div style="display:flex;gap:.5rem;">
              <a href="/admin/films/edit/{m['id']}" class="btn btn-yellow btn-sm">✏️ Edit</a>
              <a href="/admin/films/delete/{m['id']}" class="btn btn-danger btn-sm" onclick="return confirm('Hapus film ini?')">🗑️ Hapus</a>
            </div>
          </td>
        </tr>'''

    content = f'''
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.75rem;">
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;">🎬 Kelola Film</h1>
      <a href="/admin/films/add" class="btn btn-green">+ Tambah Film</a>
    </div>
    <div class="card" style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th>Poster</th><th>Judul</th><th>Genre</th><th>Durasi</th><th>Skor</th><th>Rating</th><th>Aksi</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''
    return make_response(admin_base(content, 'films'))


@admin_bp.route('/admin/films/add', methods=['GET','POST'])
def admin_film_add():
    if not admin_required(): return redirect('/admin')
    if request.method == 'POST':
        db = get_db()
        showtimes = [t.strip() for t in request.form.get('showtimes','').split(',') if t.strip()]
        try: score = float(request.form.get('score',0))
        except: score = 0.0
        new_movie = {
            "id": next_movie_id(),
            "title": request.form.get('title','').strip(),
            "genre": request.form.get('genre','').strip(),
            "duration": request.form.get('duration','').strip(),
            "rating": request.form.get('rating','SU'),
            "score": score,
            "poster": request.form.get('poster','').strip(),
            "description": request.form.get('description','').strip(),
            "cast": request.form.get('cast','').strip(),
            "director": request.form.get('director','').strip(),
            "showtimes": showtimes if showtimes else ["10:00","13:00","16:00","19:00"],
        }
        if not new_movie['title']:
            flash_msg('Judul film wajib diisi!','danger')
            return redirect('/admin/films/add')
        db['movies'].append(new_movie)
        save_db(db)
        flash_msg(f'Film "{new_movie["title"]}" berhasil ditambahkan!','success')
        return redirect('/admin/films')
    content = _film_form('Tambah Film Baru', '/admin/films/add', {})
    return make_response(admin_base(content, 'films'))


@admin_bp.route('/admin/films/edit/<int:movie_id>', methods=['GET','POST'])
def admin_film_edit(movie_id):
    if not admin_required(): return redirect('/admin')
    db = get_db()
    m = next((x for x in db['movies'] if x['id']==movie_id), None)
    if not m: return redirect('/admin/films')

    if request.method == 'POST':
        showtimes = [t.strip() for t in request.form.get('showtimes','').split(',') if t.strip()]
        try: score = float(request.form.get('score',0))
        except: score = 0.0
        m['title'] = request.form.get('title','').strip()
        m['genre'] = request.form.get('genre','').strip()
        m['duration'] = request.form.get('duration','').strip()
        m['rating'] = request.form.get('rating','SU')
        m['score'] = score
        m['poster'] = request.form.get('poster','').strip()
        m['description'] = request.form.get('description','').strip()
        m['cast'] = request.form.get('cast','').strip()
        m['director'] = request.form.get('director','').strip()
        m['showtimes'] = showtimes if showtimes else m['showtimes']
        save_db(db)
        flash_msg(f'Film "{m["title"]}" berhasil diperbarui!','success')
        return redirect('/admin/films')

    content = _film_form(f'Edit Film: {m["title"]}', f'/admin/films/edit/{movie_id}', m)
    return make_response(admin_base(content, 'films'))


def _film_form(title, action, m):
    poster_val = m.get('poster','')
    preview = f'<img id="posterPreview" src="{poster_val}" style="width:120px;height:170px;object-fit:cover;border-radius:10px;border:1px solid rgba(255,255,255,.1);display:{"block" if poster_val else "none"};" onerror="this.style.display=\'none\'"/>' if poster_val else '<img id="posterPreview" src="" style="width:120px;height:170px;object-fit:cover;border-radius:10px;border:1px solid rgba(255,255,255,.1);display:none;"/>'
    no_preview_display = "none" if poster_val else "flex"

    return f'''
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.75rem;">
      <a href="/admin/films" class="btn btn-ghost btn-sm">← Kembali</a>
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;">{title}</h1>
    </div>
    <div style="display:grid;grid-template-columns:1fr 300px;gap:1.5rem;">
      <div class="card">
        <form method="POST" id="mainForm">
          <input type="hidden" name="poster" id="posterHidden" value="{poster_val}"/>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
            <div class="form-group" style="grid-column:1/-1"><label>Judul Film *</label><input type="text" name="title" value="{m.get('title','')}" placeholder="Nama film" required/></div>
            <div class="form-group"><label>Genre</label><input type="text" name="genre" value="{m.get('genre','')}" placeholder="Action/Sci-Fi"/></div>
            <div class="form-group"><label>Durasi</label><input type="text" name="duration" value="{m.get('duration','')}" placeholder="2j 30m"/></div>
            <div class="form-group"><label>Rating Usia</label>
              <select name="rating">
                {''.join(f'<option value="{r}" {"selected" if m.get("rating")==r else ""}>{r}</option>' for r in ["SU","13+","17+","21+"])}
              </select>
            </div>
            <div class="form-group"><label>Skor (0-10)</label><input type="number" name="score" value="{m.get('score','8.0')}" min="0" max="10" step="0.1" placeholder="8.5"/></div>
            <div class="form-group"><label>Sutradara</label><input type="text" name="director" value="{m.get('director','')}" placeholder="Nama sutradara"/></div>
            <div class="form-group"><label>Pemeran</label><input type="text" name="cast" value="{m.get('cast','')}" placeholder="Aktor 1, Aktor 2"/></div>
            <div class="form-group" style="grid-column:1/-1"><label>Jam Tayang (pisah dengan koma)</label><input type="text" name="showtimes" value="{', '.join(m.get('showtimes',[]))}" placeholder="10:00, 13:00, 16:00, 19:00"/></div>
            <div class="form-group" style="grid-column:1/-1"><label>Deskripsi</label><textarea name="description" placeholder="Sinopsis film...">{m.get('description','')}</textarea></div>
          </div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;margin-top:.5rem;">💾 Simpan Film</button>
        </form>
      </div>
      <div>
        <div class="card">
          <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;margin-bottom:1rem;">🖼️ Poster Film</h3>
          <div class="form-group">
            <label>URL Gambar Poster</label>
            <input type="text" id="posterUrl" value="{poster_val}" placeholder="https://..." oninput="prevPoster(this.value)"/>
            <p style="color:#8888aa;font-size:.75rem;margin-top:.5rem;">Masukkan link gambar dari internet (JPG/PNG).</p>
          </div>
          <div style="margin-top:1rem;display:flex;flex-direction:column;align-items:center;gap:.75rem;">
            {preview}
            <div id="noPreview" style="width:120px;height:170px;border:2px dashed rgba(255,255,255,.1);border-radius:10px;display:{no_preview_display};align-items:center;justify-content:center;color:#8888aa;font-size:.8rem;text-align:center;">Belum ada<br/>gambar</div>
            <button type="button" onclick="testPoster()" style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:8px;padding:.4rem .9rem;font-family:Outfit,sans-serif;font-size:.8rem;cursor:pointer;">🔍 Test Gambar</button>
          </div>
        </div>
      </div>
    </div>
    <script>
    function prevPoster(url) {{
      document.getElementById('posterHidden').value = url;
      const img = document.getElementById('posterPreview');
      const no = document.getElementById('noPreview');
      if(url){{img.src=url;img.style.display='block';no.style.display='none';}}
      else{{img.style.display='none';no.style.display='flex';}}
    }}
    function testPoster() {{
      const url = document.getElementById('posterUrl').value;
      if(!url){{alert('Masukkan URL gambar terlebih dahulu!');return;}}
      prevPoster(url);
      const img = document.getElementById('posterPreview');
      img.onerror = function(){{alert('❌ Gambar tidak bisa dimuat! Coba URL lain.');img.style.display='none';document.getElementById('noPreview').style.display='flex';}};
      img.onload = function(){{alert('✅ Gambar berhasil dimuat!');document.getElementById('noPreview').style.display='none';}};
    }}
    </script>'''


@admin_bp.route('/admin/films/delete/<int:movie_id>')
def admin_film_delete(movie_id):
    if not admin_required(): return redirect('/admin')
    db = get_db()
    movie = next((m for m in db['movies'] if m['id']==movie_id), None)
    if movie:
        db['movies'] = [m for m in db['movies'] if m['id'] != movie_id]
        save_db(db)
        flash_msg(f'Film "{movie["title"]}" berhasil dihapus!','success')
    return redirect('/admin/films')


# ── ADMIN: BOOKINGS ───────────────────────────────────────────────────────────
@admin_bp.route('/admin/bookings')
def admin_bookings():
    if not admin_required(): return redirect('/admin')
    db = get_db()
    rows = ''.join(f'''<tr>
      <td style="font-family:monospace;font-size:.8rem;color:#8888aa;">{b["id"]}</td>
      <td>{b["user"]}</td><td>{b["movie"]}</td>
      <td style="color:#8888aa;font-size:.85rem;">{b["cinema"]}</td>
      <td style="color:#8888aa;">{b["date"]} {b["time"]}</td>
      <td>{", ".join(b["seats"])}</td>
      <td style="color:#e8173a;font-weight:700;">{fmt_rp(b["total"])}</td>
      <td><span style="color:#34d399;font-size:.8rem;">✅ {b["status"]}</span></td>
    </tr>''' for b in reversed(db['bookings'])) or '<tr><td colspan="8" style="text-align:center;color:#8888aa;padding:1.5rem;">Belum ada booking</td></tr>'

    content = f'''
    <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:1.75rem;">🎟️ Semua Booking</h1>
    <div class="card" style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th>ID</th><th>User</th><th>Film</th><th>Bioskop</th><th>Waktu</th><th>Kursi</th><th>Total</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''
    return make_response(admin_base(content, 'bookings'))


# ── ADMIN: USERS ──────────────────────────────────────────────────────────────
@admin_bp.route('/admin/users')
def admin_users():
    if not admin_required(): return redirect('/admin')
    db = get_db()
    rows = ''.join(f'''<tr>
      <td style="font-weight:600;">{u["username"]}</td>
      <td style="color:#8888aa;">{u["email"]}</td>
      <td style="color:#8888aa;font-size:.85rem;">{u["joined"][:10]}</td>
      <td style="color:#e8173a;font-weight:700;">{sum(1 for b in db["bookings"] if b["user"]==u["username"])} booking</td>
    </tr>''' for u in db['users']) or '<tr><td colspan="4" style="text-align:center;color:#8888aa;padding:1.5rem;">Belum ada user</td></tr>'

    content = f'''
    <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:1.75rem;">👥 Daftar User</h1>
    <div class="card" style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th>Username</th><th>Email</th><th>Bergabung</th><th>Aktivitas</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''
    return make_response(admin_base(content, 'users'))


# ── ADMIN LOGOUT ──────────────────────────────────────────────────────────────
@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('role', None)
    return redirect('/admin')
