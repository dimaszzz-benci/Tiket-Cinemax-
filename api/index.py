import os, json, hashlib, uuid, tempfile
from flask import Flask, request, render_template, redirect, session, send_from_directory, flash, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'cinemax_v2')

# ── DB (JSON ephemeral for Vercel) ──
DB = tempfile.mktemp(suffix='.json')
def get_db():
    if not os.path.exists(DB):
        json.dump({"users":[],"bookings":[],"movies":[],
                   "admin":{"user":"admin","pass":hashlib.md5(b"admin123").hexdigest()},
                   "qr_image":None}, open(DB,'w'))
    return json.load(open(DB))
def save_db(d): json.dump(d, open(DB,'w'), indent=2)

# ── Uploads ──
UPLOAD_DIR = tempfile.mkdtemp(prefix='cinemax_')
ALLOWED = {'png','jpg','jpeg','gif'}
def allowed(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED

@app.route('/uploads/<fn>')
def uploaded_file(fn): return send_from_directory(UPLOAD_DIR, fn)

# ── Routes ──
@app.route('/')
def index(): return render_template('index.html', movies=get_db()['movies'])

@app.route('/movie/<int:mid>')
def detail(mid):
    m = next((x for x in get_db()['movies'] if x['id']==mid), None)
    return redirect('/') if not m else render_template('movie_detail.html', movie=m)

@app.route('/booking/<int:mid>', methods=['GET','POST'])
def booking(mid):
    if 'user' not in session: return redirect('/login')
    db, m = get_db(), next((x for x in get_db()['movies'] if x['id']==mid), None)
    if not m: return redirect('/')
    if request.method == 'POST':
        seats = request.form.getlist('seats')
        if len(seats) < 3 or len(seats) > 8:
            flash('Wajib pilih 3-8 kursi!', 'danger'); return redirect(request.url)
        bk = {"id":f"TKT{uuid.uuid4().hex[:16].upper()}","user":session['user'],"movie":m['title'],
              "cinema":request.form['cinema'],"date":request.form['date'],
              "time":request.form['time'],"seats":seats,"seat_type":request.form['type'],
              "method":request.form['method'],"total":len(seats)*int(request.form['price']),
              "status":"paid","booked_at":"2026-04-14T12:00:00"}
        db['bookings'].append(bk); save_db(db); session['last_bk']=bk
        return redirect(f'/payment/{bk["id"]}')
    return render_template('booking.html', movie=m, cinemas=["CGV","XXI","Cinepolis"],
                           dates=["2026-04-15","2026-04-16","2026-04-17"],
                           prices={"Reguler":45000,"Premium":75000,"IMAX":95000})

@app.route('/payment/<bkid>')
def payment(bkid):
    bk = session.get('last_bk')
    if not bk or bk['id']!=bkid: return redirect('/')
    db = get_db()
    qr_image = db.get('qr_image')
    return render_template('payment.html', booking=bk, qr_image=qr_image)

@app.route('/my-tickets')
def my_tickets():
    if 'user' not in session: return redirect('/login')
    bks = [b for b in get_db()['bookings'] if b['user']==session['user']]
    return render_template('my_tickets.html', bookings=bks)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        db = get_db()
        u = next((x for x in db['users'] if x['user']==request.form['user'] and x['pass']==hashlib.md5(request.form['pass'].encode()).hexdigest()), None)
        if u: session['user']=u['user']; return redirect('/')
        flash('Akun tidak ditemukan', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        db = get_db()
        if any(u['user']==request.form['user'] for u in db['users']):
            flash('Username sudah dipakai', 'danger')
        else:
            db['users'].append({"user":request.form['user'],"email":request.form['email'],
                                "pass":hashlib.md5(request.form['pass'].encode()).hexdigest()})
            save_db(db); flash('Berhasil! Silakan login', 'success'); return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

# ── ADMIN ──
def admin_ok(): return session.get('role')=='admin'

@app.route('/admin/', methods=['GET','POST'])
@app.route('/admin', methods=['GET','POST'])
def admin():
    if not admin_ok():
        if request.method=='POST':
            db = get_db()
            if request.form['user']==db['admin']['user'] and hashlib.md5(request.form['pass'].encode()).hexdigest()==db['admin']['pass']:
                session['role']='admin'; return redirect('/admin/')
            flash('Kredensial salah', 'danger')
        return render_template('admin/login.html')
    db = get_db()
    total_pendapatan = sum(b.get('total',0) for b in db['bookings'])
    return render_template('admin/dashboard.html',
                           bookings=db['bookings'],
                           users=db['users'],
                           movies=db['movies'],
                           qr_image=db.get('qr_image'),
                           total_pendapatan=total_pendapatan)

@app.route('/admin/films')
def admin_films():
    if not admin_ok(): return redirect('/admin/')
    return render_template('admin/films.html', movies=get_db()['movies'])

@app.route('/admin/bookings')
def admin_bookings():
    if not admin_ok(): return redirect('/admin/')
    db = get_db()
    return render_template('admin/bookings.html', bookings=db['bookings'])

@app.route('/admin/users')
def admin_users():
    if not admin_ok(): return redirect('/admin/')
    db = get_db()
    return render_template('admin/users.html', users=db['users'])

@app.route('/admin/film/<act>', methods=['GET','POST'])
@app.route('/admin/film/<act>/<int:mid>', methods=['GET','POST'])
def admin_film_act(act, mid=None):
    if not admin_ok(): return redirect('/admin/')
    db = get_db()
    if request.method=='POST':
        showtimes = [t.strip() for t in request.form.get('showtimes','').split(',') if t.strip()] or ["10:00","13:00","19:00"]
        poster = request.form.get('poster_url','').strip()
        f = request.files.get('poster_file')
        if f and f.filename and allowed(f.filename):
            fn = secure_filename(f.filename); f.save(os.path.join(UPLOAD_DIR, fn))
            poster = url_for('uploaded_file', fn=fn, _external=False)
        data = {"title":request.form['title'],"genre":request.form['genre'],"duration":request.form['duration'],
                "rating":request.form['rating'],"score":float(request.form.get('score',0)),
                "poster":poster,"description":request.form['description'],"cast":request.form['cast'],
                "director":request.form['director'],"showtimes":showtimes}
        if act=='add':
            data['id'] = max([m['id'] for m in db['movies']], default=0)+1
            db['movies'].append(data)
        elif act=='edit' and mid:
            for m in db['movies']:
                if m['id']==mid: m.update(data); break
        save_db(db); return redirect('/admin/films')
    
    movie = next((m for m in db['movies'] if m['id']==mid), {}) if act=='edit' else {}
    return render_template('admin/film_form.html', movie=movie, act=act)

@app.route('/admin/film/del/<int:mid>')
def admin_film_del(mid):
    if not admin_ok(): return redirect('/admin/')
    db = get_db(); db['movies']=[m for m in db['movies'] if m['id']!=mid]; save_db(db)
    return redirect('/admin/films')

# ── QR PEMBAYARAN ──
@app.route('/admin/qr', methods=['POST'])
def admin_qr():
    if not admin_ok(): return redirect('/admin/')
    f = request.files.get('qr_file')
    if f and f.filename and allowed(f.filename):
        fn = secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_DIR, fn))
        qr_url = url_for('uploaded_file', fn=fn, _external=False)
        db = get_db()
        db['qr_image'] = qr_url
        save_db(db)
        flash('QR Pembayaran berhasil diupload!', 'success')
    else:
        flash('File tidak valid. Gunakan PNG/JPG/JPEG/GIF.', 'danger')
    return redirect('/admin/')

@app.route('/admin/logout')
def admin_logout(): session.pop('role',None); return redirect('/admin/')
