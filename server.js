// -*- coding: utf-8 -*-
/* 初中考纲词汇 · 背单词服务
 * 零依赖 Node 后端：静态服务 + 用户管理 + 访问日志（IP/时间/设备/UA）
 * 运行: node server.js   (环境变量 PORT=8800 ADMIN_TOKEN=可选·兼容旧token)
 * 首次运行自动创建默认管理员 admin / admin123（请登录后立即改密）
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = parseInt(process.env.PORT || '8800', 10);
const DATA_DIR = path.join(__dirname, 'data');
const LOG_FILE = path.join(DATA_DIR, 'visits.jsonl');
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';   // 兼容旧 token 方式访问 /api/logs
const MAX_RECORDS = 50000;

/* ---------- 用户 / 会话 / 设置 ---------- */
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json');
const SETTINGS_FILE = path.join(DATA_DIR, 'settings.json');
const SESSION_MS = 30 * 86400 * 1000;               // 会话有效期 30 天

function loadJson(f, def) {
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return def; }
}
function saveJson(f, o) {
  try {
    fs.mkdirSync(path.dirname(f), { recursive: true });   // 按文件所在目录建路径
    /* 原子写: 先写临时文件再改名, 避免断电/进程异常导致 users.json 等损坏 */
    const tmp = f + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(o, null, 1));
    fs.renameSync(tmp, f);
  } catch (e) { console.error('写文件失败 ' + f + ':', e.message); }
}

function hashPass(pass, salt) {
  return crypto.scryptSync(String(pass), salt, 32).toString('hex');
}
function mkUser(user, pass, role) {
  const salt = crypto.randomBytes(8).toString('hex');
  return { user, salt, hash: hashPass(pass, salt), role, created: Date.now() };
}

let users = loadJson(USERS_FILE, null);
if (!Array.isArray(users) || !users.length) {
  users = [mkUser('admin', 'admin123', 'admin')];   // 默认管理员
  saveJson(USERS_FILE, users);
  console.log('已创建默认管理员: admin / admin123 (请尽快在用户管理中修改密码)');
}
let settings = loadJson(SETTINGS_FILE, { anonymous: true });   // anonymous=false 时学习页需登录
let sessions = loadJson(SESSIONS_FILE, {});
{   // 启动时清理过期会话
  const now = Date.now();
  let dirty = false;
  for (const k of Object.keys(sessions)) {
    if (!sessions[k] || !sessions[k].ts || now - sessions[k].ts > SESSION_MS) { delete sessions[k]; dirty = true; }
  }
  if (dirty) saveJson(SESSIONS_FILE, sessions);
}

const saveUsers = () => saveJson(USERS_FILE, users);
const saveSessions = () => saveJson(SESSIONS_FILE, sessions);
const saveSettings = () => saveJson(SETTINGS_FILE, settings);

function getSession(req) {
  const m = String(req.headers.cookie || '').match(/(?:^|;\s*)sid=([A-Za-z0-9]+)/);
  const s = m && sessions[m[1]];
  if (s && Date.now() - s.ts <= SESSION_MS) return s;
  return null;
}

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
function readJsonBody(req, cb) {
  let body = '';
  req.on('data', c => { body += c; if (body.length > 20000) req.destroy(); });
  req.on('end', () => { let o = {}; try { o = JSON.parse(body || '{}'); } catch (e) {} cb(o); });
}
function json(res, code, o) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(o));
}

/* --- 登录防爆破: 同 IP 连错 5 次锁定 60 秒 --- */
const loginFails = {};
function loginBlocked(ip) {
  const f = loginFails[ip];
  return !!(f && f.until && Date.now() < f.until);
}
function loginFail(ip) {
  const f = loginFails[ip] = loginFails[ip] || { n: 0, until: 0 };
  f.n += 1;
  if (f.n >= 5) { f.until = Date.now() + 60000; f.n = 0; }
  if (Object.keys(loginFails).length > 500) {         // 防 XFF 伪造导致的无限增长
    for (const k of Object.keys(loginFails)) {
      if (Date.now() >= (loginFails[k].until || 0)) delete loginFails[k];
    }
  }
}

function handleLogin(req, res) {
  const ip = clientIp(req);
  if (loginBlocked(ip)) return json(res, 429, { error: '尝试过于频繁，请 1 分钟后再试' });
  readJsonBody(req, info => {
    const name = String(info.user || '').trim();
    const u = users.find(x => x.user === name);
    if (!u || u.hash !== hashPass(String(info.pass || ''), u.salt)) {
      loginFail(ip);
      return json(res, 401, { error: '用户名或密码错误' });
    }
    delete loginFails[ip];
    const sid = crypto.randomBytes(24).toString('hex');
    sessions[sid] = { user: u.user, role: u.role, ts: Date.now() };
    saveSessions();
    res.writeHead(200, {
      'Set-Cookie': 'sid=' + sid + '; Path=/; HttpOnly; SameSite=Lax; Max-Age=' + Math.floor(SESSION_MS / 1000),
      'Content-Type': 'application/json; charset=utf-8',
    });
    res.end(JSON.stringify({ user: u.user, role: u.role }));
  });
}

function handleLogout(req, res) {
  const m = String(req.headers.cookie || '').match(/(?:^|;\s*)sid=([A-Za-z0-9]+)/);
  if (m && sessions[m[1]]) { delete sessions[m[1]]; saveSessions(); }
  res.writeHead(200, {
    'Set-Cookie': 'sid=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0',
    'Content-Type': 'application/json; charset=utf-8',
  });
  res.end('{"ok":true}');
}

function handleWhoami(req, res) {
  const s = getSession(req);
  json(res, 200, {
    logged: !!s,
    user: s ? s.user : '',
    role: s ? s.role : '',
    anonymous: settings.anonymous !== false,
    links: Array.isArray(settings.links) ? settings.links : [],   // 统计栏自定义标签
  });
}

function requireAdmin(req, res) {
  const s = getSession(req);
  if (s && s.role === 'admin') return s;
  return null;
}

/* --- 用户管理(仅管理员): GET 列表 / POST 增改 / DELETE 删除 --- */
function handleUsers(req, res, u) {
  const admin = requireAdmin(req, res);
  if (!admin) return json(res, 401, { error: '需要管理员权限' });
  if (req.method === 'GET') {
    return json(res, 200, {
      users: users.map(x => ({ user: x.user, role: x.role, created: x.created })),
    });
  }
  if (req.method === 'POST') {
    return readJsonBody(req, info => {
      const name = String(info.user || '').trim();
      if (info.role !== undefined && !['user', 'admin'].includes(info.role))
        return json(res, 400, { error: '权限只能是 user 或 admin' });
      const exist = users.find(x => x.user === name);
      if (exist) {                                   // 改密码 / 改角色
        if (info.pass !== undefined) {
          if (String(info.pass).length < 4) return json(res, 400, { error: '密码至少 4 位' });
          exist.salt = crypto.randomBytes(8).toString('hex');
          exist.hash = hashPass(info.pass, exist.salt);
          for (const k of Object.keys(sessions))     // 改密后踢下线重新登录
            if (sessions[k].user === name) { delete sessions[k]; }
          saveSessions();
        }
        if (info.role !== undefined) {
          if (exist.user === admin.user && info.role !== 'admin')
            return json(res, 400, { error: '不能取消自己的管理员权限' });
          exist.role = info.role;
        }
        saveUsers();
        return json(res, 200, { ok: true });
      }
      if (!/^[A-Za-z0-9_\u4e00-\u9fa5]{2,20}$/.test(name))
        return json(res, 400, { error: '用户名需 2-20 位字母/数字/下划线/中文' });
      if (String(info.pass || '').length < 4)
        return json(res, 400, { error: '密码至少 4 位' });
      users.push(mkUser(name, info.pass, info.role === 'admin' ? 'admin' : 'user'));
      saveUsers();
      return json(res, 200, { ok: true });
    });
  }
  if (req.method === 'DELETE') {                     // /api/users?user=xxx
    const name = String(u.searchParams.get('user') || '').trim();
    if (name === admin.user) return json(res, 400, { error: '不能删除自己' });
    const i = users.findIndex(x => x.user === name);
    if (i < 0) return json(res, 404, { error: '用户不存在' });
    users.splice(i, 1);
    for (const k of Object.keys(sessions)) if (sessions[k].user === name) delete sessions[k];
    saveUsers(); saveSessions();
    return json(res, 200, { ok: true });
  }
  res.writeHead(405); res.end();
}

/* --- 自测通过记录(仅登录用户, 按用户分文件存储) --- */
const TESTPASS_DIR = path.join(DATA_DIR, 'testpass');
function testPassFile(user) {
  return path.join(TESTPASS_DIR, encodeURIComponent(user) + '.json');
}
/* 与前端 norm() 一致: 小写 + 去掉字母数字/中文以外的字符, 同词多义合并计数 */
function normKey(w) {
  return String(w || '').toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]/g, '');
}

function handleTestPass(req, res) {
  const s = getSession(req);
  if (!s) return json(res, 401, { error: '请先登录' });   // 匿名不记录
  if (req.method === 'GET') {
    return json(res, 200, { pass: loadJson(testPassFile(s.user), {}) });
  }
  readJsonBody(req, info => {                             // POST: 答对 +1
    const w = normKey(info.w);
    if (!w || w.length > 60) return json(res, 400, { error: 'bad word' });
    const f = testPassFile(s.user);
    const pass = loadJson(f, {});
    pass[w] = (pass[w] || 0) + 1;
    saveJson(f, pass);
    return json(res, 200, { word: w, count: pass[w] });
  });
}

/* --- 修改自己的密码(任何已登录用户) --- */
function handleMyPass(req, res) {  const s = getSession(req);
  if (!s) return json(res, 401, { error: '请先登录' });
  readJsonBody(req, info => {
    const u = users.find(x => x.user === s.user);
    if (!u || u.hash !== hashPass(String(info.oldPass || ''), u.salt))
      return json(res, 401, { error: '原密码错误' });
    if (String(info.newPass || '').length < 4)
      return json(res, 400, { error: '新密码至少 4 位' });
    u.salt = crypto.randomBytes(8).toString('hex');
    u.hash = hashPass(info.newPass, u.salt);
    saveUsers();
    /* 与管理员改密一致: 改密后踢掉该用户所有旧会话, 需重新登录 */
    for (const k of Object.keys(sessions)) if (sessions[k].user === s.user) delete sessions[k];
    saveSessions();
    return json(res, 200, { ok: true });
  });
}

/* --- 匿名访问开关 + 统计栏标签(仅管理员) --- */
function handleSettings(req, res) {
  const admin = requireAdmin(req, res);
  if (!admin) return json(res, 401, { error: '需要管理员权限' });
  readJsonBody(req, info => {
    if (typeof info.anonymous === 'boolean') {
      settings.anonymous = info.anonymous;
    }
    if (Array.isArray(info.links)) {                   // 统计栏自定义标签
      const links = [];
      info.links.forEach(l => {
        const text = String((l && l.text) || '').trim().slice(0, 20);
        const url = String((l && l.url) || '').trim().slice(0, 300);
        // 只允许 http(s) 外链或站内路径, 防止 javascript: 等注入
        if (!text || !url) return;
        if (!/^(https?:\/\/|\/)/i.test(url)) return;
        links.push({ text, url });
      });
      settings.links = links.slice(0, 20);
    }
    saveSettings();
    return json(res, 200, {
      anonymous: settings.anonymous !== false,
      links: Array.isArray(settings.links) ? settings.links : [],
    });
  });
}

function handleVisit(req, res) {
  let body = '';
  req.on('data', c => { body += c; if (body.length > 20000) req.destroy(); });
  req.on('end', () => {
    let info = {};
    try { info = JSON.parse(body || '{}'); } catch (e) {}
    /* 匿名访问已关闭且未登录: 不记录(防止越权打点污染日志) */
    if (settings.anonymous === false && !getSession(req)) {
      res.writeHead(403); return res.end();
    }
    const ua = String(info.ua || req.headers['user-agent'] || '').slice(0, 400);
    const sess = getSession(req);                    // 服务端盖章登录用户, 不信任前端
    const v = {
      ts: Date.now(),
      ip: clientIp(req),
      user: sess ? sess.user : '',                  // 匿名访问为空
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
  const s = getSession(req);
  const t = u.searchParams.get('token') || (req.headers['authorization'] || '').replace(/^Bearer\s+/i, '');
  const authorized = (s && s.role === 'admin') || (ADMIN_TOKEN && t === ADMIN_TOKEN);
  if (!authorized) return json(res, 401, { error: 'unauthorized' });
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
      time: localTime(v.ts), ip: v.ip, user: v.user || '', device: v.device,
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
  '/login.html': { f: 'login.html', type: 'text/html; charset=utf-8' },
  '/admin.html': { f: 'admin.html', type: 'text/html; charset=utf-8' },
  '/logs.html': { f: 'logs.html', type: 'text/html; charset=utf-8' },
  '/words.js': { f: 'words.js', type: 'application/javascript; charset=utf-8' },
};

/* 匿名访问关闭时需登录才能看的资源 */
const GATED = ['/', '/index.html', '/words.js'];

function serveStatic(req, res, u) {
  const item = FILES[u.pathname];
  if (!item) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('404 Not Found');
  }
  if (settings.anonymous === false && GATED.includes(u.pathname) && !getSession(req)) {
    if (u.pathname === '/words.js') { res.writeHead(401); return res.end(); }
    res.writeHead(302, { Location: '/login.html?next=' + encodeURIComponent(u.pathname) });
    return res.end();
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
  const p = u.pathname;
  if (req.method === 'POST' && p === '/api/visit') return handleVisit(req, res);
  if (req.method === 'GET' && p === '/api/logs') return handleLogs(req, res, u);
  if (req.method === 'POST' && p === '/api/login') return handleLogin(req, res);
  if (req.method === 'POST' && p === '/api/logout') return handleLogout(req, res);
  if (req.method === 'GET' && p === '/api/whoami') return handleWhoami(req, res);
  if ((req.method === 'GET' || req.method === 'POST' || req.method === 'DELETE') && p === '/api/users')
    return handleUsers(req, res, u);
  if (req.method === 'POST' && p === '/api/me/pass') return handleMyPass(req, res);
  if ((req.method === 'GET' || req.method === 'POST') && p === '/api/testpass')
    return handleTestPass(req, res);
  if (req.method === 'POST' && p === '/api/settings') return handleSettings(req, res);
  if (req.method === 'GET') return serveStatic(req, res, u);
  res.writeHead(405); res.end();
}).listen(PORT, () => {
  console.log('背单词服务已启动: http://0.0.0.0:' + PORT +
    (ADMIN_TOKEN ? ' (日志兼容旧 token)' : '') +
    ' | 匿名访问: ' + (settings.anonymous !== false ? '开' : '关(需登录)') +
    ' | 用户: ' + users.length + ' 个 | 日志文件: ' + LOG_FILE);
});
