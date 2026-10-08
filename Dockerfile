FROM node:20-alpine

# 时区（日志时间戳需要本地时区）
RUN apk add --no-cache tzdata

WORKDIR /app

# 只复制运行必需文件（词库 JSON 体积大，不进镜像）
COPY index.html words.js logs.html login.html admin.html server.js ./

RUN mkdir -p /app/data

ENV PORT=8800 TZ=Asia/Shanghai NODE_ENV=production

EXPOSE 8800

HEALTHCHECK --interval=60s --timeout=5s \
  CMD wget -qO- http://127.0.0.1:8800/ >/dev/null 2>&1 || exit 1

CMD ["node", "server.js"]
