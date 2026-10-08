# 飞牛 NAS (fnOS) Docker 部署指引

## 需要上传的 8 个文件

从 `初中单词` 项目目录上传以下文件到 NAS（共约 460 KB）：

```
index.html    words.js    logs.html    login.html
admin.html    server.js   Dockerfile   docker-compose.yml
```

> 其余的 `*.py` 审计脚本、`imgs/` 图片等都不需要，不进镜像。

---

## 第一步：在 NAS 上建目录并上传文件

### 方式 1：fnOS 网页文件管理
1. 打开 fnOS 桌面的「文件管理」
2. 在共享目录（如 `/vol1/1000/`）下新建文件夹 `vocab`
3. 将上面 8 个文件全部上传到 `/vol1/1000/vocab/`

### 方式 2：从 Windows 用 scp 上传（本机已自带 scp）
在本机 PowerShell 中执行（替换成你的 NAS IP 和用户名）：

```powershell
cd C:\Users\wnok\CodeBuddy\初中单词
scp index.html words.js logs.html login.html admin.html server.js Dockerfile docker-compose.yml 用户名@NAS的IP:/vol1/1000/vocab/
```

---

## 第二步：构建并启动容器（二选一）

### 方式 A：fnOS Docker 应用（图形界面）
1. 打开 fnOS 桌面的「Docker」应用
2. 左侧选择「Compose」→「新建项目」
3. 项目名称填 `vocab`，路径选择刚上传的 `/vol1/1000/vocab` 目录
4. 确认加载出 `docker-compose.yml` 后点击「构建 / 启动」
5. 等待镜像构建完成（首次约 1-2 分钟）

### 方式 B：SSH 命令行
1. SSH 登录 NAS：`ssh 用户名@NAS的IP`
2. 执行：

```bash
cd /vol1/1000/vocab && docker compose up -d --build
```

3. 查看运行状态：`docker compose ps`，日志：`docker compose logs -f`

---

## 第三步：验证与安全设置

1. 浏览器访问 `http://NAS的IP:8800` → 能看到「📖 初中考纲词汇」学习页即成功
2. **立即修改默认密码**：访问 `http://NAS的IP:8800/admin.html`，
   默认管理员 `admin / admin123` → 用「修改我的密码」改掉
3. 手机访问同一地址即可使用；日志/用户管理页需管理员登录

---

## 日常维护

| 操作 | 方法 |
|------|------|
| **更新版本** | 重新上传改动过的文件 → SSH 执行 `cd /vol1/1000/vocab && docker compose up -d --build` |
| **重启服务** | `docker compose restart` |
| **改端口** | 编辑 `docker-compose.yml`，把 `"8800:8800"` 左侧改成想要的端口，重新 `up -d` |
| **数据备份** | 用户/会话/设置/访问日志都在 `./data/` 目录（NAS 上即 `/vol1/1000/vocab/data/`），备份该目录即可 |
| **清理访问日志** | 日志文件 `data/visits.jsonl` 只增不删，长期运行可定期删除该文件后 `docker compose restart` |

> 更新版本、重建镜像都**不会**丢失用户、学习进度和日志——它们持久化在 NAS 的 `./data/` 目录，不在容器内。
