"""Belgenin onerdigi "yakindan bak": ilk kutunun cevresini kirp, kirpintida ayni Box'i tekrar sor.

Ilk tur sonuclari olcum/box_en_1_*.json'dan okunur (yalnizca belgede olan alanlar).
Kirpinti: ilk kutu her yandan kendi genisligi/yuksekligi kadar buyutulur (en az %15),
en uzun kenari 1000 px olacak sekilde buyutulur. Ikinci kutu tam goruntuye geri cevrilir.
  python3 olc_yakin.py  ->  olcum/yakin_en_1.json
"""
import concurrent.futures as cf
import io
import json
import os
import pathlib
import time

from dotenv import load_dotenv
from PIL import Image as P
from typesafe_sdk import Box, Image, TypeSafeClient

from olc_box import HEDEF

KOK = pathlib.Path(__file__).resolve().parent
load_dotenv(KOK.parents[1] / ".env")
jev = TypeSafeClient(api_key=os.environ["JEV_KEY"])
H = {"TypeSafe-Danger-Zone-Images": "true"}
GERCEK = json.loads((KOK / "belgeler" / "gercek.json").read_text())
ILK = json.loads((KOK / "olcum" / "box_en_1_jev-1.14.0.json").read_text())


def bolge(k):
    w, h = k["right"] - k["left"], k["bottom"] - k["top"]
    dx, dy = max(w, 0.15), max(h, 0.15)
    return {"left": max(0, k["left"] - dx), "right": min(1, k["right"] + dx),
            "top": max(0, k["top"] - dy), "bottom": min(1, k["bottom"] + dy)}


def olc(is_):
    ad, alan, k = is_
    im = P.open(KOK / "belgeler" / ad).convert("RGB"); W, Hh = im.size
    b = bolge(k)
    kirp = im.crop((round(b["left"] * W), round(b["top"] * Hh), round(b["right"] * W), round(b["bottom"] * Hh)))
    s = 1000 / max(kirp.size)
    kirp = kirp.resize((max(280, round(kirp.width * s)), max(280, round(kirp.height * s))), P.LANCZOS)
    tampon = io.BytesIO(); kirp.save(tampon, "JPEG", quality=92)
    tarif = HEDEF["en"][alan].replace("`belge`", "`kesit`")
    for deneme in range(4):
        try:
            c = jev.system_one(state={"kesit": Image(tampon.getvalue())},
                               questions={"k": Box(instructions=tarif)}, model="jev-1.14.0", extra_headers=H)
            break
        except Exception:
            time.sleep(2 + 3 * deneme)
    else:
        return None
    k2 = c.answers["k"].box; bw, bh = b["right"] - b["left"], b["bottom"] - b["top"]
    tam = {"left": b["left"] + k2.left * bw, "right": b["left"] + k2.right * bw,
           "top": b["top"] + k2.top * bh, "bottom": b["top"] + k2.bottom * bh}
    return {"ad": ad, "alan": alan, "kutu": tam, "guven": c.answers["k"].confidence,
            "token": c.usage.input_tokens}


if __name__ == "__main__":
    isler = [(s["ad"], a, v["kutu"]) for s in ILK for a, v in s["alanlar"].items()
             if a in GERCEK[s["ad"]]["alanlar"]]
    with cf.ThreadPoolExecutor(6) as h:
        sonuc = [x for x in h.map(olc, isler) if x]
    # analiz.py ile ayni bicim: goruntu basina alanlar
    gr = {}
    for x in sonuc:
        gr.setdefault(x["ad"], {"ad": x["ad"], "ms": 0, "token": 0, "alanlar": {}})
        gr[x["ad"]]["alanlar"][x["alan"]] = {"kutu": x["kutu"], "guven": x["guven"], "var": 1.0}
        gr[x["ad"]]["token"] += x["token"]
    (KOK / "olcum" / "yakin_en_1.json").write_text(json.dumps(list(gr.values()), ensure_ascii=False, indent=1))
    print(len(sonuc), "/", len(isler), "alan")
