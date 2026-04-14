from flask import session

def flash_msg(msg, cat='info'):
    if '_flashes' not in session:
        session['_flashes'] = []
    session['_flashes'].append((cat, msg))
    session.modified = True

def get_flashes():
    msgs = session.pop('_flashes', [])
    session.modified = True
    return msgs

def base(content, title="CineMax"):
    user = session.get('user', '')
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


def admin_base(content, active='dashboard'):
    from database import get_db
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
        ('payment_settings','💳 Pengaturan Bayar','/admin/payment-settings'),
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
body{{background:#090912;color:#f0f0f8;font-family:'Outfit',sans-serif;min-height:100vh;display:grid;grid-template-columns:230px 1fr;}}
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
