# Jev serisi: kodlar ve ölçümler

YouTube'daki **Güncel Gündem: Jev** videolarının kodları. [TypeSafe Jev](https://docs.typesafe.ai)
System One modeliyle yapılan her deney ölçülüyor; sayılar `OLCUMLER.md` dosyalarında.

| Video | Bu depoda |
|---|---|
| [Jev'e Göz Geldi: Kişisel Veriyi Karartabilir mi?](https://youtu.be/iIguGiD1ruc) (Jev 1.14: görüntü, Box, uzun bağlam) | `jev5/` |

## jev5

```
karart.py           Videodaki demo: metni Mac'in metin tanıması (Apple Vision) + desen bulur,
                    imzayı Jev bulur ("var mı" Noul + Box + yakından ikinci soru), %2 pay ile karartır
belge_uret.py       30 uydurma belge (fatura, form, kargo etiketi) x 3 hâl = 90 görüntü + gerçek kutular
olc_box.py          Box + Noul ölçümü (her alan, olan ve olmayan)  ->  olcum/box_*.json
olc_yakin.py        "Yakından bak": ilk kutunun çevresini kırpıp tekrar sor  ->  olcum/yakin_en_1.json
ocr_bazal.py        Karşılaştırma: Apple Vision + düzenli ifade  ->  olcum/ocr.json
analiz.py           Tam karartma, IoU, pay ekleme;  python3 analiz.py olcum/box_en_1_jev-1.14.0.json 0.02
olc_token.py        Görüntü boyutuna göre token
olc_baglam.py       Uzun bağlam: tek fesih maddesi + tuzak, 8k–244k token
olc_baglam_ek.py    Uzun bağlam, zor sürüm: ek protokol süreyi değiştiriyor
OLCUMLER.md         Bütün sonuçlar
```

Belgelerdeki bütün isimler, adresler, TC numaraları (bilerek geçersiz) ve IBAN'lar uydurmadır.

Çalıştırma: `pip install -r requirements.txt`, proje kökünde `.env` dosyasına `JEV_KEY=...` yazın
(anahtar hiçbir yere yazdırılmaz). Görüntü ve Box için Jev 1.14 (`jev-1.14.0` ya da `jev-preview`)
ve her istekte `TypeSafe-Danger-Zone-Images: true` başlığı gerekir; ikisi de TypeSafe'e göre
"Dreamer-ready", yani önizleme. `karart.py` ve `ocr_bazal.py` macOS ister (Apple Vision).

Kaynaklar: [Images](https://docs.typesafe.ai/images), [Box](https://docs.typesafe.ai/primitives/box),
[Models / uzun bağlam](https://docs.typesafe.ai/models).
