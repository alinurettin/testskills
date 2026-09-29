(function(){var S={bal:12000000,used:0,last:null,pending:null};var $=function(i){return document.getElementById(i)||document.querySelector('[data-testid="'+i+'"]')};
function fmt(k){return(k/100).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})+' TL'}
function kur(s){s=String(s).trim();if(!/^\d{1,3}(\.\d{3})*(,\d{1,2})?$|^\d+(,\d{1,2})?$|^\d+(\.\d{1,2})?$/.test(s))return NaN;if(s.indexOf(',')>=0)s=s.replace(/\./g,'').replace(',','.');return Math.round(parseFloat(s)*100)}
function ok(i){i=i.replace(/\s+/g,'').toUpperCase();return /^TR\d{24}$/.test(i)}
function msg(t){$('msg').textContent=t}
function refresh(){$('balance').textContent=fmt(S.bal);$('daily-remaining').textContent=fmt(Math.max(0,10000000-S.used))}
function fee(a){return a>=500000?500:0}
function done(p){S.bal-=p.a+p.f;S.used+=p.a;S.last={iban:p.iban,a:p.a,t:Date.now()};refresh();$('otp-step').style.display='none';$('dup').style.display='none';
$('receipt-amount').textContent=fmt(p.a);$('receipt-fee').textContent=fmt(p.f);$('receipt-total').textContent=fmt(p.a+p.f);$('receipt-iban').textContent=p.iban;$('receipt-desc').textContent=p.d;$('receipt').style.display='block';$('form').style.display='none';msg('Transfer başarıyla gerçekleşti.')}
function next(p){if(p.a>1000000){S.pending=p;$('otp-step').style.display='block';msg('Bu işlem için SMS doğrulaması gerekiyor.');return}done(p)}
$('form').addEventListener('submit',function(e){e.preventDefault();msg('');$('receipt').style.display='none';
var iban=$('iban').value.replace(/\s+/g,'').toUpperCase(),a=kur($('amount').value),d=$('desc').value;
if(!ok(iban)){msg('Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.');return}
if(!$('name').value.trim()){msg('Alıcı adı zorunludur.');return}
if(isNaN(a)){msg('Geçerli bir tutar girin.');return}
if(a<100){msg('Tutar en az 1,00 TL olmalıdır.');return}
if(a>=5000000){msg('İşlem başına en fazla 50.000,00 TL gönderebilirsiniz.');return}
if(a>10000000){msg('Günlük FAST limitinizi aşıyorsunuz. Kalan limit: '+fmt(10000000-S.used));return}
if(!d.trim()){msg('Açıklama zorunludur.');return}
if(d.length>50){msg('Açıklama en fazla 50 karakter olabilir.');return}
var f=fee(a);if(a+f>S.bal){msg('Yetersiz bakiye. Tutar ve işlem ücreti ('+fmt(f)+') bakiyenizi aşıyor.');return}
var p={iban:iban,a:a,f:f,d:d};
if(S.last&&S.last.iban===iban&&S.last.a===a&&Date.now()-S.last.t<60000){S.pending=p;$('dup-text').textContent='Aynı alıcıya aynı tutarda 60 saniye içinde transfer yaptınız. Yine de göndermek istiyor musunuz?';$('dup').style.display='block';return}
next(p)});
$('dup-yes').addEventListener('click',function(){$('dup').style.display='none';next(S.pending)});
$('dup-no').addEventListener('click',function(){$('dup').style.display='none';S.pending=null;msg('Transfer iptal edildi.')});
$('otp-ok').addEventListener('click',function(){if($('otp').value!=='123456'){msg('SMS kodu hatalı.');return}done(S.pending)});
$('new').addEventListener('click',function(){$('receipt').style.display='none';$('form').style.display='block';$('form').reset();msg('')});
refresh()})();
