"""Uzun baglam, zor surum: fesih suresi bir ek protokolle degistirilir; dogru cevap yeni sure.

Ana madde X gun der; belgenin sonlarina dogru "Ek Protokol" X'i Y'ye cevirir. Ayrica yenilememe tuzagi.
Boylar 8k / 60k / 240k token, her boyda 20 soru (ana madde 5 konum x 4 deger).
  python3 olc_baglam_ek.py  ->  olcum/baglam_ek.json
"""
import concurrent.futures as cf, json, random, time
import olc_baglam as b

r = random.Random(21)


def olc(is_):
    boy, konum, eski, yeni, tuzak, maddeler = is_
    m = list(maddeler)
    m.insert(int(len(m) * 0.9), f"EK PROTOKOL 1: Taraflar, fesih maddesinde yer alan {eski} günlük bildirim süresini, "
                                f"bu protokolün imza tarihinden itibaren geçerli olmak üzere {yeni} gün olarak değiştirmiştir.")
    m.insert(int(len(m) * (1 - konum)), f"Madde – Yenileme: Sözleşme kendiliğinden birer yıl uzar; uzamasını istemeyen taraf bitiş tarihinden {tuzak} gün önce yazılı bildirimde bulunur.")
    m.insert(int(len(m) * konum), "Madde – Fesih: " + b.IGNE.format(eski))
    durum = "SATIŞ VE HİZMET SÖZLEŞMESİ\n\n" + "\n".join(m)
    for deneme in range(4):
        try:
            bas = time.perf_counter()
            c = b.jev.system_one(state=durum, questions=b.SORU, model="jev-1.14.0",
                                 extra_headers=b.UZUN if boy > 30_000 else {})
            a = c.answers["fesih"]
            return {"boy": boy, "konum": konum, "eski": eski, "yeni": yeni, "tuzak": tuzak, "cevap": a.choice,
                    "guven": a.confidence, "olasilik": a.model_dump().get("probabilities"),
                    "dogru": a.choice == str(yeni), "token": c.usage.input_tokens,
                    "ms": round((time.perf_counter() - bas) * 1000)}
        except Exception as e:
            hata = f"{type(e).__name__}: {str(e)[:160]}"; time.sleep(3 + 5 * deneme)
    return {"boy": boy, "hata": hata}


if __name__ == "__main__":
    isler = []
    for boy in (8_000, 60_000, 240_000):
        maddeler = b.samanlik(int(boy * b.KR_TOKEN))
        for konum in (0.02, 0.25, 0.5, 0.75, 0.98):
            for eski in (15, 30, 60, 90):
                yeni = r.choice([g for g in (15, 30, 45, 60, 90) if g != eski])
                tuzak = r.choice([g for g in (15, 30, 45, 60, 90) if g not in (eski, yeni)])
                isler.append((boy, konum, eski, yeni, tuzak, maddeler))
    with cf.ThreadPoolExecutor(4) as h:
        sonuc = list(h.map(olc, isler))
    (b.KOK / "olcum" / "baglam_ek.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
    for boy in (8_000, 60_000, 240_000):
        o = [s for s in sonuc if s["boy"] == boy and "hata" not in s]
        print(f"{boy:>7}: yeni süre (doğru) {sum(s['dogru'] for s in o)}/{len(o)}  eski süre {sum(s['cevap'] == str(s['eski']) for s in o)}  "
              f"tuzak {sum(s['cevap'] == str(s['tuzak']) for s in o)}  güven ort {sum(s['guven'] for s in o) / len(o):.2f}  "
              f"yanlışlarda güven {[round(s['guven'], 2) for s in o if not s['dogru']][:8]}")
