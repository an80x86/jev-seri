"""Karsilastirma: Mac'in yerlesik metin tanimasi (Apple Vision, yerel, ucretsiz) + duzenli ifade.

TC, telefon ve IBAN icin desenle eslesen metnin kendi kutusu alinir; imza, ad ve toplam
icin desen yok, bu yontem onlari bulamaz. analiz.py ile ayni bicimde yazar.
  python3 ocr_bazal.py  ->  olcum/ocr.json
"""
import json
import pathlib
import re
import time

import Quartz
import Vision
from Foundation import NSURL

KOK = pathlib.Path(__file__).resolve().parent
GERCEK = json.loads((KOK / "belgeler" / "gercek.json").read_text())
DESEN = {"tc": r"(?<!\d)[1-9]\d{10}(?!\d)",
         "telefon": r"0 ?5\d{2} ?\d{3} ?\d{2} ?\d{2}",
         "iban": r"TR\d{2}(?: ?\d{4}){5} ?\d{2}"}


def oku(yol):
    istek = Vision.VNRecognizeTextRequest.alloc().init()
    istek.setRecognitionLanguages_(["tr-TR", "en-US"])
    istek.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    isleyici = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(yol)), None)
    isleyici.performRequests_error_([istek], None)
    return [g.topCandidates_(1)[0] for g in istek.results()]


def kutu(aday, bas, son):
    """Eslesen alt dizenin kutusu; Vision sol-alt koseli, 0-1 araliginda verir."""
    k, _ = aday.boundingBoxForRange_error_((bas, son - bas), None)
    b = k.boundingBox()
    return {"left": b.origin.x, "right": b.origin.x + b.size.width,
            "top": 1 - b.origin.y - b.size.height, "bottom": 1 - b.origin.y}


if __name__ == "__main__":
    sonuc = []
    for ad in sorted(GERCEK):
        bas = time.perf_counter()
        adaylar = oku(KOK / "belgeler" / ad)
        ms = (time.perf_counter() - bas) * 1000
        s = {"ad": ad, "ms": round(ms), "token": 0, "alanlar": {}}
        for alan, desen in DESEN.items():
            bulunan = None
            for a in adaylar:
                m = re.search(desen, a.string())
                if m:
                    bulunan = kutu(a, m.start(), m.end()); break
            s["alanlar"][alan] = ({"kutu": bulunan, "guven": 1.0, "var": 1.0} if bulunan else
                                  {"kutu": {"left": 0, "right": 0, "top": 0, "bottom": 0}, "guven": 0.0, "var": 0.0})
        sonuc.append(s)
    (KOK / "olcum" / "ocr.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(len(sonuc), "görüntü")
