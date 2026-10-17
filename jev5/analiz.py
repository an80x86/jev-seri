"""Box sonuclarini gercek kutularla karsilastirir.

  IoU        : kesisim / birlesim
  kapsama    : gercek kutunun ne kadari tahmin kutusunun icinde (karartma icin onemli olan)
  tam_maske  : kapsama >= 0.99 (degerin tamami kararir)
  python3 analiz.py olcum/box_en_1_jev-1.14.0.json [pay]
"""
import collections
import json
import pathlib
import statistics as st
import sys

KOK = pathlib.Path(__file__).resolve().parent
GERCEK = json.loads((KOK / "belgeler" / "gercek.json").read_text())


def alan(b):
    return max(0, b["right"] - b["left"]) * max(0, b["bottom"] - b["top"])


def kesisim(a, b):
    return alan({"left": max(a["left"], b["left"]), "right": min(a["right"], b["right"]),
                 "top": max(a["top"], b["top"]), "bottom": min(a["bottom"], b["bottom"])})


def pay_ekle(b, pay):
    return {"left": max(0, b["left"] - pay), "right": min(1, b["right"] + pay),
            "top": max(0, b["top"] - pay), "bottom": min(1, b["bottom"] + pay)}


def satirlar(yol, pay=0.0):
    for s in json.loads(pathlib.Path(yol).read_text()):
        g = GERCEK[s["ad"]]
        for a, t in s["alanlar"].items():
            gk = g["alanlar"].get(a)
            k = pay_ekle(t["kutu"], pay) if pay else t["kutu"]
            r = {"ad": s["ad"], "sablon": g["sablon"], "kosul": g["kosul"], "alan": a, "var_mi": gk is not None,
                 "guven": t["guven"], "noul": t["var"], "ms": s["ms"], "token": s["token"],
                 "kutu_alani": alan(k)}
            if gk:
                ks = kesisim(k, gk)
                r.update(iou=ks / (alan(k) + alan(gk) - ks), kapsama=ks / alan(gk),
                         fazla=alan(k) / alan(gk))
            yield r


def ozet(R, anahtar):
    gruplar = collections.defaultdict(list)
    for r in R:
        gruplar[anahtar(r)].append(r)
    for k in sorted(gruplar):
        g = gruplar[k]
        print(f"  {str(k):28} n={len(g):3}  IoU ort {st.mean(r['iou'] for r in g):.2f}  "
              f"IoU>=.5 {sum(r['iou'] >= .5 for r in g):3}/{len(g)}  "
              f"tam maske {sum(r['kapsama'] >= .99 for r in g):3}/{len(g)}  "
              f"kapsama ort {st.mean(r['kapsama'] for r in g):.2f}  güven ort {st.mean(r['guven'] for r in g):.2f}")


if __name__ == "__main__":
    yol = sys.argv[1]; pay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    R = list(satirlar(yol, pay))
    var = [r for r in R if r["var_mi"]]; yok = [r for r in R if not r["var_mi"]]
    print(f"{yol}  pay={pay}  görüntü başına ort {st.mean(r['ms'] for r in R):.0f} ms, "
          f"{st.mean(r['token'] for r in R):.0f} token")
    print("Alana göre:"); ozet(var, lambda r: r["alan"])
    print("Koşula göre:"); ozet(var, lambda r: r["kosul"])
    print("Toplam:"); ozet(var, lambda r: "hepsi")
    if yok: print(f"Olmayan alan: n={len(yok)}  Box güven ort {st.mean(r['guven'] for r in yok):.2f} "
          f"(min {min(r['guven'] for r in yok):.2f}, max {max(r['guven'] for r in yok):.2f})  "
          f"Noul ort {st.mean(r['noul'] for r in yok):.2f}  Noul>=.5: {sum(r['noul'] >= .5 for r in yok)}")
    print(f"Olan alan:   n={len(var)}  Box güven ort {st.mean(r['guven'] for r in var):.2f}  "
          f"Noul ort {st.mean(r['noul'] for r in var):.2f}  Noul<.5: {sum(r['noul'] < .5 for r in var)}")
