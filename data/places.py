"""Town/neighbourhood -> (JPS state code, JPS district) gazetteer.

JPS publishes no station coordinates, so "where am I" must resolve to a JPS
district by name. This table maps the places people actually type (towns,
suburbs, aliases, common misspellings) to the district JPS uses. Anything not
here falls through to jps.nearest()'s fuzzy match; the UI must show which
district was picked so the inference is visible.
"""
import re

# (state_code, district) exactly as they appear in data/jps.py output.
PLACES = {
    # --- Kuala Lumpur (WLH) ---
    "kuala lumpur": ("WLH", "Kuala Lumpur"), "kl": ("WLH", "Kuala Lumpur"),
    "bangsar": ("WLH", "Kuala Lumpur"), "bukit bintang": ("WLH", "Kuala Lumpur"),
    "kampung baru": ("WLH", "Kuala Lumpur"), "kg baru": ("WLH", "Kuala Lumpur"), "kg. baru": ("WLH", "Kuala Lumpur"),
    "chow kit": ("WLH", "Kuala Lumpur"), "brickfields": ("WLH", "Kuala Lumpur"), "cheras": ("WLH", "Kuala Lumpur"),
    "sri petaling": ("WLH", "Kuala Lumpur"), "bukit jalil": ("WLH", "Kuala Lumpur"), "mont kiara": ("WLH", "Kuala Lumpur"),
    "ttdi": ("WLH", "Kuala Lumpur"), "taman tun": ("WLH", "Kuala Lumpur"), "sentul": ("WLH", "Kuala Lumpur"),
    "setapak": ("WLH", "Kuala Lumpur"), "wangsa maju": ("WLH", "Kuala Lumpur"), "titiwangsa": ("WLH", "Kuala Lumpur"),
    "kepong": ("WLH", "Kuala Lumpur"), "segambut": ("WLH", "Kuala Lumpur"), "jalan ipoh": ("WLH", "Kuala Lumpur"),
    "masjid india": ("WLH", "Kuala Lumpur"), "dataran merdeka": ("WLH", "Kuala Lumpur"), "klcc": ("WLH", "Kuala Lumpur"),
    "batu caves": ("WLH", "Gombak (WPKL)"), "gombak": ("WLH", "Gombak (WPKL)"), "taman melati": ("WLH", "Gombak (WPKL)"),
    "selayang": ("SEL", "Gombak"), "rawang": ("SEL", "Gombak"), "kundang": ("SEL", "Gombak"),
    # --- Selangor (SEL) ---
    "selangor": ("SEL", "Petaling"), "shah alam": ("SEL", "Petaling"), "petaling jaya": ("SEL", "Petaling"), "pj": ("SEL", "Petaling"),
    "subang jaya": ("SEL", "Petaling"), "subang": ("SEL", "Petaling"), "usj": ("SEL", "Petaling"), "puchong": ("SEL", "Petaling"),
    "damansara": ("SEL", "Petaling"), "kota damansara": ("SEL", "Petaling"), "bandar utama": ("SEL", "Petaling"), "sunway": ("SEL", "Petaling"),
    "seri kembangan": ("SEL", "Petaling"), "sri kembangan": ("SEL", "Petaling"), "ara damansara": ("SEL", "Petaling"),
    "klang": ("SEL", "Klang"), "port klang": ("SEL", "Klang"), "kapar": ("SEL", "Klang"), "meru": ("SEL", "Klang"),
    "kajang": ("SEL", "Hulu Langat"), "bangi": ("SEL", "Hulu Langat"), "ampang": ("SEL", "Hulu Langat"), "semenyih": ("SEL", "Hulu Langat"),
    "hulu langat": ("SEL", "Hulu Langat"), "cheras selangor": ("SEL", "Hulu Langat"), "balakong": ("SEL", "Hulu Langat"),
    "sepang": ("SEL", "Sepang"), "cyberjaya": ("SEL", "Sepang"), "klia": ("SEL", "Sepang"), "dengkil": ("SEL", "Sepang"),
    "putrajaya": ("SEL", "Sepang"),  # Putrajaya has 0 public JPS stations; nearest district
    "banting": ("SEL", "Kuala Langat"), "kuala langat": ("SEL", "Kuala Langat"), "jenjarom": ("SEL", "Kuala Langat"),
    "kuala selangor": ("SEL", "Kuala Selangor"), "ijok": ("SEL", "Kuala Selangor"), "bestari jaya": ("SEL", "Kuala Selangor"),
    "hulu selangor": ("SEL", "Hulu Selangor"), "kuala kubu bharu": ("SEL", "Hulu Selangor"), "kkb": ("SEL", "Hulu Selangor"),
    "batang kali": ("SEL", "Hulu Selangor"), "serendah": ("SEL", "Hulu Selangor"), "sabak bernam": ("SEL", "Sabak Bernam"),
    "sungai besar": ("SEL", "Sabak Bernam"), "tanjung karang": ("SEL", "Kuala Selangor"),
    # --- Johor (JHR) ---
    "johor": ("JHR", "Johor Bahru"), "johor bahru": ("JHR", "Johor Bahru"), "jb": ("JHR", "Johor Bahru"), "skudai": ("JHR", "Johor Bahru"),
    "iskandar puteri": ("JHR", "Johor Bahru"), "pasir gudang": ("JHR", "Johor Bahru"), "kulai": ("JHR", "Kulai"), "senai": ("JHR", "Kulai"),
    "batu pahat": ("JHR", "Batu Pahat"), "kluang": ("JHR", "Kluang"), "kota tinggi": ("JHR", "Kota Tinggi"), "mersing": ("JHR", "Mersing"),
    "muar": ("JHR", "Muar"), "pontian": ("JHR", "Pontian"), "segamat": ("JHR", "Segamat"), "tangkak": ("JHR", "Tangkak"),
    # --- Kedah (KDH) / Perlis (PLS) / Penang (PNG) ---
    "kedah": ("KDH", "Kota Setar"), "alor setar": ("KDH", "Kota Setar"), "alor star": ("KDH", "Kota Setar"), "kota setar": ("KDH", "Kota Setar"),
    "sungai petani": ("KDH", "Kuala Muda"), "sp": ("KDH", "Kuala Muda"), "kulim": ("KDH", "Kulim"), "jitra": ("KDH", "Kubang Pasu"),
    "langkawi": ("KDH", "Kota Setar"),  # no Langkawi JPS station on the public page
    "baling": ("KDH", "Baling"), "pendang": ("KDH", "Pendang"), "sik": ("KDH", "Sik"), "yan": ("KDH", "Yan"),
    "perlis": ("PLS", "Kangar"), "kangar": ("PLS", "Kangar"), "arau": ("PLS", "Arau"), "padang besar": ("PLS", "Padang Besar"),
    "penang": ("PNG", "Timur Laut Pulau Pinang"), "pulau pinang": ("PNG", "Timur Laut Pulau Pinang"), "george town": ("PNG", "Timur Laut Pulau Pinang"),
    "georgetown": ("PNG", "Timur Laut Pulau Pinang"), "bayan lepas": ("PNG", "Barat Daya Pulau Pinang"), "balik pulau": ("PNG", "Barat Daya Pulau Pinang"),
    "butterworth": ("PNG", "Seberang Perai Utara"), "bukit mertajam": ("PNG", "Seberang Perai Tengah"), "nibong tebal": ("PNG", "Seberang Perai Selatan"),
    # --- Perak (PRK) ---
    "perak": ("PRK", "Kinta"), "ipoh": ("PRK", "Kinta"), "kinta": ("PRK", "Kinta"), "batu gajah": ("PRK", "Kinta"),
    "taiping": ("PRK", "Larut Matang dan Selama"), "kuala kangsar": ("PRK", "Kuala Kangsar"), "teluk intan": ("PRK", "Hilir Perak"),
    "kampar": ("PRK", "Kampar"), "gerik": ("PRK", "Hulu Perak"), "lumut": ("PRK", "Perak Tengah"), "sitiawan": ("PRK", "Perak Tengah"),
    "tanjung malim": ("PRK", "Muallim"), "parit buntar": ("PRK", "Kerian"), "bagan datuk": ("PRK", "Bagan Datuk"),
    # --- Negeri Sembilan (NSN) / Melaka (MLK) ---
    "negeri sembilan": ("NSN", "Seremban"), "seremban": ("NSN", "Seremban"), "nilai": ("NSN", "Seremban"), "port dickson": ("NSN", "Port Dickson"),
    "pd": ("NSN", "Port Dickson"), "kuala pilah": ("NSN", "Kuala Pilah"), "jelebu": ("NSN", "Jelebu"), "rembau": ("NSN", "Rembau"), "tampin": ("NSN", "Tampin"),
    "melaka": ("MLK", "Melaka Tengah"), "malacca": ("MLK", "Melaka Tengah"), "ayer keroh": ("MLK", "Melaka Tengah"),
    "alor gajah": ("MLK", "Alor Gajah"), "jasin": ("MLK", "Jasin"),
    # --- Pahang (PHG) ---
    "pahang": ("PHG", "Kuantan"), "kuantan": ("PHG", "Kuantan"), "bentong": ("PHG", "Bentong"), "genting": ("PHG", "Bentong"),
    "temerloh": ("PHG", "Temerloh"), "mentakab": ("PHG", "Temerloh"), "raub": ("PHG", "Raub"), "jerantut": ("PHG", "Jerantut"),
    "pekan": ("PHG", "Pekan"), "maran": ("PHG", "Maran"), "bera": ("PHG", "Bera"), "rompin": ("PHG", "Rompin"),
    "cameron highlands": ("PHG", "Cameron Highlands"), "kuala lipis": ("PHG", "Lipis"), "lipis": ("PHG", "Lipis"),
    # --- Terengganu (TRG) / Kelantan (KEL) ---
    "terengganu": ("TRG", "Kuala Terengganu"), "kuala terengganu": ("TRG", "Kuala Terengganu"), "kt": ("TRG", "Kuala Terengganu"),
    "kuala nerus": ("TRG", "Kuala Nerus"), "dungun": ("TRG", "Dungun"), "kemaman": ("TRG", "Kemaman"), "chukai": ("TRG", "Kemaman"),
    "besut": ("TRG", "Besut"), "marang": ("TRG", "Marang"), "setiu": ("TRG", "Setiu"), "hulu terengganu": ("TRG", "Hulu Terengganu"),
    "kelantan": ("KEL", "Kota Bharu"), "kota bharu": ("KEL", "Kota Bharu"), "kota baru": ("KEL", "Kota Bharu"), "kb": ("KEL", "Kota Bharu"),
    "pasir mas": ("KEL", "Pasir Mas"), "tumpat": ("KEL", "Tumpat"), "bachok": ("KEL", "Bachok"), "pasir puteh": ("KEL", "Pasir Puteh"),
    "machang": ("KEL", "Machang"), "tanah merah": ("KEL", "Tanah Merah"), "kuala krai": ("KEL", "Kuala Krai"), "gua musang": ("KEL", "Gua Musang"),
    "jeli": ("KEL", "Jeli"), "rantau panjang": ("KEL", "Pasir Mas"),
    # --- Sarawak (SRK) / Sabah (SAB) / Labuan (WLP) ---
    "sarawak": ("SRK", "Kuching"), "kuching": ("SRK", "Kuching"), "miri": ("SRK", "Miri"), "sibu": ("SRK", "Sibu"), "bintulu": ("SRK", "Bintulu"),
    "samarahan": ("SRK", "Samarahan"), "kota samarahan": ("SRK", "Samarahan"), "serian": ("SRK", "Serian"), "sri aman": ("SRK", "Sri Aman"),
    "betong": ("SRK", "Betong"), "sarikei": ("SRK", "Sarikei"), "kapit": ("SRK", "Kapit"), "mukah": ("SRK", "Mukah"), "limbang": ("SRK", "Limbang"),
    "sabah": ("SAB", "Penampang"), "kota kinabalu": ("SAB", "Penampang"), "kk": ("SAB", "Penampang"), "penampang": ("SAB", "Penampang"),
    "tawau": ("SAB", "Tawau"), "tambunan": ("SAB", "Tambunan"), "kinabatangan": ("SAB", "Kinabatangan"), "sandakan": ("SAB", "Kinabatangan"),
    "labuan": ("WLP", "Labuan"),
}

_norm_re = re.compile(r"[^a-z0-9 ]+")


def normalize(text: str) -> str:
    t = (text or "").lower().replace("kg.", "kg").replace("sg.", "sg")
    t = _norm_re.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def resolve(text: str):
    """Return (state_code, district, matched_key) or None.

    Longest matching gazetteer key contained in the text wins, so
    'Kg Baru Kuala Lumpur' -> Kuala Lumpur via 'kg baru' / 'kuala lumpur',
    'Cheras Selangor' -> Hulu Langat (longer key beats 'cheras').
    """
    t = normalize(text)
    if not t:
        return None
    if t in PLACES:
        return (*PLACES[t], t)
    best = None
    for key, val in PLACES.items():
        if re.search(rf"(^| ){re.escape(key)}( |$)", t):
            if best is None or len(key) > len(best[2]):
                best = (*val, key)
    return best


if __name__ == "__main__":
    tests = {
        "Shah Alam": ("SEL", "Petaling"), "Cheras": ("WLH", "Kuala Lumpur"), "Cheras Selangor": ("SEL", "Hulu Langat"),
        "Kg. Baru Kuala Lumpur": ("WLH", "Kuala Lumpur"), "gombak": ("WLH", "Gombak (WPKL)"), "Kota Bharu": ("KEL", "Kota Bharu"),
        "saya di bangsar sekarang": ("WLH", "Kuala Lumpur"), "Kuching": ("SRK", "Kuching"), "Atlantis": None,
    }
    for q, want in tests.items():
        got = resolve(q)
        got2 = got[:2] if got else None
        assert got2 == want, (q, got, want)
        print(f"{q!r:32} -> {got}")
    print(f"OK — {len(PLACES)} gazetteer entries")
