# Görev: Yayın Öncesi API Testi — Anadolu Güven Sigorta

Merhaba, ben Anadolu Güven Sigorta'da ürün ekibindenim. Yeni **Poliçe & Hasar
API**'mizi önümüzdeki hafta canlıya alacağız. Canlıya çıkmadan önce bağımsız bir
gözle test edilmesini istiyorum çünkü ekip içi testlerde fazla iyimser
davrandığımızı düşünüyorum.

Senden, elindeki **OpenAPI sözleşmesine (openapi.yaml)** göre çalışan API'yi
test etmeni ve bulduğun kusurları (hataları) kanıtlarıyla birlikte raporlamanı
istiyorum. Özellikle şunları merak ediyorum, ama bunlarla sınırlı kalma:

- Yetkilendirme doğru çalışıyor mu? Bir kullanıcı başkasının verisine veya
  yönetici işlemlerine erişebiliyor mu?
- API gerçekten sözleşmede (openapi.yaml) yazdığı gibi mi davranıyor? Yanıtlar,
  durum kodları, doğrulama kuralları ve iş kuralları söz verildiği gibi mi?
- Beklenmedik/kötü girdilerde mantıklı davranıyor mu, yoksa içini mi döküyor?

Lütfen her bulgu için **nasıl tekrar üretileceğini** (hangi istek, hangi token,
hangi yanıt) yaz ki geliştirici doğrulayabilsin. Gerçekten var olmayan bir sorunu
"hata" diye raporlamaktan kaçın; her bulgu kanıta dayanmalı.

## Erişim bilgileri

- API temel adresi: `http://localhost:3000`
  (Sunucu test ortamında çalışıyor; adres ve port sana ekip tarafından
  verilecek. Varsayılan port 3000'dir.)
- Kimlik doğrulama: `Authorization: Bearer <token>` başlığı.
- Test token'ları:
  | Token | Kullanıcı | Rol |
  |-------|-----------|-----|
  | `tok_user1_ayse`   | Ayşe Yılmaz (u1)     | normal kullanıcı |
  | `tok_user2_mehmet` | Mehmet Demir (u2)    | normal kullanıcı |
  | `tok_admin_root`   | Sistem Yöneticisi    | yönetici (admin) |

> Not: Ortamdaki tüm veriler sentetik/kurgusaldır (gerçek kişi, TCKN, IBAN veya
> ödeme bilgisi yoktur). İstediğin kadar kayıt oluşturabilir, güncelleyebilirsin;
> sunucu yeniden başlatıldığında durum sıfırlanır.

## Girdiler (sana verilenler)

1. `TASK.md` — bu dosya.
2. `openapi.yaml` — API'nin OpenAPI 3.1 sözleşmesi (doğru/beklenen davranışın
   kaynağı).
3. Çalışan API'nin temel adresi ve yukarıdaki test token'ları.

(Sunucunun kaynak kodu sana verilmez; yalnızca sözleşme ve çalışan servis üzerinden
test edersin.)

## Beklenen teslimatlar

Aşağıdaki dosyaları üret:

1. **`bulgular.md`** — Kusur (defect) raporu. Her bulgu için:
   - kısa başlık ve önem derecesi (Kritik / Yüksek / Orta / Düşük),
   - etkilenen uç (endpoint) ve beklenen vs. gerçekleşen davranış,
   - sözleşmeye (openapi.yaml) veya iş kuralına atıf,
   - tekrar üretim adımları (istek + token + gözlenen yanıt).
2. **`test-kayitlari.md`** — Çalıştırdığın isteklerin kanıt kaydı (gönderilen
   istekler ve alınan yanıtların özeti). `bulgular.md` içindeki her bulgu buradaki
   bir kanıta dayanmalı.

Raporu Türkçe yazman yeterli.
