from flask import Blueprint, request, redirect, session, make_response
from datetime import datetime
from helpers import flash_msg, base
from database import get_db, save_db, get_movies, fmt_rp, CINEMAS, SEAT_PRICE

booking_bp = Blueprint('booking', __name__)


@booking_bp.route('/booking/<int:movie_id>', methods=['GET','POST'])
def booking(movie_id):
    if 'user' not in session:
        flash_msg('Silakan login terlebih dahulu', 'warning')
        return redirect('/login')

    movies = get_movies()
    m = next((x for x in movies if x['id'] == movie_id), None)
    if not m:
        return redirect('/')

    if request.method == 'POST':
        seats = request.form.getlist('seats')
        if not seats:
            flash_msg('Pilih minimal 1 kursi!', 'danger')
            return redirect(f'/booking/{movie_id}')

        seat_type = request.form.get('seat_type', 'Reguler')
        total = len(seats) * SEAT_PRICE[seat_type]
        bk = {
            "id": f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user": session['user'],
            "movie": m['title'],
            "cinema": request.form.get('cinema'),
            "date": request.form.get('date'),
            "time": request.form.get('showtime'),
            "seats": seats,
            "seat_type": seat_type,
            "total": total,
            "status": "confirmed",
            "booked_at": datetime.now().isoformat()
        }
        db = get_db()
        db['bookings'].append(bk)
        save_db(db)
        session['last_booking'] = bk
        return redirect(f'/payment/{bk["id"]}')

    cinema_opts = ''.join(f'<option value="{c}">{c}</option>' for c in CINEMAS)
    time_btns = ''.join(
        f'<button type="button" onclick="selTime(this,\'{t}\')" style="padding:.45rem 1rem;border:1px solid rgba(255,255,255,.1);border-radius:8px;background:transparent;color:#f0f0f8;font-family:Outfit,sans-serif;font-size:.85rem;font-weight:600;cursor:pointer;transition:all .2s;">{t}</button>'
        for t in m.get('showtimes', [])
    )
    type_btns = ''.join(
        f'<button type="button" onclick="selType(this,\'{n}\')" style="padding:.8rem;border:2px solid rgba(255,255,255,.1);border-radius:12px;background:transparent;cursor:pointer;text-align:left;transition:all .2s;color:#f0f0f8;font-family:Outfit,sans-serif;"><div style="font-weight:700;font-size:.9rem;">{n}</div><div style="color:#e8173a;font-size:.85rem;font-weight:600;">{fmt_rp(p)}</div></button>'
        for n, p in SEAT_PRICE.items()
    )

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
