import hashlib, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

_DB = {
    "users": [],
    "bookings": [],
    "movies": list(DEFAULT_MOVIES),
    "admin": {"username": "admin", "password": hashlib.md5(b"admin123").hexdigest()},
    # Settings pembayaran: qris_image = URL/path gambar QR yang diset admin
    "payment_settings": {
        "qris_image": ""
    }
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

def fmt_rp(n):
    return 'Rp {:,}'.format(n).replace(',','.')
