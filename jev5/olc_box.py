"""Box olcumu: 90 belge goruntusu, her alan icin Box + "var mi" Noul.

Belgede olmayan alanlar da sorulur (Box'in "bulunamadi" cevabi yok).
  python3 olc_box.py en 1      # dil, tekrar no -> olcum/box_en_1.json
"""
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import time

from dotenv import load_dotenv
from typesafe_sdk import Box, Image, Noul, TypeSafeClient

KOK = pathlib.Path(__file__).resolve().parent
load_dotenv(KOK.parents[1] / ".env")
jev = TypeSafeClient(api_key=os.environ["JEV_KEY"])
DIL = sys.argv[1] if len(sys.argv) > 1 else "en"
TEKRAR = sys.argv[2] if len(sys.argv) > 2 else "1"
MODEL = os.environ.get("JEV_MODEL", "jev-1.14.0")
H = {"TypeSafe-Danger-Zone-Images": "true"}

HEDEF = {
    "en": {"ad": "the full name of the person (customer, applicant or recipient) in `belge`",
           "tc": "the T.C. Kimlik No value (11-digit Turkish national ID number) in `belge`, not its label",
           "telefon": "the mobile phone number starting with 05 in `belge`, not its label",
           "iban": "the IBAN (starts with TR) in `belge`",
           "imza": "the handwritten signature in `belge`",
           "toplam": "the grand total amount (the GENEL TOPLAM value) in `belge`"},
    "tr": {"ad": "`belge` içindeki kişinin (müşteri, başvuran ya da alıcı) adı soyadı",
           "tc": "`belge` içindeki T.C. Kimlik No değeri (11 haneli), etiketi değil",
           "telefon": "`belge` içindeki 05 ile başlayan cep telefonu numarası, etiketi değil",
           "iban": "`belge` içindeki IBAN (TR ile başlar)",
           "imza": "`belge` içindeki el yazısı imza",
           "toplam": "`belge` içindeki genel toplam tutarı (GENEL TOPLAM değeri)"},
}
VAR = {"en": "Does `belge` contain {}?", "tr": "`belge` şunu içeriyor mu: {}?"}
GERCEK = json.loads((KOK / "belgeler" / "gercek.json").read_text())


def olc(ad):
    q = {}
    for alan, tarif in HEDEF[DIL].items():
        q[f"kutu_{alan}"] = Box(instructions=tarif)
        q[f"var_{alan}"] = Noul(instructions=VAR[DIL].format(tarif))
    img = Image(KOK / "belgeler" / ad)
    for deneme in range(4):
        try:
            bas = time.perf_counter()
            c = jev.system_one(state={"belge": img}, questions=q, model=MODEL, extra_headers=H)
            ms = (time.perf_counter() - bas) * 1000
            break
        except Exception as e:                      # gecici hata: bekle, tekrar dene
            hata = f"{type(e).__name__}: {str(e)[:150]}"
            time.sleep(2 + deneme * 3)
    else:
        return {"ad": ad, "hata": hata}
    s = {"ad": ad, "model": c.model, "ms": round(ms), "token": c.usage.input_tokens, "alanlar": {}}
    for alan in HEDEF[DIL]:
        k, v = c.answers[f"kutu_{alan}"], c.answers[f"var_{alan}"]
        s["alanlar"][alan] = {"kutu": k.box.model_dump(), "guven": k.confidence, "var": v.noul}
    return s


if __name__ == "__main__":
    adlar = sorted(GERCEK)
    with cf.ThreadPoolExecutor(6) as h:
        sonuc = list(h.map(olc, adlar))
    (KOK / "olcum").mkdir(exist_ok=True)
    yol = KOK / "olcum" / f"box_{DIL}_{TEKRAR}_{MODEL}.json"
    yol.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
    hatali = [s["ad"] for s in sonuc if "hata" in s]
    print(yol.name, len(sonuc), "görüntü, hata:", len(hatali), hatali[:3])
