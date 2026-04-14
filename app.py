from flask import Flask, request, redirect, session, make_response
import hashlib, os
from database import get_db, save_db, get_movies, fmt_rp, CINEMAS, SEAT_PRICE
from helpers import flash_msg, get_flashes, base
from admin import admin_bp
from payment import payment_bp
from booking import booking_bp

app = Flask(__name__)
app.secret_key = 'bioskop_secret_2024'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(BASE_DIR)
except:
    pass

app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(booking_bp)

@app.route('/')
def index():
    movies = get_movies()
    cards = ''
    for m in movies:
        poster = m.get('poster','https://placehold.co/300x450/1a1a2e/e94560?text=Film')
        cards += f'''<a href="/movie/{m['id']}" style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden;text-decoration:none;color:#f0f0f8;transition:all .3s;display:block;" onmouseover="this.style.transform='translateY(-6px)';this.style.borderColor='rgba(232,23,58,.4)'" onmouseout="this.style.transform='';this.style.borderColor='rgba(255,255,255,.07)'">
          <div style="position:relative;aspect-ratio:2/3;overflow:hidden;">
            <img src="{poster}" style="width:100%;height:100%;object-fit:cover;" loading="lazy" onerror="this.src='https://placehold.co/300x450/1a1a2e/e94560?text=No+Image'"/>
            <div style="position:absolute;top:.75rem;right:.75rem;background:rgba(0,0,0,.75);border:1px solid rgba(255,215,0,.4);border-radius:8px;padding:.25rem .5rem;font-size:.8rem;font-weight:700;color:#ffd700;">⭐ {m['score']}</div>
          </div>
          <div style="padding:1rem;">
            <div style="font-weight:700;font-size:.95rem;margin-bottom:.4rem;">{m['title']}</div>
            <div style="color:#8888aa;font-size:.8rem;">{m['genre']} • {m['duration']}</div>
          </div>
          <div style="padding:0 1rem 1rem;">
            <span style="background:rgba(232,23,58,.2);color:#f87171;padding:.2rem .6rem;border-radius:6px;font-size:.75rem;font-weight:600;">{m['rating']}</span>
          </div>
        </a>'''
    content = f'''
    <div style="background:linear-gradient(180deg,#1a0520,#090912);padding:4rem 1.5rem 3rem;text-align:center;position:relative;overflow:hidden;">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(232,23,58,.15),transparent);pointer-events:none;"></div>
      <div style="display:inline-flex;align-items:center;gap:.5rem;background:rgba(232,23,58,.1);border:1px solid rgba(232,23,58,.3);color:#f87171;font-size:.8rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;padding:.35rem 1rem;border-radius:999px;margin-bottom:1.5rem;">🔥 {len(movies)} Film Tersedia</div>
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:clamp(3rem,8vw,5.5rem);line-height:.95;letter-spacing:3px;margin-bottom:1.25rem;">Pesan Tiket<br><span style="background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Bioskop Online</span></h1>
      <p style="color:#8888aa;font-size:1.05rem;max-width:480px;margin:0 auto 2rem;">Pilih film favoritmu, pilih kursi terbaik, nikmati pengalaman sinema luar biasa.</p>
      <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
        <a href="#films" class="btn btn-red">🎬 Lihat Film</a>
        <a href="/register" class="btn btn-ghost">Daftar Gratis →</a>
      </div>
    </div>
    <div style="max-width:1200px;margin:0 auto;padding:2.5rem 1.5rem;" id="films">
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;letter-spacing:2px;margin-bottom:1.75rem;">Film <span style="background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Sedang Tayang</span></h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1.25rem;">{cards}</div>
    </div>'''
    return make_response(base(content, "Beranda"))

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movies = get_movies()
    m = next((x for x in movies if x['id'] == movie_id), None)
    if not m: return redirect('/')
    poster = m.get('poster','https://placehold.co/300x450/1a1a2e/e94560?text=Film')
    times = ''.join(f'<span style="padding:.45rem 1rem;border:1px solid rgba(255,255,255,.1);border-radius:8px;font-size:.9rem;font-weight:600;color:#8888aa;">🕐 {t}</span>' for t in m.get('showtimes',[]))
    content = f'''
    <div style="background:linear-gradient(180deg,#1a0a20,#090912);padding:3rem 1.5rem 0;">
      <div style="max-width:1100px;margin:0 auto;display:grid;grid-template-columns:260px 1fr;gap:2.5rem;align-items:start;">
        <img src="{poster}" style="width:100%;border-radius:16px;box-shadow:0 30px 60px rgba(0,0,0,.6);" onerror="this.src='https://placehold.co/300x450/1a1a2e/e94560?text=No+Image'"/>
        <div style="padding:1rem 0;">
          <div style="color:#8888aa;font-size:.85rem;margin-bottom:.75rem;">{m['genre']}</div>
          <h1 style="font-family:'Bebas Neue',sans-serif;font-size:3rem;letter-spacing:2px;margin-bottom:1.25rem;line-height:1;">{m['title']}</h1>
          <div style="display:flex;gap:1.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
            <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;color:#ffd700;">⭐ {m['score']}</div><div style="color:#8888aa;font-size:.75rem;text-transform:uppercase;">Skor</div></div>
            <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;">{m['duration']}</div><div style="color:#8888aa;font-size:.75rem;text-transform:uppercase;">Durasi</div></div>
            <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;">{m['rating']}</div><div style="color:#8888aa;font-size:.75rem;text-transform:uppercase;">Rating</div></div>
          </div>
          <p style="color:#c0c0d8;line-height:1.7;margin-bottom:1.5rem;">{m['description']}</p>
          <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1.25rem;margin-bottom:1rem;">
            <div style="font-size:.75rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.5rem;">🎬 Sutradara</div>
            <div style="font-weight:600;">{m['director']}</div>
          </div>
          <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1.25rem;margin-bottom:1.5rem;">
            <div style="font-size:.75rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.5rem;">⭐ Pemeran</div>
            <div style="font-weight:600;">{m['cast']}</div>
          </div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;">
            <a href="/booking/{m['id']}" class="btn btn-red" style="font-size:1rem;padding:.8rem 2rem;">🎟️ Beli Tiket</a>
            <a href="/" class="btn btn-ghost">← Kembali</a>
          </div>
        </div>
      </div>
    </div>
    <div style="max-width:1100px;margin:2rem auto;padding:0 1.5rem;">
      <div class="card">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.5rem;margin-bottom:1.25rem;">🗓️ Jadwal Tayang</h2>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;">{times}</div>
        <p style="color:#8888aa;margin-top:1rem;font-size:.85rem;">Tersedia di: {', '.join(CINEMAS)}</p>
        <div style="margin-top:1.5rem;"><a href="/booking/{m['id']}" class="btn btn-red">🎟️ Pesan Sekarang</a></div>
      </div>
    </div>'''
    return make_response(base(content, m['title']))

@app.route('/my-tickets')
def my_tickets():
    if 'user' not in session: return redirect('/login')
    db = get_db()
    bks = [b for b in db['bookings'] if b['user'] == session['user']]
    if bks:
        items = ''
        for b in reversed(bks):
            items += f'''<div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden;display:grid;grid-template-columns:6px 1fr auto;margin-bottom:1.25rem;">
              <div style="background:linear-gradient(135deg,#e8173a,#ff6b35);"></div>
              <div style="padding:1.5rem;">
                <div style="font-family:'Bebas Neue',sans-serif;font-size:1.5rem;letter-spacing:1px;margin-bottom:.75rem;">{b['movie']}</div>
                <div style="display:flex;gap:1.5rem;flex-wrap:wrap;font-size:.85rem;color:#8888aa;">
                  <span>🏛 <strong style="color:#f0f0f8;">{b['cinema']}</strong></span>
                  <span>📅 <strong style="color:#f0f0f8;">{b['date']}</strong></span>
                  <span>🕐 <strong style="color:#f0f0f8;">{b['time']}</strong></span>
                  <span>💺 <strong style="color:#f0f0f8;">{b['seat_type']}</strong></span>
                  <span>🪑 <strong style="color:#f0f0f8;">{', '.join(b['seats'])}</strong></span>
                </div>
                <div style="margin-top:.75rem;font-size:.75rem;color:#8888aa;font-family:monospace;">{b['id']}</div>
              </div>
              <div style="padding:1.5rem;display:flex;flex-direction:column;align-items:flex-end;justify-content:space-between;border-left:1px dashed rgba(255,255,255,.07);min-width:130px;">
                <span style="background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);padding:.3rem .75rem;border-radius:999px;font-size:.75rem;font-weight:700;">✅ {b['status']}</span>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#e8173a;">{fmt_rp(b['total'])}</div>
              </div>
            </div>'''
        body = items
    else:
        body = '''<div style="text-align:center;padding:4rem 2rem;">
          <div style="font-size:4rem;margin-bottom:1rem;">🎬</div>
          <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;margin-bottom:.5rem;">Belum Ada Tiket</h2>
          <p style="color:#8888aa;margin-bottom:1.5rem;">Kamu belum memesan tiket apapun.</p>
          <a href="/" class="btn btn-red">Lihat Film →</a>
        </div>'''
    content = f'''<div style="max-width:900px;margin:0 auto;padding:2.5rem 1.5rem;">
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;margin-bottom:.5rem;">🎟️ Tiket Saya</h1>
      <p style="color:#8888aa;margin-bottom:2rem;">Riwayat pemesanan tiket bioskopmu.</p>
      {body}</div>'''
    return make_response(base(content, 'Tiket Saya'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        user = next((u for u in db['users'] if u['username']==username and u['password']==password), None)
        if user:
            session['user'] = username
            flash_msg(f'Selamat datang, {username}!', 'success')
            return redirect('/')
        flash_msg('Username atau password salah!', 'danger')
    content = '''<div style="min-height:calc(100vh - 64px);display:flex;align-items:center;justify-content:center;padding:2rem;background:radial-gradient(ellipse 60% 50% at 50% 0%,rgba(232,23,58,.08),transparent);">
      <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:24px;padding:2.5rem;width:100%;max-width:400px;">
        <div style="text-align:center;margin-bottom:2rem;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎬 CineMax</div>
          <p style="color:#8888aa;font-size:.9rem;margin-top:.25rem;">Selamat datang kembali!</p>
        </div>
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;margin-bottom:1.75rem;">Masuk Akun</h2>
        <form method="POST">
          <div class="form-group"><label>Username</label><input type="text" name="username" placeholder="Masukkan username" required/></div>
          <div class="form-group"><label>Password</label><input type="password" name="password" placeholder="Masukkan password" required/></div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;margin-top:.5rem;">Masuk →</button>
        </form>
        <p style="text-align:center;margin-top:1.5rem;color:#8888aa;font-size:.9rem;">Belum punya akun? <a href="/register" style="color:#e8173a;font-weight:600;">Daftar sekarang</a></p>
      </div>
    </div>'''
    return make_response(base(content, 'Masuk'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        if any(u['username']==username for u in db['users']):
            flash_msg('Username sudah digunakan!', 'danger')
        else:
            import datetime as dt
            db['users'].append({"username":username,"email":request.form['email'],"password":hashlib.md5(request.form['password'].encode()).hexdigest(),"joined":dt.datetime.now().isoformat()})
            save_db(db)
            flash_msg('Registrasi berhasil! Silakan login.', 'success')
            return redirect('/login')
    content = '''<div style="min-height:calc(100vh - 64px);display:flex;align-items:center;justify-content:center;padding:2rem;background:radial-gradient(ellipse 60% 50% at 50% 0%,rgba(232,23,58,.08),transparent);">
      <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:24px;padding:2.5rem;width:100%;max-width:400px;">
        <div style="text-align:center;margin-bottom:2rem;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎬 CineMax</div>
          <p style="color:#8888aa;font-size:.9rem;margin-top:.25rem;">Bergabung dengan jutaan penonton</p>
        </div>
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;margin-bottom:1.75rem;">Buat Akun Baru</h2>
        <form method="POST">
          <div class="form-group"><label>Username</label><input type="text" name="username" placeholder="Pilih username" required/></div>
          <div class="form-group"><label>Email</label><input type="email" name="email" placeholder="email@kamu.com" required/></div>
          <div class="form-group"><label>Password</label><input type="password" name="password" placeholder="Min. 6 karakter" minlength="6" required/></div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;margin-top:.5rem;">Daftar Sekarang →</button>
        </form>
        <p style="text-align:center;margin-top:1.5rem;color:#8888aa;font-size:.9rem;">Sudah punya akun? <a href="/login" style="color:#e8173a;font-weight:600;">Masuk di sini</a></p>
      </div>
    </div>'''
    return make_response(base(content, 'Daftar'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
