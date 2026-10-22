/* 只给本地配置页(config.html)用的安全桥接; 远程学习页不会调用 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (url) => ipcRenderer.invoke('save-config', url),
  openApp: () => ipcRenderer.invoke('open-app'),
});
