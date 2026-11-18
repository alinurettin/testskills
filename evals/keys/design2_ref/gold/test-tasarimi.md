# GÜM v3.2 — test tasarım notu (referans çözüm)

Bu dosya puanlanmaz; referans teslimatın eksiksiz olması için eklenmiştir.

**Teknikler**

- Ücretlendirme: denklik sınıfları, sınır değer analizi (sınırın iki yanı, en küçük adımla), karar tablosu (indirim seçimi: sözleşme / kampanya / tavan / taban / aynı gün), yuvarlamanın sonucu değiştirdiği noktalar (HA 0,01 kg yarım yukarı, UA 0,5 kg yukarı, TB ve yüzde tutarlarında yarım kuruş), takvim analizi (kesim saati, cumartesi, pazar, Ek-B günleri, 29 Şubat, UZAK cumartesi kuralı). Beklenen değerler tam ondalık aritmetikle hesaplandı.
- Durum modeli: geçiş tablosu sayaçlarla birlikte genişletilmiş durum uzayında tarandı; 16 canlı geçiş ve 29 ardışık geçiş çifti (1-switch) 14 yol ile kapsandı, hata kolları ve tabloda olmayan olaylar ayrı satırlarda.
- Konfigürasyon: kısıtlı karma güç (tüm çiftler + `hizmet` × `bolge` × `teslim_noktasi` üçlüleri); 394 geçerli kombinasyondan 23 satır (alt sınır 18 + 5 = 23).

**Varsayımlar**

- Kesim saatinin kendisi (17:00 / cumartesi 13:00) 2.4 ile 8.2 arasında çelişkili olduğu için testlerde 1 dakika öncesi ve sonrası kullanıldı.
- `ERR_BEYAN_LIMIT` başka bir hatayla birlikte test edilmedi (9.3 listesinde yok).

**Kapsam dışı**

- G11 (hiçbir olay dizisiyle gerçekleşmiyor), `gun` biriminin anlamı, kısıtların ekranlarda engellenmesi (E2E matrisi yalnızca desteklenen kombinasyonları içerir).
