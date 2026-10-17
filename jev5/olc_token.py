"""Goruntu basina token: ayni soru, metin durumu ile goruntu durumu arasindaki fark.

  python3 olc_token.py  ->  olcum/token.json
"""
import io, json, os, pathlib, statistics as st, time
from dotenv import load_dotenv
from PIL import Image as P
from typesafe_sdk import Image, Noul, TypeSafeClient
KOK = pathlib.Path(__file__).resolve().parent
load_dotenv(KOK.parents[1] / ".env")
jev = TypeSafeClient(api_key=os.environ["JEV_KEY"])
H = {"TypeSafe-Danger-Zone-Images": "true"}
Q = {"var": Noul(instructions="Is there a signature in `belge`?")}
kaynak = P.open(KOK / "belgeler" / "fatura_01_temiz.jpg").convert("RGB")      # 1109 x 1568
taban = jev.system_one(state={"belge": "x"}, questions=Q, model="jev-1.14.0").usage.input_tokens
sonuc = {"metin_taban": taban, "olcumler": []}
for w, h in [(280, 280), (280, 396), (452, 640), (640, 905), (800, 1131), (1109, 1568), (1568, 1568)]:
    b = io.BytesIO(); kaynak.resize((w, h)).save(b, "JPEG", quality=90)
    t, ms = [], []
    for _ in range(3):
        bas = time.perf_counter()
        c = jev.system_one(state={"belge": Image(b.getvalue())}, questions=Q, model="jev-1.14.0", extra_headers=H)
        ms.append((time.perf_counter() - bas) * 1000); t.append(c.usage.input_tokens)
    sonuc["olcumler"].append({"boyut": [w, h], "piksel": w * h, "token": t, "goruntu_token": t[0] - taban,
                              "ms_ortanca": round(st.median(ms))})
    print(w, h, t, "görüntü ≈", t[0] - taban, "token", round(st.median(ms)), "ms")
(KOK / "olcum" / "token.json").write_text(json.dumps(sonuc, indent=1))
print("metin tabanı", taban)
