import urllib.request, base64, json as _json
from flask import Blueprint, request, redirect, session, make_response
from helpers import flash_msg, base
from database import get_db, save_db, fmt_rp

payment_bp = Blueprint('payment', __name__)

MIDTRANS_SERVER_KEY = 'Mid-server-UWdwnCZyJi4yuj1jUvHaCKjq'
MIDTRANS_CLIENT_KEY = 'Mid-client-CnZrBGXckbxkkT3-'
MIDTRANS_BASE_URL = 'https://app.sandbox.midtrans.com/snap/v1/transactions'


# ── HALAMAN PEMBAYARAN ────────────────────────────────────────────────────────
@payment_bp.route('/payment/<booking_id>')
@payment_bp.route('/payment/<booking_id>/<method>')
def payment(booking_id, method=''):
    bk = session.get('last_booking')
    if not bk or bk['id'] != booking_id:
        return redirect('/')

    db = get_db()
    qris_image = db.get('payment_settings', {}).get('qris_image', '')

    seat_tags = ''.join(
        f'<span style="background:rgba(232,23,58,.15);border:1px solid rgba(232,23,58,.3);color:#e8173a;padding:.3rem .65rem;border-radius:6px;font-size:.85rem;font-weight:700;">{s}</span>'
        for s in bk['seats']
    )

    # ── Blok QRIS ─────────────────────────────────────────────
    if qris_image:
        qris_block = f'''
        <div style="text-align:center;margin-bottom:1rem;">
          <p style="color:#8888aa;font-size:.8rem;margin-bottom:.75rem;">Scan QR code di bawah dengan aplikasi dompet digital manapun</p>
          <div style="display:inline-block;background:white;padding:12px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.4);">
            <img src="{qris_image}" alt="QR Code QRIS" style="display:block;width:200px;height:200px;object-fit:contain;" onerror="this.parentElement.innerHTML='<p style=color:#f87171;padding:1rem;>Gambar QR tidak bisa dimuat</p>'"/>
          </div>
          <p style="color:#ffd700;font-size:.8rem;margin-top:.75rem;">⏱ QR berlaku 15 menit</p>
        </div>'''
    else:
        qris_block = '''
        <div style="text-align:center;margin-bottom:1rem;padding:1.5rem;background:#11111e;border-radius:12px;">
          <div style="font-size:3rem;margin-bottom:.5rem;">⚠️</div>
          <p style="color:#fbbf24;font-size:.9rem;font-weight:600;">QR Code belum diatur oleh admin.</p>
          <p style="color:#8888aa;font-size:.8rem;margin-top:.25rem;">Silakan hubungi customer service untuk melakukan pembayaran QRIS.</p>
        </div>'''

    # ── Tombol konfirmasi bayar QRIS ───────────────────────────
    qris_confirm_btn = f'''
    <div id="qris-confirm-area" style="margin-top:1rem;">
      <button onclick="showConfirmQris()" class="btn btn-green" style="width:100%;justify-content:center;">
        ✅ Saya Sudah Bayar via QRIS
      </button>
    </div>
    <div id="qris-success" style="display:none;margin-top:1rem;background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.35);border-radius:14px;padding:1.5rem;text-align:center;">
      <div style="font-size:3rem;margin-bottom:.75rem;">🎉</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;color:#34d399;margin-bottom:.5rem;">Pembayaran Tiket Berhasil!</div>
      <p style="color:#c0fce8;font-size:.9rem;margin-bottom:1rem;">Terima kasih! Tiket kamu sudah dikonfirmasi. Silakan cek halaman tiket saya.</p>
      <a href="/my-tickets" class="btn btn-green">🎟️ Lihat Tiket Saya</a>
    </div>'''

    # ── Blok metode non-QRIS (semua punya gambar/info detail) ─
    def method_active(m):
        return 'block' if method == m else 'none'

    def border_active(m, color):
        return f'rgba({color},.5)' if method == m else 'rgba(255,255,255,.1)'

    # Blok konfirmasi bayar untuk metode non-QRIS
    def confirm_btn_non_qris(mid):
        return f'''
        <div style="margin-top:1.25rem;">
          <button onclick="showSuccessNonQris('{mid}')" class="btn btn-green" style="width:100%;justify-content:center;">
            ✅ Konfirmasi Pembayaran Selesai
          </button>
        </div>
        <div id="success-{mid}" style="display:none;margin-top:1rem;background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.35);border-radius:14px;padding:1.5rem;text-align:center;">
          <div style="font-size:3rem;margin-bottom:.75rem;">🎉</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;color:#34d399;margin-bottom:.5rem;">Pembayaran Tiket Berhasil!</div>
          <p style="color:#c0fce8;font-size:.9rem;margin-bottom:1rem;">Terima kasih telah melakukan pembayaran. Tiket kamu aktif.</p>
          <a href="/my-tickets" class="btn btn-green">🎟️ Lihat Tiket Saya</a>
        </div>'''

    content = f'''
    <div style="max-width:720px;margin:0 auto;padding:2.5rem 1.5rem;">
      <div style="text-align:center;padding:1rem;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:12px;color:#34d399;font-size:.95rem;margin-bottom:2rem;">
        🎉 Pemesanan dikonfirmasi! Selamat menikmati <strong>{bk['movie']}</strong>
      </div>

      <!-- Tiket Detail -->
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

      <!-- Pilih Metode -->
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;margin-bottom:1.25rem;">💳 Pilih Metode Pembayaran</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1.5rem;">
        <a href="/payment/{bk['id']}/qris" style="padding:1rem;border:2px solid {border_active('qris','255,215,0')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>💰</div><div style='font-size:.8rem;font-weight:600;'>QRIS</div></a>
        <a href="/payment/{bk['id']}/gopay" style="padding:1rem;border:2px solid {border_active('gopay','0,174,214')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>📱</div><div style='font-size:.8rem;font-weight:600;'>GoPay/OVO</div></a>
        <a href="/payment/{bk['id']}/va" style="padding:1rem;border:2px solid {border_active('va','59,130,246')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>🏦</div><div style='font-size:.8rem;font-weight:600;'>Virtual Account</div></a>
        <a href="/payment/{bk['id']}/transfer" style="padding:1rem;border:2px solid {border_active('transfer','52,211,153')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>💳</div><div style='font-size:.8rem;font-weight:600;'>Transfer Bank</div></a>
        <a href="/payment/{bk['id']}/minimarket" style="padding:1rem;border:2px solid {border_active('minimarket','249,115,22')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>🏪</div><div style='font-size:.8rem;font-weight:600;'>Minimarket</div></a>
        <a href="/payment/{bk['id']}/kartu" style="padding:1rem;border:2px solid {border_active('kartu','167,139,250')};border-radius:12px;text-align:center;text-decoration:none;color:#f0f0f8;display:block;transition:border-color .2s;"><div style='font-size:1.6rem;margin-bottom:.25rem;'>💎</div><div style='font-size:.8rem;font-weight:600;'>Kartu Kredit</div></a>
      </div>

      <!-- === QRIS === -->
      <div id="pay-qris" style="display:{method_active('qris')};background:#181828;border:1px solid rgba(255,215,0,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#ffd700;">💰 Bayar via QRIS</div>
        {qris_block}
        {qris_confirm_btn}
      </div>

      <!-- === GOPAY === -->
      <div id="pay-gopay" style="display:{method_active('gopay')};background:#181828;border:1px solid rgba(0,174,214,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#00aed6;">📱 Bayar via GoPay / OVO</div>
        <div style="background:#11111e;border-radius:10px;padding:1rem;margin-bottom:.75rem;">
          <div style="font-size:.8rem;color:#8888aa;margin-bottom:.25rem;">Nomor GoPay / OVO Tujuan</div>
          <div style="font-size:1.5rem;font-weight:700;letter-spacing:2px;color:#00aed6;">0812-3456-7890</div>
        </div>
        <div style="background:#11111e;border-radius:10px;padding:1rem;">
          <div style="font-size:.8rem;color:#8888aa;margin-bottom:.25rem;">Nama Penerima</div>
          <div style="font-size:1rem;font-weight:700;">CineMax Official</div>
        </div>
        <p style="color:#8888aa;font-size:.8rem;margin-top:1rem;">Buka aplikasi GoPay/OVO → Transfer → masukkan nomor di atas → masukkan nominal tepat.</p>
        {confirm_btn_non_qris('gopay')}
      </div>

      <!-- === VIRTUAL ACCOUNT === -->
      <div id="pay-va" style="display:{method_active('va')};background:#181828;border:1px solid rgba(59,130,246,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#3b82f6;">🏦 Bayar via Virtual Account</div>
        <div style="display:grid;gap:.75rem;">
          <div style="background:#11111e;border-radius:10px;padding:1rem;cursor:pointer;" onclick="copyVA('BCA','1234567890123456')">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div><div style="font-size:.8rem;color:#8888aa;">BCA Virtual Account</div><div style="font-size:1.2rem;font-weight:700;letter-spacing:2px;">1234 5678 9012 3456</div></div>
              <span style="font-size:1.2rem;">📋</span>
            </div>
          </div>
          <div style="background:#11111e;border-radius:10px;padding:1rem;cursor:pointer;" onclick="copyVA('Mandiri','8877665544332211')">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div><div style="font-size:.8rem;color:#8888aa;">Mandiri Virtual Account</div><div style="font-size:1.2rem;font-weight:700;letter-spacing:2px;">8877 6655 4433 2211</div></div>
              <span style="font-size:1.2rem;">📋</span>
            </div>
          </div>
          <div style="background:#11111e;border-radius:10px;padding:1rem;cursor:pointer;" onclick="copyVA('BNI','9988776655443322')">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div><div style="font-size:.8rem;color:#8888aa;">BNI Virtual Account</div><div style="font-size:1.2rem;font-weight:700;letter-spacing:2px;">9988 7766 5544 3322</div></div>
              <span style="font-size:1.2rem;">📋</span>
            </div>
          </div>
        </div>
        <p style="color:#8888aa;font-size:.8rem;margin-top:1rem;">Klik nomor untuk menyalin. Masukkan nominal tepat sesuai tagihan.</p>
        {confirm_btn_non_qris('va')}
      </div>

      <!-- === TRANSFER BANK === -->
      <div id="pay-transfer" style="display:{method_active('transfer')};background:#181828;border:1px solid rgba(52,211,153,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#34d399;">💳 Transfer Bank</div>
        <div style="background:#11111e;border-radius:10px;padding:1rem;margin-bottom:.75rem;">
          <div style="font-size:.8rem;color:#8888aa;margin-bottom:.25rem;">Bank BCA</div>
          <div style="font-size:1.5rem;font-weight:700;letter-spacing:2px;">1234 567 890</div>
          <div style="font-size:.9rem;color:#8888aa;margin-top:.25rem;">a/n CineMax Indonesia</div>
        </div>
        <div style="background:#11111e;border-radius:10px;padding:1rem;">
          <div style="font-size:.8rem;color:#8888aa;margin-bottom:.25rem;">Bank Mandiri</div>
          <div style="font-size:1.5rem;font-weight:700;letter-spacing:2px;">156 000 1234 5678</div>
          <div style="font-size:.9rem;color:#8888aa;margin-top:.25rem;">a/n CineMax Indonesia</div>
        </div>
        <p style="color:#fbbf24;font-size:.8rem;margin-top:1rem;">⚠️ Transfer tepat sesuai nominal tagihan</p>
        {confirm_btn_non_qris('transfer')}
      </div>

      <!-- === MINIMARKET === -->
      <div id="pay-minimarket" style="display:{method_active('minimarket')};background:#181828;border:1px solid rgba(249,115,22,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#f97316;">🏪 Bayar di Minimarket</div>
        <div style="background:#11111e;border-radius:10px;padding:1.25rem;text-align:center;margin-bottom:.75rem;">
          <div style="font-size:.8rem;color:#8888aa;margin-bottom:.5rem;">Kode Pembayaran</div>
          <div style="font-size:2rem;font-weight:700;letter-spacing:4px;color:#f97316;">8521 4739 2610</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:.5rem;text-align:center;">
          <div style="background:#11111e;border-radius:8px;padding:.75rem;font-size:.8rem;font-weight:600;">Indomaret</div>
          <div style="background:#11111e;border-radius:8px;padding:.75rem;font-size:.8rem;font-weight:600;">Alfamart</div>
          <div style="background:#11111e;border-radius:8px;padding:.75rem;font-size:.8rem;font-weight:600;">Alfamidi</div>
        </div>
        <p style="color:#8888aa;font-size:.8rem;margin-top:1rem;">Tunjukkan kode ini ke kasir minimarket terdekat</p>
        {confirm_btn_non_qris('minimarket')}
      </div>

      <!-- === KARTU KREDIT === -->
      <div id="pay-kartu" style="display:{method_active('kartu')};background:#181828;border:1px solid rgba(167,139,250,.2);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;margin-bottom:1rem;color:#a78bfa;">💎 Kartu Kredit / Debit</div>
        <div class="form-group"><label>Nomor Kartu</label><input type="text" placeholder="1234 5678 9012 3456" maxlength="19" oninput="fmtCard(this)" style="font-size:1.1rem;letter-spacing:2px;"/></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
          <div class="form-group"><label>Berlaku Hingga</label><input type="text" placeholder="MM/YY" maxlength="5"/></div>
          <div class="form-group"><label>CVV</label><input type="password" placeholder="***" maxlength="3"/></div>
        </div>
        <div class="form-group"><label>Nama di Kartu</label><input type="text" placeholder="NAMA LENGKAP"/></div>
        {confirm_btn_non_qris('kartu')}
      </div>

      <!-- Total & Bayar Midtrans -->
      <div style="background:linear-gradient(135deg,rgba(232,23,58,.1),rgba(255,107,53,.1));border:1px solid rgba(232,23,58,.3);border-radius:16px;padding:1.5rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;">
        <div>
          <div style="color:#8888aa;font-size:.9rem;">Total Pembayaran</div>
          <div style="color:#8888aa;font-size:.8rem;">{len(bk['seats'])} kursi × {bk['seat_type']}</div>
        </div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;color:#e8173a;">{fmt_rp(bk['total'])}</div>
      </div>

      <button class="btn btn-red" style="width:100%;justify-content:center;font-size:1.05rem;padding:.9rem;" id="pay-btn" onclick="bayarMidtrans()">
        💳 Bayar via Midtrans (Semua Metode)
      </button>
      <div style="text-align:center;margin-top:1rem;">
        <a href="/my-tickets" style="color:#8888aa;font-size:.9rem;">Lihat semua tiket saya →</a>
      </div>
    </div>

    <script src="https://app.sandbox.midtrans.com/snap/snap.js" data-client-key="Mid-client-CnZrBGXckbxkkT3-"></script>
    <script>
    function copyVA(bank, num) {{
      navigator.clipboard.writeText(num)
        .then(() => alert('✅ Nomor VA ' + bank + ' berhasil disalin!'))
        .catch(() => alert('Nomor VA ' + bank + ': ' + num));
    }}
    function fmtCard(el) {{
      let v = el.value.replace(/[^0-9]/g,'').substring(0,16);
      el.value = v.replace(/(\d{{4}})/g,'$1 ').trim();
    }}
    function showConfirmQris() {{
      document.getElementById('qris-confirm-area').style.display = 'none';
      document.getElementById('qris-success').style.display = 'block';
      document.getElementById('qris-success').scrollIntoView({{behavior:'smooth'}});
    }}
    function showSuccessNonQris(id) {{
      document.getElementById('success-' + id).style.display = 'block';
      document.getElementById('success-' + id).scrollIntoView({{behavior:'smooth'}});
    }}
    function bayarMidtrans() {{
      fetch('/create-payment/{bk["id"]}', {{method:'POST'}})
        .then(r => r.json())
        .then(data => {{
          if(data.token) {{
            snap.pay(data.token, {{
              onSuccess: function(result) {{
                alert('✅ Pembayaran berhasil!');
                window.location.href = '/my-tickets';
              }},
              onPending: function(result) {{
                alert('⏳ Pembayaran pending. Selesaikan pembayaranmu.');
              }},
              onError: function(result) {{
                alert('❌ Pembayaran gagal. Coba lagi.');
              }},
              onClose: function() {{
                alert('Popup ditutup sebelum menyelesaikan pembayaran.');
              }}
            }});
          }} else {{
            alert('Gagal membuat transaksi: ' + (data.error || 'Unknown error'));
          }}
        }})
        .catch(e => alert('Error: ' + e));
    }}
    </script>'''

    return make_response(base(content, f'Pembayaran - {bk["movie"]}'))


# ── CREATE MIDTRANS PAYMENT ───────────────────────────────────────────────────
@payment_bp.route('/create-payment/<booking_id>', methods=['POST'])
def create_payment(booking_id):
    bk = session.get('last_booking')
    if not bk or bk['id'] != booking_id:
        return {'error': 'Booking tidak ditemukan'}, 404

    payload = {
        "transaction_details": {
            "order_id": bk['id'],
            "gross_amount": bk['total']
        },
        "customer_details": {
            "first_name": bk['user'],
            "email": bk['user'] + "@cinemax.com"
        },
        "item_details": [{
            "id": str(bk.get('movie','film')),
            "price": bk['total'],
            "quantity": 1,
            "name": f"Tiket {bk['movie']} - {', '.join(bk['seats'])}"
        }]
    }

    try:
        data = _json.dumps(payload).encode()
        auth = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
        req = urllib.request.Request(
            MIDTRANS_BASE_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth}'
            }
        )
        with urllib.request.urlopen(req) as resp:
            result = _json.loads(resp.read())
            return {'token': result.get('token'), 'redirect_url': result.get('redirect_url')}
    except Exception as e:
        return {'error': str(e)}, 500
