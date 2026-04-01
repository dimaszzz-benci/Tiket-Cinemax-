from flask import Flask, request, redirect, session, make_response
from datetime import datetime
import json, os, hashlib

app = Flask(__name__)
app.secret_key = 'bioskop_secret_2024'

# Fix path - compatible Vercel & Pydroid
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(BASE_DIR)
except:
    pass

# ── DEFAULT MOVIES ─────────────────────────────────────────────────────────────
DEFAULT_MOVIES = [
    {"id":1,"title":"Avengers: Secret Wars","genre":"Action/Sci-Fi","duration":"2j 45m","rating":"13+","score":9.1,
     "poster":"https://placehold.co/300x450/1a1a2e/e94560?text=Avengers",
     "description":"Para Avenger kembali bersatu menghadapi ancaman terbesar di seluruh multiverse.",
     "cast":"Robert Downey Jr., Chris Evans","director":"Russo Brothers","showtimes":["10:00","13:00","16:00","19:00","22:00"]},
    {"id":2,"title":"Dune: Messiah","genre":"Sci-Fi/Drama","duration":"2j 32m","rating":"13+","score":8.8,
     "poster":"https://placehold.co/300x450/0d0d0d/f5a623?text=Dune",
     "description":"Paul Atreides memimpin pemberontakan di planet Arrakis.",
     "cast":"Timothée Chalamet, Zendaya","director":"Denis Villeneuve","showtimes":["11:00","14:30","18:00","21:30"]},
    {"id":3,"title":"The Last Kingdom","genre":"Action/History","duration":"2j 10m","rating":"17+","score":8.5,
     "poster":"https://placehold.co/300x450/2d1b69/00d4ff?text=Kingdom",
     "description":"Kisah epik prajurit mempertahankan kerajaannya dari invasi asing.",
     "cast":"Alexander Dreymon, Emily Cox","director":"Edward Bazalgette","showtimes":["10:30","13:30","17:00","20:30"]},
    {"id":4,"title":"Haunted Mansion 2","genre":"Horror/Thriller","duration":"1j 58m","rating":"13+","score":7.9,
     "poster":"https://placehold.co/300x450/0a0a0a/39ff14?text=Haunted",
     "description":"Peneliti memasuki rumah berhantu yang menyimpan rahasia kelam.",
     "cast":"LaKeith Stanfield, Owen Wilson","director":"Justin Simien","showtimes":["12:00","15:00","18:30","21:00","23:30"]},
    {"id":5,"title":"Cinta di Ujung Senja","genre":"Romance/Drama","duration":"1j 52m","rating":"SU","score":8.2,
     "poster":"https://placehold.co/300x450/1a0a2e/ff6b9d?text=Cinta",
     "description":"Kisah cinta dua insan yang dipertemukan oleh takdir.",
     "cast":"Nicholas Saputra, Raisa","director":"Angga Dwimas Sasongko","showtimes":["10:00","12:30","15:30","18:00","20:30"]},
    {"id":6,"title":"Fast & Furious 11","genre":"Action/Racing","duration":"2j 20m","rating":"13+","score":8.0,
     "poster":"https://placehold.co/300x450/1c0000/ff4500?text=Fast11",
     "description":"Dom Toretto dan keluarga dalam satu misi terakhir.",
     "cast":"Vin Diesel, Michelle Rodriguez","director":"Louis Leterrier","showtimes":["09:30","12:00","14:30","17:00","19:30","22:00"]},
]
CINEMAS = ["CGV Grand Indonesia","XXI Plaza Senayan","Cinepolis Kota Kasablanka","IMAX Kelapa Gading"]
SEAT_PRICE = {"Reguler":45000,"Premium":75000,"IMAX":95000,"4DX":110000}

# ── DATABASE ───────────────────────────────────────────────────────────────────
_DB = {
    "users": [], "bookings": [],
    "movies": list(DEFAULT_MOVIES),
    "admin": {"username": "admin", "password": hashlib.md5(b"admin123").hexdigest()}
}

def get_db():
    return _DB

def save_db(data):
    global _DB
    _DB = data

def get_movies():
    return get_db()['movies']

def next_movie_id():
    movies = get_movies()
    return max((m['id'] for m in movies), default=0) + 1

# ── HELPERS ────────────────────────────────────────────────────────────────────
def flash_msg(msg, cat='info'):
    if '_flashes' not in session: session['_flashes'] = []
    session['_flashes'].append((cat, msg))
    session.modified = True

def get_flashes():
    msgs = session.pop('_flashes', [])
    session.modified = True
    return msgs

def fmt_rp(n):
    return 'Rp {:,}'.format(n).replace(',','.')

# ── BASE ───────────────────────────────────────────────────────────────────────
def base(content, title="CineMax"):
    user = session.get('user','')
    flashes = get_flashes()
    flash_html = ''
    colors = {'success':'#34d399','danger':'#f87171','warning':'#fbbf24','info':'#93c5fd'}
    bgs = {'success':'rgba(16,185,129,0.12)','danger':'rgba(232,23,58,0.12)','warning':'rgba(251,191,36,0.12)','info':'rgba(59,130,246,0.12)'}
    for cat, msg in flashes:
        c = colors.get(cat,'#fff'); bg = bgs.get(cat,'rgba(255,255,255,0.1)')
        flash_html += f'<div style="padding:.75rem 1.25rem;margin:.5rem 0;border-radius:10px;background:{bg};color:{c};font-size:.9rem;font-weight:500;">{msg}</div>'

    nav_right = f'''<div style="display:flex;align-items:center;gap:.75rem;">
        <span style="color:#aaa;font-size:.9rem;">👤 <strong style="color:#f0f0f8;">{user}</strong></span>
        <a href="/logout" style="background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff;padding:.35rem .9rem;border-radius:8px;text-decoration:none;font-size:.85rem;font-weight:600;">Keluar</a>
    </div>''' if user else '''<div style="display:flex;gap:.5rem;">
        <a href="/login" style="color:#aaa;padding:.35rem .8rem;border-radius:8px;text-decoration:none;font-size:.9rem;">Masuk</a>
        <a href="/register" style="background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff;padding:.35rem .9rem;border-radius:8px;text-decoration:none;font-size:.9rem;font-weight:600;">Daftar</a>
    </div>'''

    return f'''<!DOCTYPE html><html lang="id"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} - CineMax</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#090912;color:#f0f0f8;font-family:'Outfit',sans-serif;min-height:100vh}}
a{{color:inherit;text-decoration:none}}
.btn{{display:inline-flex;align-items:center;gap:.5rem;padding:.6rem 1.4rem;border-radius:10px;border:none;font-family:'Outfit',sans-serif;font-size:.9rem;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s}}
.btn-red{{background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff}}
.btn-red:hover{{opacity:.85;transform:translateY(-1px)}}
.btn-ghost{{background:transparent;color:#f0f0f8;border:1px solid rgba(255,255,255,.1)}}
.btn-ghost:hover{{background:rgba(255,255,255,.05)}}
.btn-green{{background:linear-gradient(135deg,#059669,#34d399);color:#fff}}
.btn-yellow{{background:linear-gradient(135deg,#d97706,#fbbf24);color:#000}}
.btn-danger{{background:linear-gradient(135deg,#dc2626,#f87171);color:#fff}}
.btn-sm{{padding:.4rem .9rem;font-size:.8rem}}
.card{{background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:1.5rem}}
input,select,textarea{{width:100%;background:#11111e;border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:10px;padding:.75rem 1rem;font-family:'Outfit',sans-serif;font-size:.95rem;outline:none;transition:border-color .2s}}
textarea{{resize:vertical;min-height:80px}}
input:focus,select:focus,textarea:focus{{border-color:#e8173a}}
label{{display:block;font-size:.8rem;color:#8888aa;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem}}
.form-group{{margin-bottom:1.25rem}}
.tab-btn{{padding:.5rem 1.25rem;border:1px solid rgba(255,255,255,.1);border-radius:8px;background:transparent;color:#8888aa;font-family:'Outfit',sans-serif;font-size:.85rem;font-weight:600;cursor:pointer;transition:all .2s}}
.tab-btn.active{{background:#e8173a;border-color:#e8173a;color:#fff}}
</style></head><body>
<nav style="position:sticky;top:0;z-index:1000;background:rgba(9,9,18,.93);backdrop-filter:blur(20px);border-bottom:1px solid rgba(255,255,255,.07);padding:0 1.5rem;height:64px;display:flex;align-items:center;justify-content:space-between;">
  <a href="/" style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px;">🎬 CineMax</a>
  <div style="display:flex;align-items:center;gap:.5rem;">
    <a href="/" style="color:#8888aa;padding:.4rem .8rem;border-radius:8px;font-size:.9rem;font-weight:500;">Film</a>
    <a href="/my-tickets" style="color:#8888aa;padding:.4rem .8rem;border-radius:8px;font-size:.9rem;font-weight:500;">Tiket</a>
    {nav_right}
  </div>
</nav>
<div style="max-width:1200px;margin:0 auto;padding:0 1.5rem;">{flash_html}</div>
{content}
<footer style="background:#11111e;border-top:1px solid rgba(255,255,255,.07);padding:2rem 1.5rem;margin-top:4rem;text-align:center;color:#8888aa;font-size:.85rem;">
  © 2024 CineMax — Platform tiket bioskop terbaik Indonesia 🎬
</footer>
</body></html>'''

# ── INDEX ──────────────────────────────────────────────────────────────────────
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

# ── MOVIE DETAIL ───────────────────────────────────────────────────────────────
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movies = get_movies()
    m = next((x for x in movies if x['id']==movie_id), None)
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

# ── BOOKING ────────────────────────────────────────────────────────────────────
@app.route('/booking/<int:movie_id>', methods=['GET','POST'])
def booking(movie_id):
    if 'user' not in session:
        flash_msg('Silakan login terlebih dahulu', 'warning')
        return redirect('/login')
    movies = get_movies()
    m = next((x for x in movies if x['id']==movie_id), None)
    if not m: return redirect('/')
    if request.method == 'POST':
        seats = request.form.getlist('seats')
        if not seats:
            flash_msg('Pilih minimal 1 kursi!', 'danger')
            return redirect(f'/booking/{movie_id}')
        seat_type = request.form.get('seat_type','Reguler')
        total = len(seats) * SEAT_PRICE[seat_type]
        bk = {"id":f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}","user":session['user'],"movie":m['title'],
              "cinema":request.form.get('cinema'),"date":request.form.get('date'),
              "time":request.form.get('showtime'),"seats":seats,"seat_type":seat_type,
              "total":total,"status":"confirmed","booked_at":datetime.now().isoformat()}
        db = get_db(); db['bookings'].append(bk); save_db(db)
        session['last_booking'] = bk
        return redirect(f'/payment/{bk["id"]}')

    cinema_opts = ''.join(f'<option value="{c}">{c}</option>' for c in CINEMAS)
    time_btns = ''.join(f'<button type="button" onclick="selTime(this,\'{t}\')" style="padding:.45rem 1rem;border:1px solid rgba(255,255,255,.1);border-radius:8px;background:transparent;color:#f0f0f8;font-family:Outfit,sans-serif;font-size:.85rem;font-weight:600;cursor:pointer;transition:all .2s;">{t}</button>' for t in m.get('showtimes',[]))
    type_btns = ''.join(f'<button type="button" onclick="selType(this,\'{n}\')" style="padding:.8rem;border:2px solid rgba(255,255,255,.1);border-radius:12px;background:transparent;cursor:pointer;text-align:left;transition:all .2s;color:#f0f0f8;font-family:Outfit,sans-serif;"><div style="font-weight:700;font-size:.9rem;">{n}</div><div style="color:#e8173a;font-size:.85rem;font-weight:600;">{fmt_rp(p)}</div></button>' for n,p in SEAT_PRICE.items())

    content = f'''
    <div style="max-width:1000px;margin:0 auto;padding:2rem 1.5rem;">
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:.5rem;">🎟️ Pesan Tiket — {m['title']}</h1>
      <p style="color:#8888aa;margin-bottom:2rem;">Lengkapi detail pemesananmu</p>
      <form method="POST" id="bookForm">
      <div style="display:grid;grid-template-columns:1fr 320px;gap:1.5rem;">
        <div>
          <div class="card" style="margin-bottom:1.25rem;">
            <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1.25rem;">📅 Pilih Jadwal</h3>
            <div class="form-group"><label>Bioskop</label><select name="cinema" onchange="document.getElementById('s-cinema').textContent=this.value">{cinema_opts}</select></div>
            <div class="form-group"><label>Tanggal</label><input type="date" name="date" id="dateInp" onchange="document.getElementById('s-date').textContent=this.value" required/></div>
            <div class="form-group">
              <label>Jam Tayang</label>
              <input type="hidden" name="showtime" id="timeInp" required/>
              <div style="display:flex;gap:.6rem;flex-wrap:wrap;">{time_btns}</div>
            </div>
          </div>
          <div class="card" style="margin-bottom:1.25rem;">
            <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1.25rem;">💺 Tipe Kursi</h3>
            <input type="hidden" name="seat_type" id="typeInp" value="Reguler"/>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;">{type_btns}</div>
          </div>
          <div class="card">
            <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1rem;">🪑 Pilih Kursi</h3>
            <div style="background:linear-gr
