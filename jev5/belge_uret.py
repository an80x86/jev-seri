"""Uydurma Turkce belgeler + gercek kutular (piksel olarak biliniyor).

Uc sablon: fatura, basvuru formu, kargo etiketi. Her alanin degerinin kutusu
PIL textbbox ile kaydedilir. TC numaralari bilerek gecersiz (kontrol hanesi tutmaz),
IBAN'lar da gecersiz; isimler ve adresler uydurma.

Kosullar:
  temiz     : en uzun kenar 1568 px (API ust siniri)
  kucuk     : en uzun kenar 640 px
  telefon   : 1568 px, perspektif + donme + bulaniklik + golge, koyu zemin

  python3 belge_uret.py  ->  belgeler/*.jpg + belgeler/gercek.json
"""
import json
import math
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

KOK = pathlib.Path(__file__).resolve().parent
CIKTI = KOK / "belgeler"
F = "/System/Library/Fonts/Supplemental/Arial.ttf"
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
r = random.Random(14)

ADLAR = ["Ayşe Demirtaş", "Mehmet Kaplanoğlu", "Zeynep Arıkan", "Burak Sezgin", "Elif Korkmazer",
         "Hakan Yıldırımer", "Selin Öztunalı", "Emre Bakırcıoğlu", "Derya Gündoğar", "Ozan Tekinalp",
         "Gizem Karaburun", "Murat Esenkaya", "Seda Çağlayaner", "Kerem Durmuşoğlu", "Pınar Akbulutlu"]
SOKAK = ["Lale Sk.", "Menekşe Cd.", "Çınar Sk.", "Kavak Cd.", "Papatya Sk.", "Ihlamur Cd."]
ILCE = [("Kadıköy", "İstanbul"), ("Çankaya", "Ankara"), ("Bornova", "İzmir"), ("Nilüfer", "Bursa"),
        ("Konyaaltı", "Antalya"), ("Tepebaşı", "Eskişehir")]
URUN = ["Ofis sandalyesi", "Toner kartuşu", "A4 kağıt (5 top)", "Kablosuz klavye", "Monitör 27\"",
        "USB bellek 64 GB", "Masa lambası", "Dosya dolabı", "Projeksiyon perdesi", "Kulaklık"]


def tc():
    """11 hane, ilk hane sifir degil; kontrol haneleri bilerek bozuk (gercek kisiye denk gelmez)."""
    d = [r.randint(1, 9)] + [r.randint(0, 9) for _ in range(8)]
    h10 = ((sum(d[0:9:2]) * 7) - sum(d[1:8:2])) % 10
    h11 = (sum(d) + h10) % 10
    return "".join(map(str, d)) + str((h10 + 1) % 10) + str((h11 + 3) % 10)


def tel():
    return f"0 5{r.randint(30, 59)} {r.randint(100, 999)} {r.randint(10, 99)} {r.randint(10, 99)}"


def iban():
    s = "".join(str(r.randint(0, 9)) for _ in range(24))
    return "TR" + s[:2] + " " + " ".join(s[2 + 4 * k:6 + 4 * k] for k in range(5)) + " " + s[22:]


def tl(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def yazi(d, xy, metin, boy, kalin=False, renk="#111111"):
    f = ImageFont.truetype(FB if kalin else F, boy)
    d.text(xy, metin, font=f, fill=renk)
    return list(d.textbbox(xy, metin, font=f))


def imza(d, x, y, w, h):
    """Rastgele egri cizgilerle el yazisi benzeri imza; kutusunu dondurur."""
    pts = []
    for k in range(5):
        cx = x + w * (0.1 + 0.8 * k / 4) + r.uniform(-10, 10)
        for t in range(14):
            a = t / 13 * 2 * math.pi * r.uniform(0.8, 1.3)
            pts.append((cx + math.cos(a) * w * 0.08 + t * w * 0.012,
                        y + h / 2 + math.sin(a) * h * r.uniform(0.25, 0.45)))
    d.line(pts, fill="#1a2a6c", width=3, joint="curve")
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2]


def fatura(n):
    im = Image.new("RGB", (1240, 1754), "white"); d = ImageDraw.Draw(im); g = {}
    yazi(d, (80, 70), "ÖRNEK TİCARET A.Ş.", 40, True)
    yazi(d, (80, 125), "Merkez Mah. Sanayi Cd. No:12  Ümraniye / İstanbul  ·  Vergi D.: Alemdağ", 20)
    yazi(d, (880, 70), "FATURA", 48, True)
    yazi(d, (880, 135), f"No: ORN2026{r.randint(100000, 999999)}", 22)
    yazi(d, (880, 165), f"Tarih: {r.randint(1, 28):02d}.{r.randint(1, 9):02d}.2026", 22)
    d.rectangle((80, 230, 1160, 470), outline="#999999", width=2)
    ad = r.choice(ADLAR); ilce, il = r.choice(ILCE)
    yazi(d, (100, 250), "SAYIN", 20, True)
    g["ad"] = yazi(d, (100, 285), ad, 26, True)
    yazi(d, (100, 330), f"{r.choice(SOKAK)} No:{r.randint(1, 90)} D:{r.randint(1, 20)}  {ilce} / {il}", 22)
    yazi(d, (100, 375), "T.C. Kimlik No:", 22)
    g["tc"] = yazi(d, (290, 375), tc(), 22)
    yazi(d, (100, 415), "Telefon:", 22)
    g["telefon"] = yazi(d, (290, 415), tel(), 22)
    y = 520
    for b, x in (("Ürün / Hizmet", 100), ("Miktar", 640), ("Birim Fiyat", 780), ("Tutar", 990)):
        yazi(d, (x, y), b, 22, True)
    d.line((80, y + 40, 1160, y + 40), fill="#333333", width=2)
    toplam = 0
    for k in range(r.randint(3, 7)):
        y += 60; adet = r.randint(1, 12); fiyat = r.randint(50, 9000) + r.randint(0, 99) / 100
        toplam += adet * fiyat
        yazi(d, (100, y), r.choice(URUN), 22); yazi(d, (660, y), str(adet), 22)
        yazi(d, (780, y), tl(fiyat), 22); yazi(d, (990, y), tl(adet * fiyat), 22)
    y += 90; d.line((640, y - 20, 1160, y - 20), fill="#333333", width=2)
    yazi(d, (640, y), "KDV (%20):", 22); yazi(d, (990, y), tl(toplam * 0.2), 22)
    yazi(d, (640, y + 50), "GENEL TOPLAM:", 26, True)
    g["toplam"] = yazi(d, (990, y + 50), tl(toplam * 1.2), 26, True)
    yazi(d, (80, 1420), "Ödeme bilgileri:", 22, True)
    g["iban"] = yazi(d, (80, 1460), iban(), 24)
    yazi(d, (860, 1420), "Teslim alan imza:", 22, True)
    g["imza"] = imza(d, 860, 1460, 280, 120)
    return im, g


def form(n):
    im = Image.new("RGB", (1240, 1754), "white"); d = ImageDraw.Draw(im); g = {}
    yazi(d, (80, 80), "ÜYELİK BAŞVURU FORMU", 40, True)
    yazi(d, (80, 140), "Lütfen bilgileri eksiksiz doldurunuz.", 22, renk="#555555")
    ad = r.choice(ADLAR); ilce, il = r.choice(ILCE)
    satirlar = [("Ad Soyad", ad, "ad"), ("T.C. Kimlik No", tc(), "tc"),
                ("Doğum Tarihi", f"{r.randint(1, 28):02d}.{r.randint(1, 12):02d}.{r.randint(1960, 2004)}", None),
                ("Telefon", tel(), "telefon"),
                ("E-posta", ad.split()[0].lower().replace("ş", "s").replace("ü", "u").replace("ö", "o")
                 .replace("ı", "i").replace("ç", "c").replace("ğ", "g") + "@ornek.com.tr", None),
                ("Adres", f"{r.choice(SOKAK)} No:{r.randint(1, 90)}  {ilce} / {il}", None),
                ("Meslek", r.choice(["Öğretmen", "Mühendis", "Hemşire", "Muhasebeci", "Esnaf"]), None)]
    sira = list(range(len(satirlar))); y = 230
    for k in sira:
        etiket, deger, ad_ = satirlar[k]
        d.rectangle((80, y, 1160, y + 90), outline="#999999", width=2)
        yazi(d, (100, y + 30), etiket, 22, True)
        b = yazi(d, (420, y + 28), deger, 26)
        if ad_: g[ad_] = b
        y += 110
    yazi(d, (80, y + 40), "Kişisel verilerimin işlenmesine onay veriyorum.", 22)
    yazi(d, (80, y + 120), "İmza:", 22, True)
    g["imza"] = imza(d, 220, y + 90, 320, 120)
    yazi(d, (760, y + 120), f"Tarih: {r.randint(1, 28):02d}.10.2026", 22)
    return im, g


def kargo(n):
    im = Image.new("RGB", (1500, 1000), "white"); d = ImageDraw.Draw(im); g = {}
    d.rectangle((20, 20, 1480, 980), outline="#111111", width=4)
    yazi(d, (60, 50), "ÖRNEK KARGO", 44, True)
    yazi(d, (60, 115), f"Gönderi No: {r.randint(10**11, 10**12 - 1)}", 24)
    for k in range(70):
        x = 900 + k * 7; d.rectangle((x, 60, x + r.choice([2, 3, 5]), 160), fill="black")
    d.line((40, 200, 1460, 200), fill="#111111", width=3)
    yazi(d, (60, 230), "ALICI", 28, True)
    ad = r.choice(ADLAR); ilce, il = r.choice(ILCE)
    g["ad"] = yazi(d, (60, 280), ad, 40, True)
    yazi(d, (60, 345), f"{r.choice(SOKAK)} No:{r.randint(1, 90)} Daire:{r.randint(1, 20)}", 30)
    yazi(d, (60, 395), f"{ilce} / {il}", 30)
    yazi(d, (60, 460), "Tel:", 30)
    g["telefon"] = yazi(d, (140, 460), tel(), 30)
    d.line((40, 540, 1460, 540), fill="#111111", width=3)
    yazi(d, (60, 570), "GÖNDEREN", 24, True)
    yazi(d, (60, 615), "Örnek Ticaret A.Ş.  ·  Ümraniye / İstanbul", 26)
    yazi(d, (60, 660), "Tel: 0 216 555 00 00", 26)
    yazi(d, (60, 760), f"Desi: {r.randint(1, 30)}   Ödeme: Gönderici   Parça: 1/1", 26)
    return im, g


def olcekle(im, g, uzun):
    k = uzun / max(im.size)
    im2 = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    return im2, {a: [v * k for v in b] for a, b in g.items()}


def telefon_fotosu(im, g):
    """Koyu masa uzerinde hafif egik, perspektifli, golgeli, bulanik telefon fotografi benzetimi."""
    W, H = (1568, 1176) if im.width > im.height else (1176, 1568)
    zemin = Image.new("RGB", (W, H), (58, 52, 47))
    k = min(W * 0.82 / im.width, H * 0.86 / im.height)
    w, h = round(im.width * k), round(im.height * k)
    kag = im.resize((w, h), Image.LANCZOS)
    # dort koseyi rastgele oynat (perspektif), sonra kucuk donme
    ox, oy = (W - w) / 2, (H - h) / 2
    j = lambda: r.uniform(-0.035, 0.035) * w
    hedef = [(ox + j(), oy + j()), (ox + w + j(), oy + j()), (ox + w + j(), oy + h + j()), (ox + j(), oy + h + j())]
    a = math.radians(r.uniform(-4, 4)); cx, cy = W / 2, H / 2
    hedef = [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a),
              cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in hedef]
    kaynak = [(0, 0), (w, 0), (w, h), (0, h)]
    kats = _perspektif(hedef, kaynak)
    duz = kag.transform((W, H), Image.PERSPECTIVE, kats, Image.BICUBIC, fillcolor=(58, 52, 47))
    maske = Image.new("L", (w, h), 255).transform((W, H), Image.PERSPECTIVE, kats, Image.BICUBIC)
    zemin.paste(duz, (0, 0), maske)
    # golge: bir koseden yumusak karartma
    gol = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(gol)
    gd.ellipse((-W * 0.4, H * 0.45, W * 0.7, H * 1.6), fill=r.randint(50, 90))
    gol = gol.filter(ImageFilter.GaussianBlur(120))
    zemin = Image.composite(Image.new("RGB", (W, H), "black"), zemin, gol)
    zemin = zemin.filter(ImageFilter.GaussianBlur(r.uniform(0.6, 1.3)))
    # kutulari ayni donusumle tasi: kose noktalarini ileri donusumle
    ileri = _perspektif(kaynak, hedef)
    def tasi(x, y):
        x, y = x * k, y * k
        a_, b_, c_, d_, e_, f_, g_, h_ = ileri
        z = g_ * x + h_ * y + 1
        return (a_ * x + b_ * y + c_) / z, (d_ * x + e_ * y + f_) / z
    g2 = {}
    for ad, (x0, y0, x1, y1) in g.items():
        ps = [tasi(x0, y0), tasi(x1, y0), tasi(x1, y1), tasi(x0, y1)]
        g2[ad] = [min(p[0] for p in ps), min(p[1] for p in ps), max(p[0] for p in ps), max(p[1] for p in ps)]
    return zemin, g2


def _perspektif(hedef, kaynak):
    """PIL PERSPECTIVE katsayilari: hedef noktalar -> kaynak noktalar."""
    import numpy as np
    A, B = [], []
    for (x, y), (u, v) in zip(hedef, kaynak):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return list(np.linalg.solve(np.array(A, float), np.array(B, float)))


if __name__ == "__main__":
    CIKTI.mkdir(exist_ok=True)
    gercek = {}
    for sablon, fn in (("fatura", fatura), ("form", form), ("kargo", kargo)):
        for n in range(1, 11):
            im, g = fn(n)
            for kosul in ("temiz", "kucuk", "telefon"):
                if kosul == "telefon":
                    im2, g2 = telefon_fotosu(im, g)
                else:
                    im2, g2 = olcekle(im, g, 1568 if kosul == "temiz" else 640)
                ad = f"{sablon}_{n:02d}_{kosul}.jpg"
                im2.save(CIKTI / ad, "JPEG", quality=90)
                W, H = im2.size
                gercek[ad] = {"sablon": sablon, "kosul": kosul, "boyut": [W, H],
                              "alanlar": {a: {"left": b[0] / W, "top": b[1] / H, "right": b[2] / W,
                                              "bottom": b[3] / H} for a, b in g2.items()}}
    (CIKTI / "gercek.json").write_text(json.dumps(gercek, ensure_ascii=False, indent=1))
    print(len(gercek), "görüntü")
