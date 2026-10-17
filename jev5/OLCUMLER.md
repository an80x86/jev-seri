# jev5 ölçümleri — Jev 1.14: görüntü, Box, uzun bağlam

Senaryodaki her sayı burada ölçüldü. Anlatımda bunların dışında bir rakam geçmez.
Ölçüm tarihi: 2026-10-17. Model `jev-1.14.0` (`jev-preview`), SDK `typesafe-sdk` 0.7.5.
Toplam ölçüm maliyeti: kayıtlı 20,98 milyon token ≈ 0,88 $ (ilk, ayarı yanlış uzun bağlam
denemesi kayda girmedi; hepsi birlikte ≈ 1 $).

## 0. Duyuru ve belge ne diyor

Duyuru (x.com/typesafeai, 15.10.2026): Jev 1.14; görüntü, yeni kutu tipi (Box), daha uzun
bağlam; "deneme özellikleri, üretime hazır değil".
Belgeler (docs.typesafe.ai: images, primitives/box, models, sdk/python/changelog):
- Görüntü ve Box "Dreamer-ready": üretim için hazır değil, format ve doğruluk değişebilir.
  Her istekte `TypeSafe-Danger-Zone-Images: true` başlığı şart.
- Box'in "bulunamadı" cevabı yok: olmayan bir şey sorulsa da dört kenar döner. Belge
  yanına bir Noul ("var mı?") koymayı öneriyor.
- Box güveni için "önerilen eşik yok, kendi görüntülerinizde ayarlayın".
- Görüntü sınırları: PNG/JPEG, kenar 280–1568 px; dışındaki reddedilir, küçültülmez.
- Görüntü token'ı için "tahmin rehberi yakında".
- Uzun bağlam: `TypeSafe-Danger-Zone-Long-Context: true` ile 262 bin token (normalde
  istek başına 64 bin, soru başına 32 bin); "daha yavaş ve daha az isabetli".
- Belge kendi içinde tutarsız: Models sayfasındaki tabloda Jev 1.14 girdisi hâlâ "Text";
  System One sayfası "görüntü desteklenmiyor (henüz)" diyor; Images sayfası "1.13 ve 1.14
  ikisi de görüntü kabul eder" diyor. Duman testinde 1.13 de görüntüyü kabul etti.

## 1. Düzenek: kişisel veriyi karartmak

İş sorusu: belge fotoğrafındaki kişisel veriyi (TC kimlik no, telefon, IBAN, ad, imza) ve
toplam tutarı Jev'in Box'ıyla bulup karartırsam, değerin tamamı gizleniyor mu?
- `belge_uret.py`: 3 şablon (fatura, başvuru formu, kargo etiketi) × 10 uydurma belge.
  Her alanın kutusu piksel olarak biliniyor. TC ve IBAN'lar bilerek geçersiz, isimler uydurma.
- 3 koşul: temiz (uzun kenar 1568 px), küçük (640 px), telefon fotoğrafı benzetimi
  (perspektif, ±4° dönme, gölge, bulanıklık, koyu zemin). Toplam 90 görüntü.
- Belgede olan 360 alan + olmayan 180 alan (ör. kargo etiketinde IBAN). Her görüntü tek
  istek: her alan için bir Box + bir Noul ("içeriyor mu?"). `olc_box.py`.
- Ölçüt: **tam karartma** = gerçek kutunun ≥ %99'u tahmin kutusunun içinde (değer tamamen
  gizlenir). Ayrıca IoU ve "karartılan alan / gerçek alan".

## 2. Box: ilk sonuç (İngilizce talimat, 1. çalıştırma)

| Alan | n | Tam karartma | IoU ort | Güven ort |
|---|---|---|---|---|
| ad | 90 | 60 | 0,13 | 0,36 |
| tc | 60 | 41 | 0,07 | 0,47 |
| telefon | 90 | 69 | 0,21 | 0,63 |
| iban | 30 | 13 | 0,28 | 0,88 |
| toplam | 30 | 1 | 0,16 | 0,38 |
| imza | 60 | 6 | 0,67 (55/60 IoU≥0,5) | 0,85 |
| **hepsi** | 360 | **190** (%53) | 0,24 | 0,57 |

- Kutular doğru bölgeyi buluyor ama gevşek: etiketi ("T.C. Kimlik No:") içine alıyor, komşu
  satıra taşıyor, bazen bir satır kayıyor (toplam yerine KDV satırı). Karartılan alan
  gerçeğin ortanca 4,9 katı.
- İmza: kutu imzaya iyi oturuyor (IoU 0,67) ama tam sığdırıyor; uçtaki çizgiler dışarıda
  kalıyor, 60'ın 6'sı tam karartma.
- Koşula göre tam karartma: temiz 73/120, küçük 60/120, telefon 57/120.
- Türkçe talimatla: 212/360 tam karartma (İngilizce 190). Ama Türkçe Noul 90 telefonun
  56'sına "yok" dedi; İngilizce 0. → Talimatları İngilizce yazmak daha güvenli
  (belge de "İngilizce birincil dil" diyor).
- Hız ve token: görüntü başına (12 soru) ortanca ≈ 430 ms, ≈ 3.900 token.

## 3. Tekrarlanabilirlik

Aynı 90 görüntü, aynı sorular, ikinci çalıştırma (`box_en_2`):
- 540 cevabın 500'ü farklı (kenar ya da güven).
- Kenar farkı: ortanca 0,01; %10'u 0,24'ten fazla; en büyüğü 0,72.
- Tam karartma kararı 360 alanın 46'sında değişti (%13). Toplam yine benzer: 194/360.

## 4. Güven ne söylüyor

| Box güveni | n | Tam karartma | IoU ort |
|---|---|---|---|
| < 0,3 | 75 | 42 | 0,04 |
| 0,3–0,6 | 116 | 69 | 0,13 |
| 0,6–0,8 | 57 | 31 | 0,26 |
| ≥ 0,8 | 112 | 48 | 0,49 |

Güven IoU'yu izliyor ama karartmayı öngörmüyor: güveni yüksek kutular daha dar, kenarları
daha sık kaçırıyor.

## 5. Pay eklemek ve yakınlaşmak

Tek adım (360 alan):

| Pay (görüntünün oranı) | Tam karartma | Sızan | Karartılan / gerçek (ortanca) |
|---|---|---|---|
| 0 | 190 | 170 | 4,9× |
| 0,01 | 272 | 88 | 7,6× |
| 0,02 | 298 | 62 | 11,0× |
| 0,03 | 319 | 41 | 14,5× |
| 0,05 | 338 | 22 | 23,1× |
| 0,10 | 345 | 15 | 48,2× |

Belgenin önerdiği "yakından bak" (`olc_yakin.py`): ilk kutunun çevresi kırpılıp büyütülür,
aynı Box kırpıntıda tekrar sorulur (2. istek).
- IoU 0,24 → 0,48; ama kutu daralır, pay yoksa tam karartma 105/360.
- Yakınlaş + 0,02 pay: 319/360, karartılan 6,4× (tek adımda aynı 319 için 14,5×).
- Yakınlaş + 0,05 pay: 342/360, 16,1×.

## 6. Karşılaştırma: Mac'in kendi OCR'ı + düzenli ifade

`ocr_bazal.py`: Apple Vision (yerel, ücretsiz, Türkçe destekli) ile metni oku, TC/telefon/IBAN
desenine uyan metnin kendi kutusunu al. Ad, toplam ve imza için desen yok; bu yöntem onları
bulamaz. Görüntü başına ≈ 133 ms.

TC + telefon + IBAN (180 alan):

| Yöntem | Tam karartma | Karartılan / gerçek (ortanca) |
|---|---|---|
| OCR + desen, pay 0 | 161 | 1,5× |
| OCR + desen, pay 0,005 | 172 | 2,7× |
| Jev tek adım, pay 0 | 123 | 6,4× |
| Jev tek adım, pay 0,05 | 172 | 32,1× |
| Jev tek adım, pay 0,10 | 177 | 76,7× |
| Jev yakınlaş, pay 0,02 | 173 | 7,6× |

Koşula göre (OCR %0,5 / Jev tek %5 / Jev yakın %2): temiz 60/60 · 60/60 · 58/60;
küçük 52/60 · 52/60 · 55/60; telefon 60/60 · 60/60 · 60/60.
OCR'ın kaçırdıkları: 640 px'lik 7 formda TC satırını hiç okumadı, 1 faturada telefon.

İmza (60): OCR bulamaz. Jev yakınlaş + 0,01 pay 59/60 (1,4×), + 0,02 pay **60/60 (1,9×)**;
tek adım + 0,02 pay 53/60.

Sonuç: metin olan kişisel veride basit OCR daha az alan karartarak aynı sonucu veriyor.
Jev'in yeri metin olmayan şey: imza (benzer şekilde kaşe, fotoğraf).

## 7. Olmayan alan

- Box her zaman kutu döndü (180/180). Olmayan alanlarda güven ort 0,05 (en çok 0,24).
- Box güveniyle ayırmak: eşik 0,25 → olmayana kutu 0/180 ama olan 50/360 atlanır;
  eşik 0,1 → olmayana kutu 18/180, olan 3/360 atlanır.
- Noul (İngilizce): olmayan 180'in hiçbirine "var", olan 360'ın hiçbirine "yok" demedi.
  Belgenin önerisi tutuyor: varlığı Noul'a sor, kutuyu ancak o "var" derse kullan.

## 8. Görüntü token'ı ve maliyet

`olc_token.py`, aynı fatura farklı boyutlarda, tek Noul (metin tabanı 284 token çıkarıldı):

| Boyut | Görüntü token'ı | Ortanca süre |
|---|---|---|
| 280×280 | 236 | 279 ms |
| 452×640 | 814 | 276 ms |
| 640×905 | 1.551 | 302 ms |
| 800×1131 | 2.411 | 412 ms |
| 1109×1568 | 4.514 | 403 ms |
| 1568×1568 | 6.304 | 440 ms |

Kabaca token ≈ piksel / 390. Fiyat 0,042 $ / milyon token: tam sayfa ≈ 0,0002 $
(1.000 sayfa ≈ 0,19 $). Aynı görüntüde token sayısı ±3 oynuyor.

## 9. Uzun bağlam

`olc_baglam.py`: uydurma sözleşme maddeleri (başka "gün" süreleri dahil) + tek fesih maddesi +
bir tuzak (yenilememe bildirimi, farklı gün). Choice: 15/30/45/60/90. 5 konum × 4 değer = 20.
- Sınır gerçek: uzun bağlam başlığı olmadan ≈ 40 bin token'lık istek (104 bin karakter)
  `400 max_tokens_exceeded`; başlıkla ≈ 317 bin token'lık istek (825 bin karakter, 2,6 kr/token
  ile tahmin) yine `max_tokens_exceeded`. Hata cevabı token sayısını vermiyor.
- Türkçe sözleşme metninde ≈ 2,6 karakter / token.

| Token | Doğru | Ortanca süre | Güven ort |
|---|---|---|---|
| 8.562 | 20/20 | 326 ms | 0,99 |
| 28.459 | 20/20 | 507 ms | 0,99 |
| 60.652 | 20/20 | 906 ms | 0,99 |
| 121.401 | 20/20 | 1.755 ms | 0,99 |
| 182.111 | 20/20 | 2.653 ms | 0,97 |
| 243.672 | 20/20 | 3.845 ms | 0,98 |

Tuzağa hiç düşmedi. 243 bin token'lık soru ≈ 0,01 $.

Zor sürüm (`olc_baglam_ek.py`): fesih maddesi X gün der, metnin %90'ındaki "Ek Protokol"
onu Y'ye çevirir; doğru cevap Y.

| Token | Doğru (Y) | Eski süre (X) | Tuzak |
|---|---|---|---|
| 8.621 | 19/20 | 1 | 0 |
| 60.727 | 17/20 | 3 | 0 |
| 242.715 | 16/20 | 4 | 0 |

- Yanlışların hepsi, asıl madde belgenin en sonunda (protokolden sonra) olduğunda: metinde
  en son geçen eski süreyi seçti. O konumda 8 bin token'da 1/4, 240 bin token'da 4/4 yanlış.
- Yanlışların güveni 0,36–0,51. Eşik 0,55: 51/60 otomatik ve hepsi doğru; 9 soru insana
  (içinde 1 doğru). Belgenin "uzun bağlam daha az isabetli" uyarısı bu sürümde görünüyor.

## Sınırlar

- Belgeler uydurma ve bilgisayarda üretildi; telefon fotoğrafı benzetim. Gerçek taranmış
  belge, el yazısı form ya da buruşuk kâğıt ölçülmedi.
- Tek model sürümü (önizleme); belge "doğruluk değişecek" diyor.
- Uzun bağlamda tek tür soru (tek madde + tuzak, ek protokol).
- Ham veri `olcum/`, görüntüler `belgeler/`.
