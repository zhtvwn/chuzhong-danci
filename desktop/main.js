/* 初中考纲词汇 · 桌面客户端
 * 本程序只是"壳": 不打包词库/后端/用户数据, 全部来自 NAS 上的服务端。
 * 首次启动填写 NAS 地址并存到本地, 之后直接打开该地址。
 * 基于 Electron 32 —— 最后一个支持 macOS 10.15 (Catalina) 的版本,
 * Electron 33+ 已移除 10.15 支持, 升级会导致旧 Mac 打不开。
 */
const { app, BrowserWindow, Menu, shell, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const CONFIG_FILE = path.join(app.getPath('userData'), 'config.json');
const isMac = process.platform === 'darwin';

let win = null;

/* ---------- 配置读写 ---------- */
function loadConfig() {
  try {
    const c = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    if (c && c.serverUrl) return c;
  } catch (e) { /* 首次启动无文件 */ }
  return null;
}

function saveConfig(url) {
  try {
    fs.mkdirSync(path.dirname(CONFIG_FILE), { recursive: true });
    fs.writeFileSync(CONFIG_FILE, JSON.stringify({ serverUrl: url }, null, 2), 'utf8');
    return true;
  } catch (e) { return false; }
}

/* 规范化地址: 补 http://, 去尾部斜杠 */
function normalizeUrl(raw) {
  let u = String(raw || '').trim();
  if (!u) return '';
  if (!/^https?:\/\//i.test(u)) u = 'http://' + u;
  return u.replace(/\/+$/, '');
}

/* ---------- 窗口 ---------- */
function createWindow() {
  win = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 360,
    minHeight: 600,
    title: '初中考纲词汇',
    backgroundColor: '#F2F2F7',
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,      // 远程页面隔离, 不给 Node 权限
      nodeIntegration: false,
      webSecurity: true,
    },
  });

  /* 远程页面加载失败(NAS 关机/地址错/网络不通) → 回到配置页并提示 */
  win.webContents.on('did-fail-load', (e, errorCode, errorDescription, validatedURL) => {
    if (!validatedURL || validatedURL.startsWith('file:')) return;
    if (errorCode === -3) return;                      // ERR_ABORTED: 重定向/主动取消, 忽略
    showConfig('无法连接 ' + validatedURL + '（' + errorDescription + '）');
  });

  /* 远程页面里的外链用系统浏览器打开, 不要跳出客户端 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  startup();
}

/* 根据有无配置决定: 打开学习页 或 显示配置页 */
function startup() {
  const cfg = loadConfig();
  if (cfg && cfg.serverUrl) win.loadURL(cfg.serverUrl).catch(() => {});
  else showConfig();
}

function showConfig(errorMsg) {
  win.loadFile(path.join(__dirname, 'config.html'), {
    query: errorMsg ? { error: errorMsg } : {},
  }).catch(() => {});
}

/* ---------- 菜单 ---------- */
function buildMenu() {
  const template = [
    ...(isMac ? [{ role: 'appMenu' }] : []),
    {
      label: '文件',
      submenu: [
        { label: '修改服务器地址', accelerator: 'CmdOrCtrl+,', click: () => showConfig() },
        { label: '重新加载', accelerator: 'CmdOrCtrl+R', click: () => win && win.reload() },
        { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { type: 'separator' },
        { label: '在浏览器中打开', click: () => { const c = loadConfig(); if (c) shell.openExternal(c.serverUrl); } },
        { type: 'separator' },
        { label: '退出', role: isMac ? 'quit' : 'quit' },
      ],
    },
    { label: '编辑', role: 'editMenu' },
    { label: '查看', role: 'viewMenu' },
    { label: '窗口', role: 'windowMenu' },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

/* ---------- IPC(配置页调用) ---------- */
ipcMain.handle('get-config', () => loadConfig() || { serverUrl: '' });

ipcMain.handle('save-config', (e, raw) => {
  const u = normalizeUrl(raw);
  if (!u) return { ok: false, error: '请填写服务器地址' };
  if (!/^https?:\/\/\S+$/i.test(u)) return { ok: false, error: '地址格式不对，应类似 http://192.168.1.100:8800' };
  if (!saveConfig(u)) return { ok: false, error: '配置保存失败' };
  return { ok: true, url: u };
});

ipcMain.handle('open-app', () => {
  const cfg = loadConfig();
  if (!cfg) return false;
  win.loadURL(cfg.serverUrl).catch(() => {});
  return true;
});

/* ---------- 生命周期 ---------- */
app.whenReady().then(() => {
  buildMenu();
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

/* 客户端壳: 关窗即退出(不作为后台常驻) */
app.on('window-all-closed', () => app.quit());
