'use strict';

(function () {
  const icerik = document.getElementById('icerik');
  const iptalKutusu = document.getElementById('iptalKutusu');

  const MAKS_ADET = 6;
  const HIZMET_BEDELI_K = 1250;
  const OGRENCI_CARPANI = 0.8;

  const durum = {
    etkinlikler: null,
    filtre: { ara: '', sehir: '', sirala: 'tarih' },
    sepet: null,
    sonEposta: '',
  };
  let cizimNo = 0;

  // -------------------------------------------------------------------------
  // Biçimlendirme
  // -------------------------------------------------------------------------
  const paraBicimi = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const tl = (tutar) => paraBicimi.format(tutar) + ' TL';
  const tlK = (kurus) => tl(kurus / 100);

  const gunBicimi = new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', year: 'numeric', weekday: 'long' });
  const saatBicimi = new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit' });

  function tarihYaz(iso) {
    const d = new Date(iso);
    const bugun = new Date();
    bugun.setHours(0, 0, 0, 0);
    const gun = new Date(d);
    gun.setHours(0, 0, 0, 0);
    const fark = Math.round((gun - bugun) / 86400000);
    const on = fark === 0 ? 'Bugün, ' : fark === 1 ? 'Yarın, ' : '';
    return on + gunBicimi.format(d) + ' · ' + saatBicimi.format(d);
  }

  function esc(deger) {
    return String(deger).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  const turAdi = (tur) => (tur === 'ogrenci' ? 'Öğrenci' : 'Tam');

  function hesapla(fiyat, tur, adet, kampanyaVar) {
    const tamK = Math.round(fiyat * 100);
    const birimK = tur === 'ogrenci' ? Math.round(tamK * OGRENCI_CARPANI) : tamK;
    const biletK = birimK * adet;
    const hizmetK = HIZMET_BEDELI_K * adet;
    const araK = biletK + hizmetK;
    const indirimK = kampanyaVar ? 5000 : 0;
    return { tamK, birimK, biletK, hizmetK, araK, indirimK, toplamK: araK - indirimK };
  }

  async function api(yol, secenekler) {
    const yanit = await fetch(yol, secenekler);
    let veri = null;
    try {
      veri = await yanit.json();
    } catch (_) {
      veri = null;
    }
    return { ok: yanit.ok, durum: yanit.status, veri: veri || {} };
  }

  function sayfaBasligi(metin) {
    document.title = metin + ' · Perdeaçık Bilet';
  }

  // -------------------------------------------------------------------------
  // Etkinlik listesi
  // -------------------------------------------------------------------------
  async function listeGoster() {
    const no = ++cizimNo;
    sayfaBasligi('Etkinlikler');
    if (!durum.etkinlikler) {
      icerik.innerHTML = '<p class="bilgi">Etkinlikler yükleniyor…</p>';
      let r;
      try {
        r = await api('/api/etkinlikler');
      } catch (_) {
        r = { ok: false, veri: {} };
      }
      if (no !== cizimNo) return;
      if (!r.ok) {
        icerik.innerHTML = '<p class="hata" role="alert">Etkinlikler yüklenemedi. Lütfen sayfayı yenileyin.</p>';
        return;
      }
      durum.etkinlikler = r.veri.etkinlikler;
    }

    const f = durum.filtre;
    const sehirler = [...new Set(durum.etkinlikler.map((e) => e.sehir))].sort((a, b) => a.localeCompare(b, 'tr'));
    icerik.innerHTML = `
      <h1>Yaklaşan etkinlikler</h1>
      <form class="filtreler" role="search" onsubmit="return false">
        <div class="alan">
          <label for="ara">Ara</label>
          <input id="ara" type="search" placeholder="Etkinlik, şehir veya mekân" autocomplete="off" value="${esc(f.ara)}">
        </div>
        <div class="alan">
          <label for="sehir">Şehir</label>
          <select id="sehir">
            <option value="">Tüm şehirler</option>
            ${sehirler.map((s) => `<option value="${esc(s)}"${s === f.sehir ? ' selected' : ''}>${esc(s)}</option>`).join('')}
          </select>
        </div>
        <div class="alan">
          <label for="sirala">Sırala</label>
          <select id="sirala">
            <option value="tarih"${f.sirala === 'tarih' ? ' selected' : ''}>Tarihe göre</option>
            <option value="fiyat"${f.sirala === 'fiyat' ? ' selected' : ''}>Fiyata göre (artan)</option>
            <option value="ad"${f.sirala === 'ad' ? ' selected' : ''}>Ada göre (A–Z)</option>
          </select>
        </div>
      </form>
      <p id="sonucSayisi" class="sonuc" aria-live="polite"></p>
      <ul id="kartlar" class="kartlar"></ul>`;

    document.getElementById('ara').addEventListener('input', (e) => { f.ara = e.target.value; listeCiz(); });
    document.getElementById('sehir').addEventListener('change', (e) => { f.sehir = e.target.value; listeCiz(); });
    document.getElementById('sirala').addEventListener('change', (e) => { f.sirala = e.target.value; listeCiz(); });
    listeCiz();
  }

  function listeCiz() {
    const f = durum.filtre;
    const aranan = f.ara.trim().toLowerCase();
    const liste = durum.etkinlikler.filter((e) => {
      if (f.sehir && e.sehir !== f.sehir) return false;
      if (!aranan) return true;
      return (e.baslik + ' ' + e.sehir + ' ' + e.mekan).toLowerCase().includes(aranan);
    });
    if (f.sirala === 'fiyat') liste.sort((a, b) => a.fiyat - b.fiyat);
    else if (f.sirala === 'ad') liste.sort((a, b) => a.baslik.localeCompare(b.baslik, 'tr'));
    else liste.sort((a, b) => new Date(a.tarih) - new Date(b.tarih));

    document.getElementById('sonucSayisi').textContent = liste.length
      ? `${liste.length} etkinlik listeleniyor.`
      : 'Aramanızla eşleşen etkinlik bulunamadı.';

    document.getElementById('kartlar').innerHTML = liste.map((e) => `
      <li class="kart">
        <p class="kategori">${esc(e.kategori)}</p>
        <h2><a href="#/etkinlik/${e.id}">${esc(e.baslik)}</a></h2>
        <p class="yer">${esc(e.sehir)} · ${esc(e.mekan)}</p>
        <p class="zaman">${esc(tarihYaz(e.tarih))}</p>
        <p class="kart-alt">
          <strong>${tl(e.fiyat)}</strong>
          ${e.kalan > 0 ? `<span>Kalan: ${e.kalan} koltuk</span>` : '<span class="rozet">Tükendi</span>'}
        </p>
      </li>`).join('');
  }

  // -------------------------------------------------------------------------
  // Etkinlik detayı
  // -------------------------------------------------------------------------
  async function detayGoster(id) {
    const no = ++cizimNo;
    sayfaBasligi('Etkinlik');
    icerik.innerHTML = '<p class="bilgi">Yükleniyor…</p>';
    let r;
    try {
      r = await api('/api/etkinlikler/' + encodeURIComponent(id));
    } catch (_) {
      r = { ok: false, veri: { hata: 'Sunucuya ulaşılamadı.' } };
    }
    if (no !== cizimNo) return;
    if (!r.ok) {
      icerik.innerHTML = `<h1>Etkinlik bulunamadı</h1><p>${esc(r.veri.hata || '')}</p><p><a href="#/">Etkinliklere dön</a></p>`;
      return;
    }
    const ev = r.veri;
    sayfaBasligi(ev.baslik);
    const ogrenciK = Math.round(Math.round(ev.fiyat * 100) * OGRENCI_CARPANI);
    const tukendi = ev.kalan <= 0;
    const onceki = durum.sepet && durum.sepet.etkinlikId === ev.id ? durum.sepet : null;
    let tur = onceki ? onceki.tur : 'tam';
    const ilkAdet = onceki && Number.isFinite(onceki.adet) ? onceki.adet : 1;

    icerik.innerHTML = `
      <p class="geri"><a href="#/">← Tüm etkinlikler</a></p>
      <article class="detay">
        <p class="kategori">${esc(ev.kategori)}</p>
        <h1>${esc(ev.baslik)}</h1>
        <p class="yer">${esc(ev.sehir)} · ${esc(ev.mekan)}</p>
        <p class="zaman">${esc(tarihYaz(ev.tarih))}</p>
        <p>${esc(ev.aciklama)}</p>
        <p class="kalan">${tukendi ? '<span class="rozet">Tükendi</span>' : `Kalan: <strong>${ev.kalan}</strong> koltuk`}</p>

        <section class="satin-al" aria-labelledby="satinAlBaslik">
          <h2 id="satinAlBaslik">Bilet al</h2>
          <span class="etiket">Bilet türü</span>
          <div class="chips" id="turSecimi">
            <div class="chip${tur === 'tam' ? ' secili' : ''}" data-tur="tam">Tam<small>${tl(ev.fiyat)}</small></div>
            <div class="chip${tur === 'ogrenci' ? ' secili' : ''}" data-tur="ogrenci">Öğrenci<small>${tlK(ogrenciK)} (%20 indirimli)</small></div>
          </div>
          <div class="alan kisa">
            <label for="adet">Bilet adedi</label>
            <input id="adet" type="number" min="1" max="${MAKS_ADET}" value="${ilkAdet}" inputmode="numeric" ${tukendi ? 'disabled' : ''}>
            <small class="ipucu">Bir siparişte en fazla ${MAKS_ADET} bilet.</small>
          </div>
          <dl class="ozet" id="detayOzet" aria-live="polite"></dl>
          <p class="hata" id="detayHata" role="alert" hidden></p>
          <button id="devamEt" class="birincil" ${tukendi ? 'disabled' : ''}>${tukendi ? 'Tükendi' : 'Devam et'}</button>
        </section>
      </article>`;

    const adetGirdi = document.getElementById('adet');
    const hataKutusu = document.getElementById('detayHata');

    function ozetGuncelle() {
      const adet = parseInt(adetGirdi.value, 10);
      const ozet = document.getElementById('detayOzet');
      if (Number.isNaN(adet)) {
        ozet.innerHTML = '<dt>Toplam</dt><dd>—</dd>';
        return;
      }
      const h = hesapla(ev.fiyat, tur, adet, false);
      ozet.innerHTML = `
        <dt>${adet} × ${turAdi(tur)} bilet</dt><dd>${tlK(h.biletK)}</dd>
        <dt>Hizmet bedeli</dt><dd>${tlK(h.hizmetK)}</dd>
        <dt class="toplam">Toplam</dt><dd class="toplam">${tlK(h.toplamK)}</dd>`;
    }

    document.querySelectorAll('#turSecimi .chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        if (tukendi) return;
        tur = chip.dataset.tur;
        document.querySelectorAll('#turSecimi .chip').forEach((c) => c.classList.toggle('secili', c === chip));
        ozetGuncelle();
      });
    });
    adetGirdi.addEventListener('input', () => {
      hataKutusu.hidden = true;
      ozetGuncelle();
    });

    document.getElementById('devamEt').addEventListener('click', () => {
      const adet = parseInt(adetGirdi.value, 10);
      if (adet > MAKS_ADET) {
        hataKutusu.textContent = `Bir siparişte en fazla ${MAKS_ADET} bilet alınabilir.`;
        hataKutusu.hidden = false;
        return;
      }
      if (adet > ev.kalan) {
        hataKutusu.textContent = `Bu etkinlik için yeterli koltuk yok (kalan: ${ev.kalan}).`;
        hataKutusu.hidden = false;
        return;
      }
      durum.sepet = {
        etkinlikId: ev.id, baslik: ev.baslik, tarih: ev.tarih, sehir: ev.sehir, mekan: ev.mekan,
        fiyat: ev.fiyat, tur, adet, kampanya: null,
      };
      location.hash = '#/odeme';
    });

    ozetGuncelle();
  }

  // -------------------------------------------------------------------------
  // Ödeme
  // -------------------------------------------------------------------------
  function odemeGoster() {
    ++cizimNo;
    sayfaBasligi('Siparişi tamamla');
    const s = durum.sepet || {};

    icerik.innerHTML = `
      <p class="geri"><a href="#/">← Etkinliklere dön</a></p>
      <h1>Siparişi tamamla</h1>
      <div class="iki-kolon">
        <section class="ozet-kutusu" aria-labelledby="ozetBaslik">
          <h2 id="ozetBaslik">Sipariş özeti</h2>
          <p class="ozet-etkinlik"><strong>${esc(s.baslik)}</strong></p>
          <p class="zaman">${s.tarih ? esc(tarihYaz(s.tarih)) : ''}</p>
          <p class="yer">${s.sehir ? esc(s.sehir + ' · ' + s.mekan) : ''}</p>
          <dl class="ozet" id="odemeOzet" aria-live="polite"></dl>
          <form class="kampanya" id="kampanyaFormu" novalidate>
            <label for="kampanyaKodu">Kampanya kodu</label>
            <div class="satir">
              <input id="kampanyaKodu" type="text" autocomplete="off">
              <button type="submit" id="kampanyaUygula" class="ikincil">Uygula</button>
            </div>
            <p id="kampanyaMesaj" class="kucuk" aria-live="polite"></p>
          </form>
        </section>

        <form id="odemeFormu" class="form" novalidate>
          <h2>İletişim bilgileri</h2>
          <div class="alan">
            <label for="adSoyad">Ad Soyad</label>
            <input id="adSoyad" name="adSoyad" autocomplete="name" required>
          </div>
          <div class="alan">
            <label for="eposta">E-posta</label>
            <input id="eposta" name="eposta" type="email" autocomplete="email" required>
          </div>
          <div class="alan">
            <label for="telefon">Cep telefonu</label>
            <input id="telefon" name="telefon" type="tel" autocomplete="tel" placeholder="05XX XXX XX XX" required>
          </div>
          <div class="alan onay">
            <input id="kvkk" type="checkbox">
            <label for="kvkk">Aydınlatma metnini okudum ve kişisel verilerimin sipariş için işlenmesini kabul ediyorum.</label>
          </div>
          <div class="hata" id="odemeHata" role="alert" hidden></div>
          <p id="odemeDurum" class="bilgi" aria-live="polite"></p>
          <button type="submit" class="birincil">Siparişi tamamla</button>
          <p class="kucuk">Ödeme, etkinlik girişinde gişede alınır.</p>
        </form>
      </div>`;

    function ozetCiz() {
      const h = hesapla(s.fiyat, s.tur, s.adet, !!s.kampanya);
      document.getElementById('odemeOzet').innerHTML = `
        <dt>${s.adet} × ${turAdi(s.tur)} bilet (${tlK(h.birimK)})</dt><dd>${tlK(h.biletK)}</dd>
        <dt>Hizmet bedeli (${s.adet} × 12,50 TL)</dt><dd>${tlK(h.hizmetK)}</dd>
        ${s.kampanya ? `<dt>Kampanya (${esc(s.kampanya)})</dt><dd>−${tlK(h.indirimK)}</dd>` : ''}
        <dt class="toplam">Ödenecek toplam</dt><dd class="toplam">${tlK(h.toplamK)}</dd>`;
      return h;
    }
    ozetCiz();

    const kampanyaMesaj = document.getElementById('kampanyaMesaj');
    document.getElementById('kampanyaFormu').addEventListener('submit', async (olay) => {
      olay.preventDefault();
      const kod = document.getElementById('kampanyaKodu').value.trim();
      kampanyaMesaj.classList.remove('hata-metin');
      if (!kod) {
        kampanyaMesaj.textContent = 'Lütfen bir kampanya kodu girin.';
        return;
      }
      const h = hesapla(s.fiyat, s.tur, s.adet, false);
      let r;
      try {
        r = await api('/api/kampanya?kod=' + encodeURIComponent(kod) + '&tutar=' + (h.araK / 100));
      } catch (_) {
        r = { ok: false, veri: { hata: 'Sunucuya ulaşılamadı.' } };
      }
      if (!r.ok) {
        kampanyaMesaj.textContent = r.veri.hata || 'Kampanya kodu uygulanamadı.';
        kampanyaMesaj.classList.add('hata-metin');
        return;
      }
      s.kampanya = r.veri.kod;
      kampanyaMesaj.textContent = `${r.veri.kod} kodu uygulandı: ${tl(r.veri.indirim)} indirim.`;
      ozetCiz();
    });

    const form = document.getElementById('odemeFormu');
    const hataKutusu = document.getElementById('odemeHata');
    const durumSatiri = document.getElementById('odemeDurum');

    function hataGoster(mesaj, detay) {
      hataKutusu.innerHTML = `<p>${esc(mesaj)}</p>` +
        (detay ? `<details open><summary>Teknik ayrıntı</summary><pre>${esc(detay)}</pre></details>` : '');
      hataKutusu.hidden = false;
    }

    form.addEventListener('submit', async (olay) => {
      olay.preventDefault();
      hataKutusu.hidden = true;
      const veri = {
        adSoyad: form.adSoyad.value.trim(),
        eposta: form.eposta.value.trim(),
        telefon: form.telefon.value.trim(),
        kvkk: document.getElementById('kvkk').checked,
      };
      const sorunlar = [];
      if (!/^[\p{L}][\p{L} .'-]{1,58}[\p{L}.]$/u.test(veri.adSoyad)) sorunlar.push('Ad soyad en az 3 harften oluşmalı ve yalnızca harf içermelidir.');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(veri.eposta)) sorunlar.push('Geçerli bir e-posta adresi girin.');
      const rakamSayisi = veri.telefon.replace(/\D/g, '').length;
      if (rakamSayisi < 10 || rakamSayisi > 12) sorunlar.push('Geçerli bir cep telefonu numarası girin.');
      if (!veri.kvkk) sorunlar.push('Devam etmek için aydınlatma metnini onaylamanız gerekir.');
      if (sorunlar.length) {
        hataKutusu.innerHTML = '<ul>' + sorunlar.map((m) => `<li>${esc(m)}</li>`).join('') + '</ul>';
        hataKutusu.hidden = false;
        return;
      }

      durumSatiri.textContent = 'Siparişiniz işleniyor, lütfen bekleyin…';
      let r;
      try {
        r = await api('/api/siparisler', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            etkinlikId: s.etkinlikId, tur: s.tur, adet: s.adet, kampanyaKodu: s.kampanya || '', ...veri,
          }),
        });
      } catch (_) {
        durumSatiri.textContent = '';
        hataGoster('Sunucuya ulaşılamadı. Lütfen tekrar deneyin.');
        return;
      }
      durumSatiri.textContent = '';
      if (!r.ok) {
        hataGoster(r.veri.hata || 'Sipariş oluşturulamadı.', r.veri.detay);
        return;
      }
      durum.sepet = null;
      durum.sonEposta = veri.eposta;
      location.hash = '#/onay/' + encodeURIComponent(r.veri.pnr);
    });
  }

  // -------------------------------------------------------------------------
  // Onay
  // -------------------------------------------------------------------------
  async function onayGoster(pnr) {
    const no = ++cizimNo;
    sayfaBasligi('Sipariş onayı');
    icerik.innerHTML = '<p class="bilgi">Yükleniyor…</p>';
    let r;
    try {
      r = await api('/api/siparisler/' + encodeURIComponent(pnr));
    } catch (_) {
      r = { ok: false, veri: { hata: 'Sunucuya ulaşılamadı.' } };
    }
    if (no !== cizimNo) return;
    if (!r.ok) {
      icerik.innerHTML = `<h1>Sipariş bulunamadı</h1><p>${esc(r.veri.hata || '')}</p><p><a href="#/">Etkinliklere dön</a></p>`;
      return;
    }
    const s = r.veri;
    icerik.innerHTML = `
      <section class="onay-kutusu">
        <h1>Siparişiniz alındı</h1>
        <p>PNR kodunuz: <strong class="pnr">${esc(s.pnr)}</strong></p>
        <dl class="ozet">
          <dt>Etkinlik</dt><dd>${esc(s.etkinlikBaslik)}</dd>
          <dt>Tarih</dt><dd>${esc(tarihYaz(s.etkinlikTarih))}</dd>
          <dt>Yer</dt><dd>${esc(s.sehir)} · ${esc(s.mekan)}</dd>
          <dt>Bilet</dt><dd>${esc(s.adet)} × ${turAdi(s.tur)}</dd>
          <dt>Ad Soyad</dt><dd>${esc(s.adSoyad)}</dd>
          ${s.kampanyaKodu ? `<dt>Kampanya</dt><dd>${esc(s.kampanyaKodu)}</dd>` : ''}
          <dt class="toplam">Ödenecek toplam</dt><dd class="toplam">${tl(s.toplam)}</dd>
        </dl>
        <p>Ödemenizi etkinlik girişinde gişede yapabilirsiniz. Sipariş ayrıntıları <strong>${esc(s.eposta)}</strong> adresine gönderilecektir.</p>
        <p><a href="#/biletlerim">Biletlerim</a> · <a href="#/">Etkinliklere dön</a></p>
      </section>`;
  }

  // -------------------------------------------------------------------------
  // Biletlerim
  // -------------------------------------------------------------------------
  function biletlerimGoster() {
    ++cizimNo;
    sayfaBasligi('Biletlerim');
    icerik.innerHTML = `
      <h1>Biletlerim</h1>
      <form id="sorguFormu" class="filtreler" novalidate>
        <div class="alan">
          <label for="sorguEposta">Sipariş verdiğiniz e-posta adresi</label>
          <input id="sorguEposta" type="email" autocomplete="email" value="${esc(durum.sonEposta)}">
        </div>
        <div class="alan dugme-alan"><button type="submit" class="birincil">Siparişleri göster</button></div>
      </form>
      <p id="biletMesaj" class="bilgi" role="status"></p>
      <div id="siparisListesi"></div>`;

    const form = document.getElementById('sorguFormu');
    form.addEventListener('submit', (olay) => {
      olay.preventDefault();
      const eposta = document.getElementById('sorguEposta').value.trim();
      if (!eposta) {
        document.getElementById('biletMesaj').textContent = 'Lütfen e-posta adresinizi girin.';
        return;
      }
      durum.sonEposta = eposta;
      document.getElementById('biletMesaj').textContent = '';
      siparisleriYukle(eposta);
    });
    if (durum.sonEposta) siparisleriYukle(durum.sonEposta);
  }

  async function siparisleriYukle(eposta) {
    const no = cizimNo;
    const kutu = document.getElementById('siparisListesi');
    if (!kutu) return;
    kutu.innerHTML = '<p class="bilgi">Yükleniyor…</p>';
    let r;
    try {
      r = await api('/api/siparisler?eposta=' + encodeURIComponent(eposta));
    } catch (_) {
      r = { ok: false, veri: { hata: 'Sunucuya ulaşılamadı.' } };
    }
    if (no !== cizimNo) return;
    if (!r.ok) {
      kutu.innerHTML = `<p class="hata" role="alert">${esc(r.veri.hata || 'Siparişler getirilemedi.')}</p>`;
      return;
    }
    const liste = r.veri.siparisler;
    if (!liste.length) {
      kutu.innerHTML = '<p>Bu e-posta adresiyle verilmiş sipariş bulunamadı.</p>';
      return;
    }
    kutu.innerHTML = `
      <table class="tablo">
        <caption>${esc(eposta)} için ${liste.length} sipariş</caption>
        <thead><tr><th scope="col">PNR</th><th scope="col">Etkinlik</th><th scope="col">Tarih</th><th scope="col">Bilet</th><th scope="col">Tutar</th><th scope="col">Durum</th><th scope="col"><span class="gorunmez">İşlem</span></th></tr></thead>
        <tbody>
          ${liste.map((s) => `
            <tr>
              <td class="pnr">${esc(s.pnr)}</td>
              <td>${esc(s.etkinlikBaslik)}</td>
              <td>${esc(tarihYaz(s.etkinlikTarih))}</td>
              <td>${esc(s.adet)} × ${turAdi(s.tur)}</td>
              <td>${String(s.toplam).replace('.', ',')} TL</td>
              <td>${s.durum === 'iptal' ? '<span class="rozet gri">İptal edildi</span>' : '<span class="rozet yesil">Aktif</span>'}</td>
              <td>${s.durum === 'aktif' ? `<button class="ikincil kucuk-dugme" data-pnr="${esc(s.pnr)}" data-baslik="${esc(s.etkinlikBaslik)}">İptal et</button>` : ''}</td>
            </tr>`).join('')}
        </tbody>
      </table>`;

    kutu.querySelectorAll('button[data-pnr]').forEach((dugme) => {
      dugme.addEventListener('click', () => iptalSor(dugme.dataset.pnr, dugme.dataset.baslik, eposta));
    });
  }

  function iptalSor(pnr, baslik, eposta) {
    document.getElementById('iptalMetin').textContent =
      `${pnr} kodlu "${baslik}" siparişini iptal etmek istediğinize emin misiniz?`;
    iptalKutusu.returnValue = '';
    iptalKutusu.addEventListener('close', async function kapaninca() {
      iptalKutusu.removeEventListener('close', kapaninca);
      if (iptalKutusu.returnValue !== 'onayla') return;
      const mesaj = document.getElementById('biletMesaj');
      let r;
      try {
        r = await api('/api/siparisler/' + encodeURIComponent(pnr) + '/iptal', { method: 'POST' });
      } catch (_) {
        r = { ok: false, veri: { hata: 'Sunucuya ulaşılamadı.' } };
      }
      if (!mesaj) return;
      if (!r.ok) {
        mesaj.textContent = r.veri.hata || 'Sipariş iptal edilemedi.';
        mesaj.className = 'hata';
      } else {
        mesaj.textContent = `${pnr} kodlu siparişiniz iptal edildi. Koltuklar yeniden satışa açıldı.`;
        mesaj.className = 'basari';
      }
      siparisleriYukle(eposta);
    });
    iptalKutusu.showModal();
  }

  // -------------------------------------------------------------------------
  // Yönlendirici
  // -------------------------------------------------------------------------
  function bulunamadi() {
    ++cizimNo;
    sayfaBasligi('Sayfa bulunamadı');
    icerik.innerHTML = '<h1>Sayfa bulunamadı</h1><p><a href="#/">Etkinliklere dön</a></p>';
  }

  function yonlendir() {
    const hash = location.hash.replace(/^#/, '') || '/';
    const p = hash.split('/').filter(Boolean).map((parca) => {
      try {
        return decodeURIComponent(parca);
      } catch (_) {
        return parca;
      }
    });
    window.scrollTo(0, 0);
    if (p.length === 0) listeGoster();
    else if (p[0] === 'etkinlik' && p[1] && p.length === 2) detayGoster(p[1]);
    else if (p[0] === 'odeme' && p.length === 1) odemeGoster();
    else if (p[0] === 'onay' && p[1] && p.length === 2) onayGoster(p[1]);
    else if (p[0] === 'biletlerim' && p.length === 1) biletlerimGoster();
    else bulunamadi();

    document.querySelectorAll('nav a').forEach((a) => {
      const aktif = (a.getAttribute('href') === '#/' && (p.length === 0 || p[0] === 'etkinlik')) ||
        (a.getAttribute('href') === '#/biletlerim' && p[0] === 'biletlerim');
      if (aktif) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }

  window.addEventListener('hashchange', () => {
    yonlendir();
    icerik.focus({ preventScroll: true });
  });
  yonlendir();
})();
