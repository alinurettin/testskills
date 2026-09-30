'use strict';

// Perdeaçık Bilet — demo sunucusu (yalnızca Node.js yerleşik modülleri)
// Tüm veriler bellekte tutulur; sunucu yeniden başlatıldığında sıfırlanır.

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PORT = Number.parseInt(process.env.PORT || '4310', 10);
const HOST = process.env.HOST || '127.0.0.1';

const HIZMET_BEDELI = 12.5;
const OGRENCI_CARPANI = 0.8;
const KAMPANYALAR = { PERDE50: { indirim: 50, altSinir: 300 } };
const IPTAL_SINIRI_MS = 24 * 60 * 1000; // 24 saat
const ODEME_GECIKMESI_MS = 700;

const AD_DESENI = /^[\p{L}][\p{L} .'-]{1,58}[\p{L}.]$/u;
const EPOSTA_DESENI = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// ---------------------------------------------------------------------------
// Statik dosyalar
// ---------------------------------------------------------------------------
const PUBLIC_DIR = path.join(__dirname, 'public');
const STATIK = {
  '/': ['index.html', 'text/html; charset=utf-8'],
  '/index.html': ['index.html', 'text/html; charset=utf-8'],
  '/app.js': ['app.js', 'text/javascript; charset=utf-8'],
  '/style.css': ['style.css', 'text/css; charset=utf-8'],
};

// ---------------------------------------------------------------------------
// Örnek veriler (sunucu açılış zamanına göre üretilir)
// ---------------------------------------------------------------------------
// Bugün ve yarın için 10:00–22:30 arası yarım saatlik seans adayları arasından,
// şu andan en az `enAzSaat`, en çok `enCokSaat` sonrasına düşen ilk/son seansı seçer.
function yakinSeans(enAzSaat, enCokSaat, sonuncu) {
  const simdi = Date.now();
  const uygun = [];
  for (let gun = 0; gun <= 1; gun++) {
    for (let dakika = 10 * 60; dakika <= 22 * 60 + 30; dakika += 30) {
      const d = new Date();
      d.setDate(d.getDate() + gun);
      d.setHours(0, dakika, 0, 0);
      const fark = d.getTime() - simdi;
      if (fark >= enAzSaat * 3600 * 1000 && fark <= enCokSaat * 3600 * 1000) uygun.push(d);
    }
  }
  return sonuncu ? uygun[uygun.length - 1] : uygun[0];
}

function gunSonra(gun, saat, dakika) {
  const d = new Date();
  d.setDate(d.getDate() + gun);
  d.setHours(saat, dakika, 0, 0);
  return d;
}

const etkinlikler = [
  {
    id: 101, kategori: 'Konser', baslik: 'Boğaziçi Caz Gecesi', sehir: 'İstanbul', mekan: 'Moda Kültür Sahnesi',
    tarih: yakinSeans(3, 23, false), fiyat: 149.9, kapasite: 120, kalan: 38,
    aciklama: 'Kadıköy\'ün sevilen caz dörtlüsü, standartlardan ve yeni bestelerden oluşan bir repertuvarla sahnede.',
  },
  {
    id: 102, kategori: 'Klasik', baslik: 'İstanbul Gençlik Senfonisi: Mevsimler', sehir: 'İstanbul', mekan: 'Nişantaşı Oda Sahnesi',
    tarih: yakinSeans(3, 23, true), fiyat: 275, kapasite: 200, kalan: 64,
    aciklama: 'Genç müzisyenlerden oluşan orkestra, Vivaldi\'nin Dört Mevsim\'ini matine konserinde yorumluyor.',
  },
  {
    id: 103, kategori: 'Klasik', baslik: 'Çello ve Piyano Resitali', sehir: 'Ankara', mekan: 'Kavaklıdere Oda Salonu',
    tarih: gunSonra(3, 20, 0), fiyat: 220, kapasite: 90, kalan: 52,
    aciklama: 'Brahms ve Fauré eserlerinden oluşan samimi bir oda müziği akşamı.',
  },
  {
    id: 104, kategori: 'Konser', baslik: 'İzmir Kordon Akustik', sehir: 'İzmir', mekan: 'Alsancak Sanat Evi',
    tarih: gunSonra(6, 21, 0), fiyat: 164.99, kapasite: 150, kalan: 80,
    aciklama: 'Ege\'nin genç şarkı yazarları akustik bir gecede buluşuyor.',
  },
  {
    id: 105, kategori: 'Tiyatro', baslik: 'Şebnem\'in Düğünü', sehir: 'Eskişehir', mekan: 'Odunpazarı Sahnesi',
    tarih: gunSonra(9, 20, 30), fiyat: 185, kapasite: 80, kalan: 3,
    aciklama: 'İki perdelik bir aile komedisi. Son koltuklar!',
  },
  {
    id: 106, kategori: 'Halk müziği', baslik: 'Zeybek ve Ege Ezgileri', sehir: 'Bursa', mekan: 'Nilüfer Kültür Evi',
    tarih: gunSonra(12, 19, 0), fiyat: 95.5, kapasite: 100, kalan: 0,
    aciklama: 'Ege\'nin zeybek havaları ve türküleri canlı icrayla.',
  },
  {
    id: 107, kategori: 'Gösteri', baslik: 'Ankara Stand-up Gecesi', sehir: 'Ankara', mekan: 'Tunalı Kulüp Sahne',
    tarih: gunSonra(15, 21, 30), fiyat: 137.5, kapasite: 140, kalan: 110,
    aciklama: 'Dört genç komedyen, dört farklı bakış açısı.',
  },
  {
    id: 108, kategori: 'Sinema', baslik: 'Ödüllü Kısa Filmler Gösterimi', sehir: 'İzmir', mekan: 'Konak Sinematek',
    tarih: gunSonra(20, 18, 0), fiyat: 60, kapasite: 90, kalan: 90,
    aciklama: 'Bu yılın festivallerinden ödüllü yedi kısa film ve yönetmenlerle söyleşi.',
  },
  {
    id: 109, kategori: 'Konser', baslik: 'Üsküdar Tasavvuf Musikisi Konseri', sehir: 'İstanbul', mekan: 'Kuzguncuk Kültür Evi',
    tarih: gunSonra(25, 20, 0), fiyat: 120, kapasite: 110, kalan: 75,
    aciklama: 'Ney, kudüm ve tanbur eşliğinde klasik tasavvuf eserleri.',
  },
];

const siparisler = [];

// ---------------------------------------------------------------------------
// Yardımcılar
// ---------------------------------------------------------------------------
class IstekHatasi extends Error {
  constructor(durum, mesaj) {
    super(mesaj);
    this.durum = durum;
  }
}

function json(res, durum, veri) {
  const govde = JSON.stringify(veri);
  res.writeHead(durum, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Content-Length': Buffer.byteLength(govde),
  });
  res.end(govde);
}

function govdeOku(req) {
  return new Promise((resolve, reject) => {
    const parcalar = [];
    let boyut = 0;
    req.on('data', (parca) => {
      boyut += parca.length;
      if (boyut > 100000) {
        reject(new IstekHatasi(413, 'İstek gövdesi çok büyük.'));
        req.destroy();
        return;
      }
      parcalar.push(parca);
    });
    req.on('end', () => {
      const metin = Buffer.concat(parcalar).toString('utf8');
      if (!metin) return resolve({});
      try {
        resolve(JSON.parse(metin));
      } catch (_) {
        reject(new IstekHatasi(400, 'Geçersiz JSON gövdesi.'));
      }
    });
    req.on('error', reject);
  });
}

const bekle = (ms) => new Promise((r) => setTimeout(r, ms));

function pnrUret() {
  const harfler = 'ABCDEFGHJKLMNPRSTUVYZ23456789';
  let pnr;
  do {
    pnr = '';
    for (let i = 0; i < 6; i++) pnr += harfler[crypto.randomInt(harfler.length)];
  } while (siparisler.some((s) => s.pnr === pnr));
  return pnr;
}

function etkinlikGorunumu(e) {
  return {
    id: e.id, kategori: e.kategori, baslik: e.baslik, sehir: e.sehir, mekan: e.mekan,
    tarih: e.tarih.toISOString(), fiyat: e.fiyat, kapasite: e.kapasite, kalan: e.kalan, aciklama: e.aciklama,
  };
}

function siparisGorunumu(s) {
  const ev = etkinlikler.find((e) => e.id === s.etkinlikId);
  return {
    pnr: s.pnr, etkinlikId: s.etkinlikId, etkinlikBaslik: ev.baslik, etkinlikTarih: ev.tarih.toISOString(),
    sehir: ev.sehir, mekan: ev.mekan, tur: s.tur, adet: s.adet, adSoyad: s.adSoyad, eposta: s.eposta,
    telefon: s.telefon, kampanyaKodu: s.kampanyaKodu, toplam: s.toplam, durum: s.durum,
    olusturmaZamani: s.olusturmaZamani.toISOString(),
  };
}

function telefonNormalEt(telefon) {
  return BigInt(telefon.replace(/\s+/g, ''));
}

// ---------------------------------------------------------------------------
// API işleyicileri
// ---------------------------------------------------------------------------
function etkinlikleriListele(res) {
  const simdi = Date.now();
  const liste = etkinlikler
    .filter((e) => e.tarih.getTime() > simdi)
    .sort((a, b) => a.tarih - b.tarih)
    .map(etkinlikGorunumu);
  json(res, 200, { etkinlikler: liste });
}

function etkinlikDetay(res, id) {
  const ev = etkinlikler.find((e) => e.id === Number(id));
  if (!ev) return json(res, 404, { hata: 'Etkinlik bulunamadı.' });
  json(res, 200, etkinlikGorunumu(ev));
}

function kampanyaKontrol(res, url) {
  const kod = String(url.searchParams.get('kod') ?? '').trim().toLocaleUpperCase('tr-TR');
  const tutar = Number(url.searchParams.get('tutar'));
  if (!kod || !Object.hasOwn(KAMPANYALAR, kod)) return json(res, 404, { hata: 'Kampanya kodu geçersiz.' });
  const k = KAMPANYALAR[kod];
  if (!Number.isFinite(tutar) || tutar < k.altSinir) {
    return json(res, 422, { hata: `Bu kod ${k.altSinir},00 TL ve üzeri siparişlerde geçerlidir.` });
  }
  json(res, 200, { kod, indirim: k.indirim });
}

async function siparisOlustur(req, res) {
  const g = await govdeOku(req);
  if (!g || typeof g !== 'object' || Array.isArray(g)) return json(res, 400, { hata: 'Geçersiz istek gövdesi.' });

  const adSoyad = String(g.adSoyad ?? '').trim();
  const eposta = String(g.eposta ?? '').trim();
  const telefon = String(g.telefon ?? '').trim();
  if (!AD_DESENI.test(adSoyad)) return json(res, 400, { hata: 'Ad soyad en az 3 harften oluşmalı ve yalnızca harf içermelidir.' });
  if (!EPOSTA_DESENI.test(eposta)) return json(res, 400, { hata: 'Geçerli bir e-posta adresi girin.' });
  const telNo = telefonNormalEt(telefon).toString();
  if (telNo.length < 10 || telNo.length > 12) return json(res, 400, { hata: 'Geçerli bir cep telefonu numarası girin.' });
  if (g.kvkk !== true) return json(res, 400, { hata: 'Devam etmek için aydınlatma metnini onaylamanız gerekir.' });

  const ev = etkinlikler.find((e) => e.id === Number(g.etkinlikId));
  if (ev.tarih.getTime() <= Date.now()) return json(res, 409, { hata: 'Bu etkinliğin satışı kapanmıştır.' });

  const tur = g.tur;
  if (tur !== 'tam' && tur !== 'ogrenci') return json(res, 400, { hata: 'Geçersiz bilet türü.' });
  const adet = Math.trunc(Number(g.adet ?? 0));
  if (!Number.isFinite(adet)) return json(res, 400, { hata: 'Geçersiz bilet adedi.' });

  // Ödeme sağlayıcısı ön onayı (demo gecikmesi)
  await bekle(ODEME_GECIKMESI_MS);

  if (adet > ev.kalan) return json(res, 409, { hata: `Bu etkinlik için yeterli koltuk yok. Kalan koltuk: ${ev.kalan}.` });

  const birim = tur === 'ogrenci' ? ev.fiyat * OGRENCI_CARPANI : ev.fiyat;
  let toplam = birim * adet + HIZMET_BEDELI * adet;

  let kampanyaKodu = null;
  const kod = String(g.kampanyaKodu ?? '').trim().toLocaleUpperCase('tr-TR');
  if (kod) {
    if (!Object.hasOwn(KAMPANYALAR, kod)) return json(res, 400, { hata: 'Kampanya kodu geçersiz.' });
    const k = KAMPANYALAR[kod];
    if (toplam < k.altSinir) return json(res, 400, { hata: `Bu kod ${k.altSinir},00 TL ve üzeri siparişlerde geçerlidir.` });
    toplam -= k.indirim;
    kampanyaKodu = kod;
  }

  ev.kalan -= adet;
  const siparis = {
    pnr: pnrUret(), etkinlikId: ev.id, tur, adet, adSoyad, eposta, telefon, telNo, kampanyaKodu,
    toplam, durum: 'aktif', olusturmaZamani: new Date(),
  };
  siparisler.push(siparis);
  json(res, 201, siparisGorunumu(siparis));
}

function siparisleriListele(res, url) {
  const eposta = String(url.searchParams.get('eposta') ?? '').trim().toLowerCase();
  if (!eposta) return json(res, 400, { hata: 'E-posta adresi gerekli.' });
  const liste = siparisler
    .filter((s) => s.eposta.toLowerCase() === eposta)
    .sort((a, b) => b.olusturmaZamani - a.olusturmaZamani)
    .map(siparisGorunumu);
  json(res, 200, { siparisler: liste });
}

function siparisGetir(res, pnr) {
  const s = siparisler.find((x) => x.pnr === String(pnr).toUpperCase());
  if (!s) return json(res, 404, { hata: 'Sipariş bulunamadı.' });
  json(res, 200, siparisGorunumu(s));
}

function siparisIptal(res, pnr) {
  const s = siparisler.find((x) => x.pnr === String(pnr).toUpperCase());
  if (!s) return json(res, 404, { hata: 'Sipariş bulunamadı.' });
  if (s.durum === 'iptal') return json(res, 409, { hata: 'Bu sipariş zaten iptal edilmiş.' });
  const ev = etkinlikler.find((e) => e.id === s.etkinlikId);
  if (ev.tarih.getTime() - Date.now() < IPTAL_SINIRI_MS) {
    return json(res, 409, { hata: 'Etkinliğe 24 saatten az kaldığı için bu sipariş iptal edilemez.' });
  }
  s.durum = 'iptal';
  s.iptalZamani = new Date();
  ev.kalan += s.adet;
  json(res, 200, siparisGorunumu(s));
}

// ---------------------------------------------------------------------------
// Yönlendirme
// ---------------------------------------------------------------------------
async function yonlendir(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const yol = url.pathname;
  const yontem = req.method;

  if (yol.startsWith('/api/')) {
    const p = yol.split('/').filter(Boolean); // ['api', ...]
    if (p[1] === 'saglik' && p.length === 2 && yontem === 'GET') return json(res, 200, { durum: 'ok' });
    if (p[1] === 'etkinlikler') {
      if (p.length === 2 && yontem === 'GET') return etkinlikleriListele(res);
      if (p.length === 3 && yontem === 'GET') return etkinlikDetay(res, p[2]);
    }
    if (p[1] === 'kampanya' && p.length === 2 && yontem === 'GET') return kampanyaKontrol(res, url);
    if (p[1] === 'siparisler') {
      if (p.length === 2 && yontem === 'POST') return siparisOlustur(req, res);
      if (p.length === 2 && yontem === 'GET') return siparisleriListele(res, url);
      if (p.length === 3 && yontem === 'GET') return siparisGetir(res, p[2]);
      if (p.length === 4 && p[3] === 'iptal' && yontem === 'POST') return siparisIptal(res, p[2]);
    }
    return json(res, 404, { hata: 'Kaynak bulunamadı.' });
  }

  const statik = STATIK[yol];
  if (statik && (yontem === 'GET' || yontem === 'HEAD')) {
    const icerik = fs.readFileSync(path.join(PUBLIC_DIR, statik[0]));
    res.writeHead(200, { 'Content-Type': statik[1], 'Cache-Control': 'no-store', 'Content-Length': icerik.length });
    return res.end(yontem === 'HEAD' ? undefined : icerik);
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('Bulunamadı');
}

const sunucu = http.createServer(async (req, res) => {
  try {
    await yonlendir(req, res);
  } catch (err) {
    if (err instanceof IstekHatasi) {
      if (!res.headersSent) json(res, err.durum, { hata: err.message });
      return;
    }
    console.error(err);
    if (!res.headersSent) {
      json(res, 500, { hata: 'Beklenmeyen bir hata oluştu: ' + err.message, detay: err.stack });
    }
  }
});

sunucu.listen(PORT, HOST, () => {
  console.log(`Perdeaçık Bilet demo sunucusu: http://${HOST}:${PORT}`);
});

function kapat() {
  sunucu.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 500).unref();
}
process.on('SIGINT', kapat);
process.on('SIGTERM', kapat);
