"""Uzun baglam: uzun bir Turkce sozlesmeye tek bir fesih maddesi saklanir, Jev'e sorulur.

Samanlik: rastgele sozlesme maddeleri (odeme vadesi, teslim suresi gibi baska "gun"ler dahil).
Igne: "Taraflardan biri sozlesmeyi ... gun once yazili bildirimle feshedebilir."
Boylar (yaklasik token): 4k, 16k, 30k, 60k, 120k, 250k. 32k ustu uzun baglam basligi ister.
Her boyda 5 konum x 4 deger = 20 soru.
  python3 olc_baglam.py  ->  olcum/baglam.json
"""
import concurrent.futures as cf
import json
import os
import pathlib
import random
import time

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

KOK = pathlib.Path(__file__).resolve().parent
load_dotenv(KOK.parents[1] / ".env")
jev = TypeSafeClient(api_key=os.environ["JEV_KEY"], timeout=300)
UZUN = {"TypeSafe-Danger-Zone-Long-Context": "true"}
r = random.Random(114)
r2 = random.Random(7)
SORU = {"fesih": Choice(
    instructions="Sözleşmeye göre taraflardan biri sözleşmeyi feshetmek için kaç gün önceden yazılı bildirimde bulunmalı?",
    criteria={"15": "15 gün", "30": "30 gün", "45": "45 gün", "60": "60 gün", "90": "90 gün"})}
KONU = ["Teslimat", "Ödeme", "Garanti", "Gizlilik", "Bakım", "Eğitim", "Sigorta", "Raporlama", "Denetim",
        "Fiyat güncelleme", "Alt yüklenici", "Fikri mülkiyet", "Mücbir sebep", "Uyuşmazlık", "Kalite"]


def madde(no):
    k = r.choice(KONU)
    secenek = [
        f"Madde {no} – {k}: Yüklenici, siparişin onaylanmasından itibaren {r.choice([7, 10, 14, 20, 21, 30])} gün içinde teslimatı {r.choice(['İstanbul', 'Ankara', 'İzmir', 'Bursa'])} deposunda yapar.",
        f"Madde {no} – {k}: Fatura bedeli, faturanın tebliğinden itibaren {r.choice([15, 30, 45, 60, 90])} gün içinde Alıcı tarafından ödenir; gecikmede aylık %{r.choice([1, 2, 3])} gecikme faizi uygulanır.",
        f"Madde {no} – {k}: Ürünler, teslim tarihinden itibaren {r.choice([12, 18, 24, 36])} ay süreyle üretim hatalarına karşı garantilidir.",
        f"Madde {no} – {k}: Taraflar, bu sözleşme kapsamında öğrendikleri ticari bilgileri sözleşme bitiminden sonra {r.choice([2, 3, 5])} yıl boyunca gizli tutar.",
        f"Madde {no} – {k}: Yüklenici, sistemlerin periyodik bakımını yılda {r.choice([2, 4, 6, 12])} kez yapar ve her bakımdan sonra {r.choice([3, 5, 7])} iş günü içinde rapor sunar.",
        f"Madde {no} – {k}: Arıza bildirimleri {r.choice([4, 8, 24, 48])} saat içinde yanıtlanır; çözüm süresi {r.choice([2, 3, 5, 10])} iş gününü geçemez.",
        f"Madde {no} – {k}: Birim fiyatlar her yıl Ocak ayında TÜFE oranında güncellenir; güncelleme {r.choice([15, 30, 45])} gün önceden bildirilir.",
        f"Madde {no} – {k}: Uyuşmazlık halinde önce {r.choice([15, 30, 45, 60])} gün süreyle arabuluculuk denenir; sonuç alınamazsa {r.choice(['İstanbul', 'Ankara', 'İzmir'])} mahkemeleri yetkilidir.",
        f"Madde {no} – {k}: Yüklenici, personeline yılda en az {r.choice([8, 16, 24, 40])} saat iş güvenliği eğitimi verir ve kayıtlarını {r.choice([2, 5, 10])} yıl saklar.",
    ]
    return r.choice(secenek)


def samanlik(hedef_kr):
    m, no, top = [], 1, 0
    while top < hedef_kr:
        s = madde(no); m.append(s); top += len(s) + 1; no += 1
    return m


IGNE = "Taraflardan biri, bu sözleşmeyi {} gün önceden karşı tarafa yazılı bildirimde bulunmak kaydıyla, herhangi bir gerekçe göstermeksizin feshedebilir."
KR_TOKEN = 2.6          # olculdu: Turkce metinde ~2,6 karakter/token (usage.input_tokens)
BOYLAR = [8_000, 28_000, 60_000, 120_000, 180_000, 240_000]


def olc(is_):
    boy, konum, gun, maddeler = is_
    i = int(len(maddeler) * konum)
    # Sasirtici: yenilememe bildirimi de "gun once yazili bildirim" ama fesih degil; farkli bir deger.
    tuzak = r2.choice([g for g in (15, 30, 45, 60, 90) if g != gun])
    j = int(len(maddeler) * (1 - konum))
    metin = list(maddeler)
    metin.insert(j, f"Madde – Yenileme: Sözleşme kendiliğinden birer yıl uzar; uzamasını istemeyen taraf bitiş tarihinden {tuzak} gün önce yazılı bildirimde bulunur.")
    metin.insert(i, f"Madde – Fesih: " + IGNE.format(gun))
    durum = "SATIŞ VE HİZMET SÖZLEŞMESİ\n\n" + "\n".join(metin)
    basliklar = UZUN if boy > 30_000 else {}
    r2_ = None
    for deneme in range(4):
        try:
            bas = time.perf_counter()
            c = jev.system_one(state=durum, questions=SORU, model="jev-1.14.0", extra_headers=basliklar)
            ms = (time.perf_counter() - bas) * 1000
            a = c.answers["fesih"]
            return {"boy": boy, "konum": konum, "gun": gun, "tuzak": tuzak, "cevap": a.choice, "guven": a.confidence,
                    "dogru": a.choice == str(gun), "token": c.usage.input_tokens, "ms": round(ms)}
        except Exception as e:
            hata = f"{type(e).__name__}: {str(e)[:160]}"; time.sleep(3 + 5 * deneme)
    return {"boy": boy, "konum": konum, "gun": gun, "hata": hata}


if __name__ == "__main__":
    isler = []
    for boy in BOYLAR:
        maddeler = samanlik(int(boy * KR_TOKEN))
        for konum in (0.02, 0.25, 0.5, 0.75, 0.98):
            for gun in (15, 30, 60, 90):
                isler.append((boy, konum, gun, maddeler))
    with cf.ThreadPoolExecutor(4) as h:
        sonuc = list(h.map(olc, isler))
    # baslik olmadan 60k: belgede soylenen sinir gercekten var mi?
    m = samanlik(int(40_000 * KR_TOKEN))
    try:
        jev.system_one(state="\n".join(m), questions=SORU, model="jev-1.14.0")
        siniri = "başlıksız ~40k: kabul edildi"
    except Exception as e:
        siniri = f"başlıksız ~40k: {type(e).__name__}: {str(e)[:200]}"
    (KOK / "olcum" / "baglam.json").write_text(json.dumps({"sonuc": sonuc, "sinir": siniri}, ensure_ascii=False, indent=1))
    print(siniri)
    for boy in BOYLAR:
        g = [s for s in sonuc if s["boy"] == boy and "hata" in s]
        o = [s for s in sonuc if s["boy"] == boy and "hata" not in s]
        if o:
            print(f"{boy:>7}: doğru {sum(s['dogru'] for s in o)}/{len(o)}  token ort {sum(s['token'] for s in o) / len(o):,.0f}  "
                  f"ms ortanca {sorted(s['ms'] for s in o)[len(o) // 2]}  güven ort {sum(s['guven'] for s in o) / len(o):.2f}  hata {len(g)}")
        else:
            print(boy, "hepsi hata:", g[0]["hata"] if g else "")
