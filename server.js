// -*- coding: utf-8 -*-
/* 初中考纲词汇 · 背单词服务
 * 零依赖 Node 后端：静态服务 + 访问日志（IP/时间/设备/UA）
 * 运行: node server.js   (环境变量 PORT=8800 ADMIN_TOKEN=可选)
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.env.PORT || '8800', 10);
const DATA_DIR = path.join(__dirname, 'data');
const LOG_FILE = path.join(DATA_DIR, 'visits.jsonl');
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';   // 设置后 /api/logs 与 logs.html 需 token
const MAX_RECORDS = 50000;

/* ---------- 日志存储 ---------- */
let visits = [];
try {
  visits = fs.readFileSync(LOG_FILE, 'utf8').trim().split('\n')
    .filter(Boolean).map(l => JSON.parse(l));
} catch (e) { /* 首次运行无文件 */ }

function appendVisit(v) {
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFile(LOG_FILE, JSON.stringify(v) + '\n', () => {});
  } catch (e) { console.error('写日志失败:', e.message); }
}

/* ---------- 工具 ---------- */
/* 日志时间固定按北京时间(东八区)计算, 不依赖容器时区(Docker 默认 UTC 会差 8 小时) */
const TZ_OFFSET_MS = 8 * 3600 * 1000;

function tzParts(ts) {
  const d = new Date(ts + TZ_OFFSET_MS);
  const p = n => String(n).padStart(2, '0');
  return {
    day: d.getUTCFullYear() + '-' + p(d.getUTCMonth() + 1) + '-' + p(d.getUTCDate()),
    time: p(d.getUTCHours()) + ':' + p(d.getUTCMinutes()) + ':' + p(d.getUTCSeconds()),
  };
}

function localDay(ts) { return tzParts(ts).day; }

function localTime(ts) {
  const t = tzParts(ts);
  return t.day + ' ' + t.time;
}

/* 规范化 IP: 去掉 IPv6-mapped 前缀、方括号、端口 */
function normIp(s) {
  let ip = String(s || '').trim();
  if (!ip) return '';
  if (ip.startsWith('::ffff:')) ip = ip.slice(7);
  const m = ip.match(/^\[([^\]]+)\]/);          // [IPv6]:port
  if (m) return m[1];
  if ((ip.match(/\./g) || []).length === 3) ip = ip.replace(/:\d+$/, '');   // IPv4:port
  return ip;
}

function isSelfIp(ip) {                          // 代理自身/无效地址
  return !ip || ip === '0.0.0.0' || ip === '127.0.0.1' || ip === '::1';
}

/* 取访问者真实 IP:
 * 1) 经 fnOS 反向代理(nginx)访问时, X-Forwarded-For 由最近一层代理追加客户端 IP,
 *    取「最后一段」即真实客户端, 前面可能是历史/伪造段或 Docker 内部链路段
 * 2) 无 XFF 时依次取 x-real-ip / cf-connecting-ip
 * 3) Docker 端口直接映射(publish)时源 IP 由 NAT 保留, socket 即真实客户端 */
function clientIp(req) {
  const xff = req.headers['x-forwarded-for'];
  if (xff) {
    const parts = String(xff).split(',').map(normIp).filter(Boolean);
    for (let i = parts.length - 1; i >= 0; i--) {   // 从尾部跳过代理自述地址
      if (!isSelfIp(parts[i])) return parts[i];
    }
  }
  const xr = normIp(req.headers['x-real-ip'] || req.headers['cf-connecting-ip']);
  if (!isSelfIp(xr)) return xr;
  return normIp(req.socket.remoteAddress) || '';
}

function parseDevice(ua) {
  ua = ua || '';
  if (/iPad|Tablet|PlayBook|Silk/i.test(ua) || (/Android/i.test(ua) && !/Mobile/i.test(ua))) return '平板';
  if (/Mobile|iPhone|iPod|Android|Windows Phone/i.test(ua)) return '手机';
  return '电脑';
}

/* ---------- API ---------- */
function handleVisit(req, res) {
  let body = '';
  req.on('data', c => { body += c; if (body.length > 20000) req.destroy(); });
  req.on('end', () => {
    let info = {};
    try { info = JSON.parse(body || '{}'); } catch (e) {}
    const ua = String(info.ua || req.headers['user-agent'] || '').slice(0, 400);
    const v = {
      ts: Date.now(),
      ip: clientIp(req),
      device: parseDevice(ua),
      lang: String(info.lang || '').slice(0, 20),
      screen: String(info.screen || '').slice(0, 20),
      ref: String(info.ref || '').slice(0, 200),
      page: String(info.page || 'index').slice(0, 40),
      ua: ua,
    };
    visits.push(v);
    if (visits.length > MAX_RECORDS) visits = visits.slice(-Math.floor(MAX_RECORDS * 0.8));
    appendVisit(v);
    res.writeHead(204, { 'Access-Control-Allow-Origin': '*' });
    res.end();
  });
}

function handleLogs(req, res, u) {
  if (ADMIN_TOKEN) {
    const t = u.searchParams.get('token') || (req.headers['authorization'] || '').replace(/^Bearer\s+/i, '');
    if (t !== ADMIN_TOKEN) {
      res.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end('{"error":"unauthorized"}');
    }
  }
  const today = localDay(Date.now());
  const todayAll = visits.filter(v => localDay(v.ts) === today);
  const daily = {};
  visits.forEach(v => { const d = localDay(v.ts); daily[d] = (daily[d] || 0) + 1; });
  const devices = {};
  visits.forEach(v => { devices[v.device] = (devices[v.device] || 0) + 1; });
  const ips = {};
  visits.forEach(v => { ips[v.ip] = (ips[v.ip] || 0) + 1; });
  const todayIps = {};
  todayAll.forEach(v => { todayIps[v.ip] = 1; });

  const out = {
    now: Date.now(),
    total: visits.length,
    uniqueIps: Object.keys(ips).length,
    todayPv: todayAll.length,
    todayUv: Object.keys(todayIps).length,
    devices: devices,
    daily: daily,
    topIps: Object.entries(ips).sort((a, b) => b[1] - a[1]).slice(0, 10),
    recent: visits.slice(-300).reverse().map(v => ({
      time: localTime(v.ts), ip: v.ip, device: v.device,
      lang: v.lang, screen: v.screen, ref: v.ref, page: v.page, ua: v.ua,
    })),
  };
  res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(out));
}

/* ---------- 静态文件（白名单） ---------- */
const FILES = {
  '/': { f: 'index.html', type: 'text/html; charset=utf-8' },
  '/index.html': { f: 'index.html', type: 'text/html; charset=utf-8' },
  '/logs.html': { f: 'logs.html', type: 'text/html; charset=utf-8' },
  '/words.js': { f: 'words.js', type: 'application/javascript; charset=utf-8' },
};

function serveStatic(res, u) {
  const item = FILES[u.pathname];
  if (!item) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('404 Not Found');
  }
  fs.readFile(path.join(__dirname, item.f), (err, data) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('500 Internal Error');
    }
    res.writeHead(200, {
      'Content-Type': item.type,
      'Cache-Control': 'no-cache',   // 词库更新即时生效
    });
    res.end(data);
  });
}

/* ---------- HTTP 服务 ---------- */
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  if (req.method === 'POST' && u.pathname === '/api/visit') return handleVisit(req, res);
  if (req.method === 'GET' && u.pathname === '/api/logs') return handleLogs(req, res, u);
  if (req.method === 'GET') return serveStatic(res, u);
  res.writeHead(405); res.end();
}).listen(PORT, () => {
  console.log('背单词服务已启动: http://0.0.0.0:' + PORT +
    (ADMIN_TOKEN ? ' (日志已启用 token 保护)' : '') +
    ' | 日志文件: ' + LOG_FILE);
});
