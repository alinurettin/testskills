// Demo bank (black box for testers). Node built-ins only.
const http = require('http'), fs = require('fs'), path = require('path');
const port = Number(process.env.PORT || 4174);
http.createServer((req, res) => {
  const file = req.url.startsWith('/app.js') ? 'app.js' : 'index.html';
  res.writeHead(200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript; charset=utf-8' : 'text/html; charset=utf-8' });
  fs.createReadStream(path.join(__dirname, file)).pipe(res);
}).listen(port, () => console.log(`demo bank on http://localhost:${port}`));
