from flask import Flask, request, redirect, session, make_response
from datetime import datetime
import json, os, hashlib

app = Flask(__name__)
app.secret_key = 'bioskop_secret_2024'
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
def get_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.json')
    if not os.path.exists(db_path):
        data = {
            "users": [], "bookings": [],
            "movies": DEFAULT_MOVIES,
            "admin": {"username": "admin", "password": hashlib.md5(b"admin123").hexdigest()}
        }
        with open(db_path, 'w') as f: json.dump(data, f, indent=2)
    with open(db_path) as f:
        db = json.load(f)
    if 'movies' not in db:
        db['movies'] = DEFAULT_MOVIES
        save_db(db)
    return db

def save_db(data):
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.json')
    with open(db_path, 'w') as f: json.dump(data, f, indent=2)

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
            <div style="background:linear-gradient(90deg,transparent,rgba(232,23,58,.3),transparent);height:3px;border-radius:3px;margin:0 2rem .5rem;"></div>
            <p style="text-align:center;color:#8888aa;font-size:.75rem;letter-spacing:3px;margin-bottom:1.5rem;">▲ LAYAR ▲</p>
            <div id="seatGrid" style="display:grid;grid-template-columns:repeat(10,1fr);gap:.35rem;margin-bottom:1rem;"></div>
            <div style="display:flex;gap:1.5rem;justify-content:center;margin-bottom:1rem;">
              <div style="display:flex;align-items:center;gap:.4rem;font-size:.8rem;color:#8888aa;"><div style="width:14px;height:14px;border-radius:3px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);"></div>Tersedia</div>
              <div style="display:flex;align-items:center;gap:.4rem;font-size:.8rem;color:#8888aa;"><div style="width:14px;height:14px;border-radius:3px;background:#e8173a;"></div>Dipilih</div>
              <div style="display:flex;align-items:center;gap:.4rem;font-size:.8rem;color:#8888aa;"><div style="width:14px;height:14px;border-radius:3px;background:rgba(255,255,255,.03);"></div>Terisi</div>
            </div>
            <p style="text-align:center;color:#8888aa;font-size:.85rem;">Dipilih: <span id="selDisplay" style="color:#e8173a;font-weight:700;">—</span></p>
          </div>
        </div>
        <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:20px;padding:1.75rem;position:sticky;top:80px;height:fit-content;">
          <h3 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1.25rem;">🧾 Ringkasan</h3>
          <div style="font-weight:700;font-size:1rem;margin-bottom:.25rem;">{m['title']}</div>
          <div style="color:#8888aa;font-size:.85rem;margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid rgba(255,255,255,.07);">{m['genre']} • ⭐ {m['score']}</div>
          <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;font-size:.9rem;"><span style="color:#8888aa;">Bioskop</span><span id="s-cinema" style="font-weight:600;">{CINEMAS[0]}</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;font-size:.9rem;"><span style="color:#8888aa;">Tanggal</span><span id="s-date" style="font-weight:600;">—</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;font-size:.9rem;"><span style="color:#8888aa;">Jam</span><span id="s-time" style="font-weight:600;">—</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;font-size:.9rem;"><span style="color:#8888aa;">Tipe</span><span id="s-type" style="font-weight:600;">Reguler</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;font-size:.9rem;"><span style="color:#8888aa;">Kursi</span><span id="s-seats" style="font-weight:600;">—</span></div>
          <div style="border-top:1px solid rgba(255,255,255,.07);padding-top:1rem;margin-top:.5rem;">
            <div style="color:#8888aa;font-size:.85rem;">Total</div>
            <div id="s-total" style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#e8173a;">Rp 0</div>
          </div>
          <button type="submit" class="btn btn-red" style="width:100%;justify-content:center;margin-top:1.25rem;">Lanjut ke Pembayaran →</button>
        </div>
      </div>
      </form>
    </div>
    <script>
    const PRICES={{"Reguler":45000,"Premium":75000,"IMAX":95000,"4DX":110000}};
    let selSeats=[],curPrice=45000;
    const TAKEN=["A3","A7","B5","C2","C8","D4","D6","E1","E9","F3","F7","G5","H2","H8"];
    const ROWS=["A","B","C","D","E","F","G","H"];
    const di=document.getElementById('dateInp');
    di.min=new Date().toISOString().split('T')[0]; di.value=di.min;
    document.getElementById('s-date').textContent=di.value;
    const grid=document.getElementById('seatGrid');
    ROWS.forEach(r=>{{for(let c=1;c<=10;c++){{
      const id=r+c,taken=TAKEN.includes(id);
      const d=document.createElement('div');
      d.style.cssText=`aspect-ratio:1;border-radius:5px;border:1px solid ${{taken?'transparent':'rgba(255,255,255,.12)'}};cursor:${{taken?'not-allowed':'pointer'}};display:flex;align-items:center;justify-content:center;font-size:.55rem;font-weight:700;transition:all .15s;background:rgba(255,255,255,.03);color:${{taken?'rgba(255,255,255,.1)':'#8888aa'}};`;
      d.textContent=id;
      if(!taken)d.onclick=()=>toggleSeat(d,id);
      grid.appendChild(d);
    }}}});
    function toggleSeat(d,id){{
      if(d.dataset.sel==='1'){{d.dataset.sel='';d.style.background='rgba(255,255,255,.03)';d.style.borderColor='rgba(255,255,255,.12)';d.style.color='#8888aa';selSeats=selSeats.filter(s=>s!==id);}}
      else{{if(selSeats.length>=8){{alert('Maksimal 8 kursi');return;}}d.dataset.sel='1';d.style.background='#e8173a';d.style.borderColor='#e8173a';d.style.color='#fff';selSeats.push(id);}}
      document.querySelectorAll('.si').forEach(e=>e.remove());
      selSeats.forEach(s=>{{const i=document.createElement('input');i.type='hidden';i.name='seats';i.value=s;i.className='si';document.getElementById('bookForm').appendChild(i);}});
      document.getElementById('selDisplay').textContent=selSeats.length?selSeats.join(', '):'—';
      document.getElementById('s-seats').textContent=selSeats.length?selSeats.join(', '):'—';
      document.getElementById('s-total').textContent='Rp '+new Intl.NumberFormat('id-ID').format(selSeats.length*curPrice);
    }}
    function selTime(btn,t){{
      document.querySelectorAll('[onclick^="selTime"]').forEach(b=>{{b.style.background='transparent';b.style.borderColor='rgba(255,255,255,.1)';}});
      btn.style.background='#e8173a';btn.style.borderColor='#e8173a';
      document.getElementById('timeInp').value=t;
      document.getElementById('s-time').textContent=t;
    }}
    function selType(btn,name){{
      document.querySelectorAll('[onclick^="selType"]').forEach(b=>b.style.borderColor='rgba(255,255,255,.1)');
      btn.style.borderColor='#e8173a';
      document.getElementById('typeInp').value=name;curPrice=PRICES[name];
      document.getElementById('s-type').textContent=name;
      document.getElementById('s-total').textContent='Rp '+new Intl.NumberFormat('id-ID').format(selSeats.length*curPrice);
    }}
    </script>'''
    return make_response(base(content, f'Pesan - {m["title"]}'))

# ── PAYMENT ────────────────────────────────────────────────────────────────────
@app.route('/payment/<booking_id>')
def payment(booking_id):
    bk = session.get('last_booking')
    if not bk or bk['id'] != booking_id: return redirect('/')
    seat_tags = ''.join(f'<span style="background:rgba(232,23,58,.15);border:1px solid rgba(232,23,58,.3);color:#e8173a;padding:.3rem .65rem;border-radius:6px;font-size:.85rem;font-weight:700;">{s}</span>' for s in bk['seats'])
    content = f'''
    <div style="max-width:720px;margin:0 auto;padding:2.5rem 1.5rem;">
      <div style="text-align:center;padding:1rem;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:12px;color:#34d399;font-size:.95rem;margin-bottom:2rem;">
        🎉 Pemesanan dikonfirmasi! Selamat menikmati <strong>{bk['movie']}</strong>
      </div>
      <div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:20px;overflow:hidden;margin-bottom:2rem;">
        <div style="background:linear-gradient(135deg,#1a0520,#2d0a14);padding:2rem;display:flex;gap:1.5rem;align-items:center;">
          <span style="font-size:3rem;">🎬</span>
          <div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;">{bk['movie']}</div>
            <div style="color:#8888aa;font-size:.85rem;font-family:monospace;">ID: {bk['id']}</div>
          </div>
        </div>
        <div style="padding:1.5rem 2rem;">
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.25rem;">
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Bioskop</div><div style="font-weight:700;font-size:.9rem;">{bk['cinema']}</div></div>
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Tanggal</div><div style="font-weight:700;font-size:.9rem;">{bk['date']}</div></div>
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Jam</div><div style="font-weight:700;font-size:.9rem;">{bk['time']}</div></div>
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Tipe</div><div style="font-weight:700;font-size:.9rem;">{bk['seat_type']}</div></div>
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Jml Kursi</div><div style="font-weight:700;font-size:.9rem;">{len(bk['seats'])} kursi</div></div>
            <div><div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.3rem;">Status</div><div style="font-weight:700;font-size:.9rem;color:#34d399;">✅ Confirmed</div></div>
          </div>
        </div>
        <div style="padding:1.25rem 2rem;border-top:1px solid rgba(255,255,255,.07);">
          <div style="font-size:.7rem;color:#8888aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.75rem;">Nomor Kursi</div>
          <div style="display:flex;gap:.5rem;flex-wrap:wrap;">{seat_tags}</div>
        </div>
        <div style="padding:1.5rem 2rem;border-top:1px solid rgba(255,255,255,.07);text-align:center;">
          <div style="font-size:2rem;letter-spacing:.3rem;margin-bottom:.5rem;">▌▌█▌▌▌█▌▌█▌▌▌▌█▌▌█▌</div>
          <div style="font-family:monospace;color:#8888aa;font-size:.8rem;">{bk['id']}</div>
        </div>
      </div>
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;margin-bottom:1.25rem;">💳 Metode Pembayaran</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1.5rem;">
        {''.join(f'<div onclick="selPay(this)" style="padding:1rem;border:2px solid rgba(255,255,255,.1);border-radius:12px;cursor:pointer;text-align:center;transition:all .2s;"><div style=\'font-size:1.6rem;margin-bottom:.25rem;\'>{ic}</div><div style=\'font-size:.8rem;font-weight:600;\'>{nm}</div></div>' for ic,nm in [("💳","Transfer Bank"),("📱","GoPay/OVO"),("🏪","Minimarket"),("💰","QRIS"),("🏦","Virtual Acc"),("💎","Kartu Kredit")])}
      </div>
      <div style="background:linear-gradient(135deg,rgba(232,23,58,.1),rgba(255,107,53,.1));border:1px solid rgba(232,23,58,.3);border-radius:16px;padding:1.5rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;">
        <div><div style="color:#8888aa;font-size:.9rem;">Total Pembayaran</div><div style="color:#8888aa;font-size:.8rem;">{len(bk['seats'])} kursi × {bk['seat_type']}</div></div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;color:#e8173a;">{fmt_rp(bk['total'])}</div>
      </div>
      <button class="btn btn-red" style="width:100%;justify-content:center;font-size:1.05rem;padding:.9rem;" onclick="alert('✅ Simulasi pembayaran berhasil!')">
        💳 Bayar {fmt_rp(bk['total'])}
      </button>
      <div style="text-align:center;margin-top:1rem;"><a href="/my-tickets" style="color:#8888aa;font-size:.9rem;">Lihat semua tiket saya →</a></div>
    </div>
    <script>function selPay(el){{document.querySelectorAll('[onclick="selPay(this)"]').forEach(e=>e.style.borderColor='rgba(255,255,255,.1)');el.style.borderColor='#e8173a';}}</script>'''
    return make_response(base(content, 'Pembayaran'))

# ── MY TICKETS ─────────────────────────────────────────────────────────────────
@app.route('/my-tickets')
def my_tickets():
    if 'user' not in session: return redirect('/login')
    db = get_db()
    bks = [b for b in db['bookings'] if b['user']==session['user']]
    if bks:
        items = ''
        for b in reversed(bks):
            items += f'''<div style="background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden;display:grid;grid-template-columns:6px 1fr auto;margin-bottom:1.25rem;" onmouseover="this.style.borderColor='rgba(232,23,58,.4)'" onmouseout="this.style.borderColor='rgba(255,255,255,.07)'">
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

# ── LOGIN ──────────────────────────────────────────────────────────────────────
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

# ── REGISTER ───────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        if any(u['username']==username for u in db['users']):
            flash_msg('Username sudah digunakan!', 'danger')
        else:
            db['users'].append({"username":username,"email":request.form['email'],"password":hashlib.md5(request.form['password'].encode()).hexdigest(),"joined":datetime.now().isoformat()})
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

# ── LOGOUT ─────────────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
def admin_required():
    return session.get('role') == 'admin'

def admin_base(content, active='dashboard'):
    db = get_db()
    flashes = get_flashes()
    flash_html = ''
    colors = {'success':'#34d399','danger':'#f87171','warning':'#fbbf24'}
    bgs = {'success':'rgba(16,185,129,0.12)','danger':'rgba(232,23,58,0.12)','warning':'rgba(251,191,36,0.12)'}
    for cat, msg in flashes:
        c = colors.get(cat,'#fff'); bg = bgs.get(cat,'rgba(255,255,255,0.1)')
        flash_html += f'<div style="padding:.75rem 1.25rem;margin:.5rem 0 0;border-radius:10px;background:{bg};color:{c};font-size:.9rem;font-weight:500;">{msg}</div>'

    nav_items = [
        ('dashboard','📊 Dashboard','/admin'),
        ('films','🎬 Kelola Film','/admin/films'),
        ('bookings','🎟️ Booking','/admin/bookings'),
        ('users','👥 Users','/admin/users'),
    ]
    nav_html = ''
    for key, label, href in nav_items:
        is_active = key == active
        style = "display:flex;align-items:center;gap:.6rem;padding:.6rem 1rem;border-radius:10px;text-decoration:none;font-size:.9rem;font-weight:600;transition:all .2s;"
        if is_active:
            style += "background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff;"
        else:
            style += "color:#8888aa;"
        nav_html += f'<a href="{href}" style="{style}">{label}</a>'

    return f'''<!DOCTYPE html><html lang="id"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Admin - CineMax</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#090912;color:#f0f0f8;font-family:'Outfit',sans-serif;min-height:100vh;display:grid;grid-template-columns:220px 1fr;}}
a{{color:inherit;text-decoration:none}}
.btn{{display:inline-flex;align-items:center;gap:.5rem;padding:.6rem 1.4rem;border-radius:10px;border:none;font-family:'Outfit',sans-serif;font-size:.9rem;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s}}
.btn-red{{background:linear-gradient(135deg,#e8173a,#ff6b35);color:#fff}}
.btn-red:hover{{opacity:.85}}
.btn-green{{background:linear-gradient(135deg,#059669,#34d399);color:#fff}}
.btn-green:hover{{opacity:.85}}
.btn-yellow{{background:linear-gradient(135deg,#d97706,#fbbf24);color:#000}}
.btn-yellow:hover{{opacity:.85}}
.btn-danger{{background:linear-gradient(135deg,#dc2626,#f87171);color:#fff}}
.btn-danger:hover{{opacity:.85}}
.btn-ghost{{background:transparent;color:#f0f0f8;border:1px solid rgba(255,255,255,.1)}}
.btn-sm{{padding:.35rem .85rem;font-size:.8rem}}
.card{{background:#181828;border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:1.5rem}}
input,select,textarea{{width:100%;background:#11111e;border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:10px;padding:.75rem 1rem;font-family:'Outfit',sans-serif;font-size:.95rem;outline:none;transition:border-color .2s}}
textarea{{resize:vertical;min-height:80px}}
input:focus,select:focus,textarea:focus{{border-color:#e8173a}}
label{{display:block;font-size:.8rem;color:#8888aa;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem}}
.form-group{{margin-bottom:1.25rem}}
th{{text-align:left;padding:.6rem .75rem;color:#8888aa;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid rgba(255,255,255,.07);}}
td{{padding:.7rem .75rem;border-bottom:1px solid rgba(255,255,255,.04);font-size:.9rem;}}
tr:hover td{{background:rgba(255,255,255,.02)}}
@media(max-width:700px){{body{{grid-template-columns:1fr}}aside{{display:none}}}}
</style></head><body>
<aside style="background:#11111e;border-right:1px solid rgba(255,255,255,.07);padding:1.5rem;display:flex;flex-direction:column;gap:.5rem;position:sticky;top:0;height:100vh;overflow-y:auto;">
  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:1rem;letter-spacing:2px;">🎬 CineMax<br><span style="font-size:1rem;color:#8888aa;-webkit-text-fill-color:#8888aa;">Admin Panel</span></div>
  {nav_html}
  <div style="margin-top:auto;padding-top:1rem;border-top:1px solid rgba(255,255,255,.07);">
    <a href="/" style="color:#8888aa;font-size:.85rem;display:block;padding:.5rem 0;">← Ke Website</a>
    <a href="/admin/logout" style="color:#f87171;font-size:.85rem;display:block;padding:.5rem 0;">🚪 Keluar Admin</a>
  </div>
</aside>
<main style="overflow-y:auto;min-height:100vh;">
  <div style="padding:1.5rem 2rem;">{flash_html}{content}</div>
</main>
</body></html>'''

# ── ADMIN LOGIN ────────────────────────────────────────────────────────────────
@app.route('/admin', methods=['GET','POST'])
def admin():
    if not admin_required():
        if request.method == 'POST':
            db = get_db()
            if request.form['username']==db['admin']['username'] and \
               hashlib.md5(request.form['password'].encode()).hexdigest()==db['admin']['password']:
                session['role']='admin'
                flash_msg('Login admin berhasil! Selamat datang.','success')
                return redirect('/admin')
            flash_msg('Username atau password admin salah!','danger')
        flashes = get_flashes()
        flash_html = ''
        for cat,msg in flashes:
            colors={'success':'#34d399','danger':'#f87171'}; bgs={'success':'rgba(16,185,129,0.12)','danger':'rgba(232,23,58,0.12)'}
            flash_html+=f'<div style="padding:.75rem 1.25rem;margin:.5rem 0;border-radius:10px;background:{bgs.get(cat,"")};color:{colors.get(cat,"#fff")};font-size:.9rem;font-weight:500;">{msg}</div>'
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
    recent_rows = ''.join(f'<tr><td style="font-family:monospace;font-size:.8rem;color:#8888aa;">{b["id"][:15]}...</td><td>{b["user"]}</td><td>{b["movie"][:20]}</td><td style="color:#e8173a;font-weight:700;">{fmt_rp(b["total"])}</td></tr>' for b in recent) or '<tr><td colspan="4" style="text-align:center;color:#8888aa;padding:1rem;">Belum ada booking</td></tr>'

    content = f'''
    <h1 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;margin-bottom:1.75rem;">📊 Dashboard</h1>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem;">
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total Booking</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(db['bookings'])}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total User</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(db['users'])}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Film Tayang</div><div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{len(movies)}</div></div>
      <div class="card"><div style="font-size:.85rem;color:#8888aa;margin-bottom:.5rem;">Total Revenue</div><div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;background:linear-gradient(135deg,#e8173a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{fmt_rp(total_rev)}</div></div>
    </div>
    <div class="card">
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;margin-bottom:1rem;">🎟️ Booking Terbaru</h2>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th>ID</th><th>User</th><th>Film</th><th>Total</th></tr></thead>
        <tbody>{recent_rows}</tbody>
      </table>
      <div style="margin-top:1rem;"><a href="/admin/bookings" class="btn btn-ghost btn-sm">Lihat Semua →</a></div>
    </div>'''
    return make_response(admin_base(content, 'dashboard'))

# ── ADMIN: KELOLA FILM ─────────────────────────────────────────────────────────
@app.route('/admin/films')
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

# ── ADMIN: TAMBAH FILM ─────────────────────────────────────────────────────────
@app.route('/admin/films/add', methods=['GET','POST'])
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

# ── ADMIN: EDIT FILM ───────────────────────────────────────────────────────────
@app.route('/admin/films/edit/<int:movie_id>', methods=['GET','POST'])
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

    return f'''
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.75rem;">
      <a href="/admin/films" class="btn btn-ghost btn-sm">← Kembali</a>
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;">{title}</h1>
    </div>
    <div style="display:grid;grid-template-columns:1fr 300px;gap:1.5rem;">
      <div class="card">
        <form method="POST">
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
            <input type="text" id="posterUrl" name="poster" value="{poster_val}" placeholder="https://..." oninput="prevPoster(this.value)" form="posterForm"/>
            <p style="color:#8888aa;font-size:.75rem;margin-top:.5rem;">Masukkan link gambar dari internet (JPG/PNG). Contoh dari Google Images: klik kanan gambar → "Salin alamat gambar"</p>
          </div>
          <div style="margin-top:1rem;display:flex;flex-direction:column;align-items:center;gap:.75rem;">
            {preview}
            <div id="noPreview" style="width:120px;height:170px;border:2px dashed rgba(255,255,255,.1);border-radius:10px;display:{"none" if poster_val else "flex"};align-items:center;justify-content:center;color:#8888aa;font-size:.8rem;text-align:center;">Belum ada<br/>gambar</div>
            <button type="button" onclick="testPoster()" style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);color:#f0f0f8;border-radius:8px;padding:.4rem .9rem;font-family:Outfit,sans-serif;font-size:.8rem;cursor:pointer;">🔍 Test Gambar</button>
          </div>
        </div>
      </div>
    </div>
    <script>
    // Sync poster URL input to main form
    document.querySelector('[name="poster"]').addEventListener('input', function(){{
      document.getElementById('posterUrl').value = this.value;
    }});
    // The poster input is already in the main form above via the oninput
    // We need to make sure the poster value is included in the main form submit
    document.querySelector('form').addEventListener('submit', function(){{
      const url = document.getElementById('posterUrl').value;
      let hidden = document.querySelector('input[name="poster"]');
      if(!hidden){{hidden=document.createElement('input');hidden.type='hidden';hidden.name='poster';this.appendChild(hidden);}}
      hidden.value = url;
    }});

    function prevPoster(url){{
      const img = document.getElementById('posterPreview');
      const no = document.getElementById('noPreview');
      if(url){{img.src=url;img.style.display='block';no.style.display='none';}}
      else{{img.style.display='none';no.style.display='flex';}}
    }}
    function testPoster(){{
      const url = document.getElementById('posterUrl').value;
      if(!url){{alert('Masukkan URL gambar terlebih dahulu!');return;}}
      const img = document.getElementById('posterPreview');
      img.src = url;
      img.style.display = 'block';
      img.onerror = function(){{alert('❌ Gambar tidak bisa dimuat! Coba URL lain.');img.style.display='none';document.getElementById('noPreview').style.display='flex';}};
      img.onload = function(){{alert('✅ Gambar berhasil dimuat!');document.getElementById('noPreview').style.display='none';}};
    }}
    </script>'''

# ── ADMIN: HAPUS FILM ──────────────────────────────────────────────────────────
@app.route('/admin/films/delete/<int:movie_id>')
def admin_film_delete(movie_id):
    if not admin_required(): return redirect('/admin')
    db = get_db()
    movie = next((m for m in db['movies'] if m['id']==movie_id), None)
    if movie:
        db['movies'] = [m for m in db['movies'] if m['id'] != movie_id]
        save_db(db)
        flash_msg(f'Film "{movie["title"]}" berhasil dihapus!','success')
    return redirect('/admin/films')

# ── ADMIN: BOOKINGS ────────────────────────────────────────────────────────────
@app.route('/admin/bookings')
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

# ── ADMIN: USERS ───────────────────────────────────────────────────────────────
@app.route('/admin/users')
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

# ── ADMIN LOGOUT ───────────────────────────────────────────────────────────────
@app.route('/admin/logout')
def admin_logout():
    session.pop('role', None)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
