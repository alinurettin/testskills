# Perdeaçık Bilet — Ürün notu (v0.9 demo)

Hazırlayan: Selin Aksoy, Ürün Sahibi · Perdeaçık Etkinlik Hizmetleri (kurgusal şirket)

Perdeaçık; küçük ve orta ölçekli salonlardaki konser, tiyatro ve gösterimler için web üzerinden bilet satışı yapan tek sayfalık bir uygulama. İlk sürümde üyelik yok. Ödeme etkinlik girişinde gişede alınıyor; uygulama yalnızca siparişi (rezervasyonu) oluşturuyor.

## Kullanıcı neler yapabilmeli

- Yaklaşan etkinlikleri listeleyebilmeli; etkinlik adı, şehir veya mekâna göre arama yapabilmeli, şehir filtresi ve sıralama (tarih, fiyat, ad) kullanabilmeli.
- Etkinlik detayında bilet türünü (Tam / Öğrenci) ve bilet adedini seçebilmeli. Bir siparişte en az 1, en fazla 6 bilet olabilir.
- Öğrenci biletinde bilet fiyatı %20 indirimlidir. Hizmet bedeli bilet başına 12,50 TL'dir ve indirimden etkilenmez.
- Kampanya: `PERDE50` kodu, hizmet bedeli dahil toplamı 300,00 TL ve üzeri olan siparişlerde 50 TL indirim sağlar.
- Ad soyad, e-posta, cep telefonu ve aydınlatma metni onayıyla siparişi tamamlayabilmeli; sipariş sonunda bir PNR kodu görmeli.
- "Biletlerim" sayfasında e-posta adresiyle siparişlerini görebilmeli. Etkinliğe 24 saatten fazla varsa siparişini iptal edebilmeli; iptal edilen koltuklar yeniden satışa açılır. İptal edilen siparişler listede "İptal edildi" durumuyla görünmeye devam eder.
- Tükenen etkinlik için bilet alınamaz.

## Kalite beklentileri

- Arayüz Türkçe; Türkçe içerik sorunsuz desteklenmeli.
- Tutarlar TL cinsinden, iki ondalık basamakla ve Türkçe biçimde gösterilmeli (ör. 1.234,50 TL).
- Erişilebilirlik hedefi: WCAG 2.1 AA.
- Desteklenen tarayıcılar: Chrome ve Edge'in güncel sürümleri (masaüstü ve mobil genişlik).

## Bilinen durumlar

- Bu bir demo/test ortamıdır; veriler bellekte tutulur ve sunucu yeniden başlatılınca sıfırlanır.
- Gerçek ödeme ve e-posta gönderimi bu sürümde yoktur.
