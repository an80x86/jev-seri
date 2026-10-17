"""Belge fotografindaki kisisel veriyi karartir: metni OCR bulur, imzayi Jev bulur.
Anahtar .env'den okunur ve hicbir yere yazdirilmaz. Belgeler uydurmadir.
"""
import io, os, re

import Vision
from dotenv import load_dotenv
from Foundation import NSData
from PIL import Image as P, ImageDraw
from typesafe_sdk import Box, Image, Noul, TypeSafeClient

load_dotenv()
jev = TypeSafeClient(api_key=os.environ['JEV_KEY'])
GORUNTU = {'TypeSafe-Danger-Zone-Images': 'true'}       # 1.14: gorsel hala onizleme
DESEN = {'tc': r'(?<!\d)[1-9]\d{10}(?!\d)', 'telefon': r'0 ?5\d\d ?\d{3} ?\d\d ?\d\d',
         'iban': r'TR\d\d(?: ?\d{4}){5} ?\d\d'}


def ocr_bul(foto):
    """Mac'in kendi metin tanimasi + duzenli ifade: metin olan kisisel veri."""
    tampon = io.BytesIO(); foto.save(tampon, 'PNG')
    istek = Vision.VNRecognizeTextRequest.alloc().init()
    istek.setRecognitionLanguages_(['tr-TR'])
    veri = NSData.dataWithBytes_length_(tampon.getvalue(), len(tampon.getvalue()))
    isleyici = Vision.VNImageRequestHandler.alloc().initWithData_options_(veri, None)
    isleyici.performRequests_error_([istek], None)
    bulunan = {}
    for satir in (s.topCandidates_(1)[0] for s in istek.results()):
        for ad, desen in DESEN.items():
            if m := re.search(desen, satir.string()):
                aralik = (m.start(), m.end() - m.start())
                b = satir.boundingBoxForRange_error_(aralik, None)[0].boundingBox()
                bulunan[ad] = (b.origin.x, 1 - b.origin.y - b.size.height,
                               b.origin.x + b.size.width, 1 - b.origin.y)
    return bulunan


def jev_sor(foto, soru):
    """Jev'e once 'var mi' diye sorar; varsa kutuyu dondurur."""
    c = jev.system_one(state={'belge': Image.from_pil(foto)}, model='jev-1.14.0',
                       extra_headers=GORUNTU,
                       questions={'var': Noul(instructions=f'Does `belge` contain {soru}?'),
                                  'kutu': Box(instructions=f'{soru} in `belge`')}).answers
    k = c['kutu'].box
    return c['var'].noul, c['kutu'].confidence, (k.left, k.top, k.right, k.bottom)


def imza_bul(foto):
    """Belgenin onerisi: ilk kutunun cevresini kirpip yakindan bir kez daha sor."""
    var, guven, (l, t, r, b) = jev_sor(foto, 'the handwritten signature')
    if var < 0.5:
        return None
    W, H = foto.size; dx, dy = max(r - l, .15), max(b - t, .15)
    L, T, R, B = max(0, l - dx), max(0, t - dy), min(1, r + dx), min(1, b + dy)
    kirp = foto.crop((L * W, T * H, R * W, B * H))
    kirp = kirp.resize((1000, round(1000 * kirp.height / kirp.width)))
    _, guven, (l, t, r, b) = jev_sor(kirp, 'the handwritten signature')
    print(f'  jev  imza  var mi {var:.2f}  kutu guveni {guven:.2f}')
    return (L + l * (R - L), T + t * (B - T), L + r * (R - L), T + b * (B - T))


foto = P.open('form_02_telefon.jpg').convert('RGB')
kutular = ocr_bul(foto)
for ad in kutular:
    print(f'  ocr  {ad:<8} bulundu')
if imza := imza_bul(foto):
    kutular['imza'] = imza

PAY = 0.02                                   # olculdu: yakindan + %2 pay -> 60/60 imza
cizim = ImageDraw.Draw(karart := foto.copy()); W, H = foto.size
for l, t, r, b in kutular.values():
    cizim.rectangle(((l - PAY) * W, (t - PAY) * H, (r + PAY) * W, (b + PAY) * H), fill='black')
karart.save('karartilmis.jpg')
print(f'  {len(kutular)} alan karartildi -> karartilmis.jpg')

import matplotlib.pyplot as plt
fig, eks = plt.subplots(1, 2, figsize=(14, 7.5), layout='constrained')
for e, g, baslik in zip(eks, (foto, karart), ('Once', 'Sonra')):
    e.imshow(g); e.set_title(baslik, fontsize=16); e.axis('off')
plt.show()
