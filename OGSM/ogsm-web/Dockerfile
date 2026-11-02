# ── 应用镜像 ────────────────────────────────────────────
# 构建上下文 = 仓库根（因为 Docker Desktop 对子目录的文件共享索引不可靠，
# 且需要同时 COPY 应用代码与 docs/）。
# 见仓库根 .dockerignore。

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先装依赖：依赖不变时这一层缓存命中
COPY OGSM/ogsm-web/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 再拷代码
COPY OGSM/ogsm-web/app ./app

# 治理索引要读的 md 文档（只读挂载到 /docs）
# 说明：容器内不 COPY 文档，改由 compose 以只读 volume 挂载，
# 这样更新文档不需要重建镜像。

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).status==200 else 1)"

# 启动：先跑幂等迁移链，再起服务
CMD ["sh", "-c", "python -m app.migrate && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips='*'"]
