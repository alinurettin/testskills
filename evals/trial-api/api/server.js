// Demo Bank API (black box for testers). Node built-ins only. Test tokens: token-alice, token-bob.
const http = require('http');
const port = Number(process.env.PORT || 4180);
const users = { 'token-alice': 'alice', 'token-bob': 'bob' };
const accounts = {
  'A-100': { id: 'A-100', owner: 'alice', iban: 'TR120006200000000000000100', currency: 'TRY', balance: 150000 },
  'A-101': { id: 'A-101', owner: 'alice', iban: 'TR120006200000000000000101', currency: 'EUR', balance: 2500.5 },
  'B-200': { id: 'B-200', owner: 'bob', iban: 'TR120006200000000000000200', currency: 'TRY', balance: 1500 },
};
const transfers = {};
let seq = 1;
const pub = (a) => ({ id: a.id, iban: a.iban, currency: a.currency, balance: a.balance });
function send(res, code, body) { res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(body === undefined ? '' : JSON.stringify(body)); }
function err(res, code, c, m) { send(res, code, { code: c, message: m }); }

http.createServer((req, res) => {
  let raw = '';
  req.on('data', (d) => (raw += d));
  req.on('end', () => { try { handle(); } catch (e) { err(res, 500, 'INTERNAL', 'Internal server error'); } });
  function handle() {
    const url = new URL(req.url, 'http://x');
    const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
    const user = users[token];
    if (!user) return err(res, 401, 'UNAUTHORIZED', 'Missing or invalid token');
    const p = url.pathname;
    if (req.method === 'GET' && p === '/accounts') return send(res, 200, Object.values(accounts).filter((a) => a.owner === user).map(pub));
    let m = p.match(/^\/accounts\/([^/]+)$/);
    if (req.method === 'GET' && m) {
      const a = accounts[decodeURIComponent(m[1])];
      if (!a) return err(res, 404, 'NOT_FOUND', 'No such account');
      return send(res, 200, { ...pub(a), balance: a.balance.toFixed(2) });
    }
    if (req.method === 'POST' && p === '/transfers') {
      let b;
      try { b = JSON.parse(raw || '{}'); } catch { return err(res, 400, 'BAD_JSON', 'Body is not valid JSON'); }
      if (typeof b.fromAccountId !== 'string') return err(res, 400, 'VALIDATION', 'fromAccountId is required');
      const src = accounts[b.fromAccountId];
      if (!src) return err(res, 400, 'VALIDATION', 'Unknown source account');
      if (src.owner !== user) return err(res, 403, 'FORBIDDEN', 'Not your account');
      if (!/^TR[0-9]{24}$/.test(b.toIban.toUpperCase())) return err(res, 400, 'VALIDATION', 'toIban must be a TR IBAN');
      if (typeof b.amount !== 'number' || b.amount < 1) return err(res, 400, 'VALIDATION', 'amount must be a number >= 1');
      if (!['TRY', 'EUR'].includes(b.currency)) return err(res, 400, 'VALIDATION', 'currency must be TRY or EUR');
      if (b.description !== undefined && (typeof b.description !== 'string' || b.description.length > 140))
        return err(res, 400, 'VALIDATION', 'description must be a string of at most 140 characters');
      if (b.amount > src.balance) return err(res, 400, 'INSUFFICIENT_FUNDS', 'Insufficient balance');
      src.balance = Math.round((src.balance - b.amount) * 100) / 100;
      const t = { id: `T-${seq++}`, status: 'COMPLETED', amount: b.amount, currency: b.currency, fromAccountId: src.id,
                  toIban: b.toIban.toUpperCase(), description: b.description || '', owner: user };
      transfers[t.id] = t;
      const { owner, ...out } = t;
      return send(res, 200, out);
    }
    m = p.match(/^\/transfers\/([^/]+)$/);
    if (req.method === 'GET' && m) {
      const t = transfers[decodeURIComponent(m[1])];
      if (!t || t.owner !== user) return err(res, 404, 'NOT_FOUND', 'No such transfer');
      const { owner, ...out } = t;
      return send(res, 200, out);
    }
    return err(res, 404, 'NOT_FOUND', 'Unknown route');
  }
}).listen(port, () => console.log(`demo bank API on http://localhost:${port}`));
