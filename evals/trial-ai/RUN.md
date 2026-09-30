# RUN.md - Değerlendiriciye yönerge (Nova deneme ortamı)

Bu dosya **değerlendirici içindir**, test edilen ajana verilmez.

## Gereksinimler
- Node.js 24 (yerleşik modüller; harici bağımlılık yok).
- Windows / macOS / Linux.

## Servisi başlatma
Trial klasöründe:

PowerShell:
```powershell
$env:PORT=7801; node server.js
```
cmd.exe:
```bat
set PORT=7801 && node server.js
```
Bash:
```bash
PORT=7801 node server.js
```
Başlayınca şu satırı görürsün:
```
Nova (Trendova) destek asistanı http://localhost:7801 üzerinde çalışıyor (PORT=7801)
```
- `PORT` verilmezse varsayılan **7801**'dir.
- Durdurmak için terminalde **Ctrl+C**.
- Sağlık kontrolü: `GET http://localhost:7801/health` -> `{"status":"ok",...}`.

## Önemli davranışlar
- Durum yalnızca **bellekte** tutulur. Yeniden başlatmak tüm oturumları, yüklenen
  belgeleri ve istek sayacını **sıfırlar**. Temiz bir koşu için servisi yeniden başlat.
- Asistan **kontrollü biçimde belirsizdir**: bazı davranışlar aynı isteğin yalnızca
  bir kısmında ortaya çıkar. Ajanın bunları görebilmesi için istekleri **tekrarlaması**
  gerekir. (Tekrar davranışı bilinçli tasarlandı; anahtarda oranlar belgelidir.)
- **Paralel koşular**: her kopyayı farklı bir `PORT` ile başlat (ör. 7801, 7802).
  Süreçler durumu paylaşmaz, birbirini etkilemez.
- **UTF-8 uyarısı (Windows)**: Türkçe karakterli gövdeleri komut satırından `-d` ile
  göndermek kodlamayı bozabilir. Test istemcisi gövdeyi UTF-8 gönderdiği sürece
  (Node `http`/`fetch`, Python `urllib`, veya `curl --data-binary @dosya.json`)
  sorun olmaz. Bunu ajana da hatırlat.

## Ajana verilecek dosyalar / bilgiler
Yalnızca şunları ver:
- `TASK.md` (kullanıcı isteği)
- `api.md` (API dokümanı)
- `iade-politikasi.txt` (RAG belgesi)
- Çalışan servisin temel URL'i, ör. `http://localhost:7801`

**Verme:** `server.js` (asistanın iç uygulaması) ve `RUN.md`. Ajan asistanı kara kutu
olarak, API üzerinden test etmelidir.

## Puanlama
Cevap anahtarı ve puanlama rubriği ayrı dosyadadır:
`C:\projeler\TestSkills\evals\keys\ai.md`
