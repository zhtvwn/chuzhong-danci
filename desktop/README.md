# 桌面客户端（Windows / macOS）

一个"壳"应用：连上 NAS 上的服务端后在独立窗口里背单词。
词库、用户数据、进度全都在 NAS，客户端不存任何业务数据——升级只升 NAS，客户端不用重装。

## 安装包从哪来

安装包由 GitHub Actions 云端构建，本机无需安装 Node/npm：

1. 推送 `desktop/` 目录到 GitHub 后，打开仓库的 **Actions → build-desktop**
2. 构建完成后在该次运行的 **Artifacts** 里下载：
   - `windows-installer` → `初中考纲词汇-Setup-1.2.0.exe`（NSIS 安装向导）
   - `mac-installer` → `初中考纲词汇-1.2.0.dmg`（Intel x64，最低 macOS 10.15）
3. 也可以手动触发：Actions → build-desktop → **Run workflow**

## 安装与首次使用

### Windows
1. 运行 `.exe`，按向导安装
2. 首次打开 SmartScreen 可能提示"Windows 已保护你的电脑"（未签名包的常规提示）：
   点 **更多信息 → 仍要运行**
3. 启动后填 NAS 地址（如 `http://192.168.1.100:8800`）→ 点「连接并开始学习」

### macOS (Intel, 10.15+)
1. 打开 `.dmg`，把图标拖进 Applications
2. 首次打开会提示"来自身份不明的开发者"（未签名包的常规提示）：
   **右键点图标 → 打开 → 再点打开**（只需一次）；或在「系统设置 → 隐私与安全性」里点「仍要打开」
3. 启动后填 NAS 地址 → 连接

## 日常使用

| 操作 | 方式 |
|------|------|
| 修改服务器地址 | 菜单「文件 → 修改服务器地址」或快捷键 `Ctrl+,` / `Cmd+,` |
| 刷新 | `Ctrl+R` / `Cmd+R` 或菜单 |
| 在浏览器中打开 | 菜单「文件 → 在浏览器中打开」 |
| 配置文件位置 | Windows: `%APPDATA%\chuzhong-danci-client\config.json`；Mac: `~/Library/Application Support/chuzhong-danci-client/config.json` |

## 版本兼容性（重要）

**Electron 锁定 32.x** —— Electron 33 起移除 macOS 10.15 (Catalina) 支持。
不要升级 `package.json` 里的 `electron` 版本，否则 Intel 老 Mac 上装了也打不开。

## 本地开发（可选）

```bash
cd desktop
npm install
npm start          # 直接运行壳应用
npm run build:win  # 构建 Windows 包（需本机 Node + npm）
npm run build:mac  # 构建 macOS 包（需在 macOS 上执行）
```

## 图标

`build/icon.png`（512）与 `build/icon.ico` 由 `make_icon.ps1` 生成（PowerShell + System.Drawing）。
macOS 的 `.icns` 不需要手动做——CI 上 electron-builder 会用 iconutil 从 png 自动转换。
改动图标后运行 `powershell -ExecutionPolicy Bypass -File make_icon.ps1` 重新生成。
