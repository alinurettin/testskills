# Görev: Yayın Öncesi API Testi — Turna Oto Kiralama

Merhaba, ben Turna Oto Kiralama'da ürün ekibindenim. Yeni **Rezervasyon ve
Kiralama API**'mizi önümüzdeki hafta canlıya alacağız: araç arama, fiyat
teklifi, rezervasyon, araç teslimi, iade ve faturalama bu API üzerinden
yürüyecek. Canlıya çıkmadan önce bağımsız bir gözle test edilmesini istiyorum,
çünkü ekip içi testlerde fazla iyimser davrandığımızı düşünüyorum.

Senden, elindeki **OpenAPI sözleşmesine (`openapi.yaml`)** göre çalışan API'yi
test etmeni ve bulduklarını kanıtlarıyla birlikte raporlamanı istiyorum. Doğru
davranışın tek kaynağı sözleşmedir; sözleşmenin başındaki genel kurallar
(roller, sabit sunucu saati, fiyatlandırma, müsaitlik vb.) bütün uçlar için
geçerlidir.

Gerçekten var olmayan bir sorunu "hata" diye raporlamaktan kaçın; her bulgu
kanıta dayanmalı ve geliştiricinin aynı sonucu yeniden elde edebileceği kadar
açık olmalı.

## Erişim bilgileri

- API temel adresi: `http://localhost:3210`
  (Sunucu test ortamında çalışıyor; adres ve port sana ekip tarafından
  bildirilecek. Varsayılan port 3210'dur.)
- Kimlik doğrulama: `Authorization: Bearer <token>` başlığı.
- Test token'ları:

  | Token | Kullanıcı | Rol |
  |-------|-----------|-----|
  | `tok_musteri_elif`  | Elif Aksoy (`mus_1`)    | müşteri |
  | `tok_musteri_baran` | Baran Çetin (`mus_2`)   | müşteri |
  | `tok_personel_ist`  | Deniz Korkmaz (`per_1`) | şube personeli, İstanbul şubesi (`IST`) |
  | `tok_yonetici`      | Sistem Yöneticisi       | yönetici |

> Not: Ortamdaki tüm veriler sentetik/kurgusaldır (gerçek kişi, kimlik numarası
> veya ödeme bilgisi yoktur). İstediğin kadar kayıt oluşturabilir, değiştirebilir,
> iptal edebilirsin. Sunucunun saati sabittir (sözleşmede yazıyor); sunucu
> yeniden başlatılırsa veriler başlangıç durumuna döner.

## Girdiler (sana verilenler)

1. `TASK.md` — bu dosya.
2. `openapi.yaml` — API'nin OpenAPI 3.1 sözleşmesi (beklenen davranışın kaynağı).
3. Çalışan API'nin temel adresi ve yukarıdaki test token'ları.

Sunucunun kaynak kodu sana verilmez; yalnızca sözleşme ve çalışan servis
üzerinden test edersin.

## Beklenen teslimatlar

Aşağıdaki iki dosyayı üret:

1. **`bulgular.md`** — iki ayrı bölümden oluşur:

   **Kusurlar** — API'nin sözleşmeye aykırı davrandığı durumlar. Her kusur için:
   - kısa başlık ve önem derecesi (Kritik / Yüksek / Orta / Düşük),
   - etkilenen uç (endpoint),
   - beklenen davranış ve gerçekleşen davranış,
   - ihlal edilen sözleşme ifadesi (`openapi.yaml` içindeki cümle, şema kuralı
     veya durum kodu; mümkünse alıntılayarak),
   - tekrar üretim: gönderilen istek, kullanılan token ve gözlenen yanıt.

   **Açık sorular ve gözlemler** — sözleşmenin hüküm vermediği, bu yüzden kusur
   diyemediğin ama ekibin bilmesi ya da karar vermesi gereken davranışlar.

2. **`test-kayitlari.md`** — çalıştırdığın isteklerin kanıt kaydı (gönderilen
   istekler ve alınan yanıtların özeti). `bulgular.md` içindeki her madde
   buradaki bir kayda dayanmalı.

Raporu Türkçe yazman yeterli.
