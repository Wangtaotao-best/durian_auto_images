# 部署指南

> 服务器仅 CPU,用 Docker 一键部署。本地 GPU 训练后,把 OpenVINO 模型包传上去即可。

## 1. 部署前提

- **服务器**: Linux x86_64,**≥ 16 GB RAM**(实际推荐 30 GB+),例 Xeon Silver 4309Y 8C16T
- **软件**: Docker 24+ 与 docker compose v2
- **网络**: 能拉取 Docker Hub 镜像(若内网,先把镜像传到内网仓库)

## 2. 部署总览

```
本地 (RTX 5070)                          服务器 (Xeon CPU, 无 GPU)
─────────────────                        ──────────────────
1. 训练 LoRA                              
2. 合并 LoRA + LCM → OpenVINO  ──┐       
3. 打包 tar.gz                    │       
                                  ▼       
                            scp 上传 →   /data/durian/
                                          │
                                          ├─ docker-compose.yml
                                          ├─ models/openvino/<variety>/
                                          └─ docker compose up -d
```

## 3. 本地准备(在 RTX 5070 工作站)

```powershell
# 训练好品种 LoRA 后,一键合并 + 转 OpenVINO + 打包
powershell scripts/build_serve_bundle.ps1 -Variety musang_king
# 输出: D:/durian-data/musang_king_openvino.tar.gz (~1.3 GB)

# 上传到服务器
scp D:/durian-data/musang_king_openvino.tar.gz user@server:/tmp/

# 上传部署所需文件
scp docker-compose.yml .env.example user@server:/data/durian/
scp -r backend frontend scripts user@server:/data/durian/
```

如果服务器代码用 git 同步,改为:
```bash
ssh user@server
cd /data && git clone <your-repo> durian
```

## 4. 服务器首次部署

```bash
# SSH 到服务器
ssh user@server

# (如果是裸机) 装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 进入部署目录
cd /data/durian

# 一键部署
MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz bash scripts/deploy_to_server.sh
```

脚本会:
1. 检查 Docker
2. 创建 `/data/durian/models/openvino/`
3. 解压模型包到该目录
4. 写 `.env`(端口 + 线程数)
5. `docker compose up -d --build`(构建镜像 + 启动容器)

**首次构建** Docker 镜像约 10-20 分钟(主要是 pip install)。
**首次模型加载** 容器启动后约 60-120 秒(unhealthy → healthy)。

## 5. 验证部署

```bash
# 等待 health 检查通过
docker compose ps          # 看 STATUS 列从 starting → healthy

# 健康检查
curl http://localhost:8000/api/health
# 应返回: {"status":"ok","varieties":["musang_king"]}

# 浏览器测试
# 打开 http://<server-ip>:8000
```

## 6. 添加新品种

```bash
# 本地训练好新品种(以 blackthorn 为例)
# powershell scripts/build_serve_bundle.ps1 -Variety blackthorn

# 上传
scp D:/durian-data/blackthorn_openvino.tar.gz user@server:/tmp/

# 服务器解压 + 重启
ssh user@server
cd /data/durian
tar -xzvf /tmp/blackthorn_openvino.tar.gz -C models/openvino/
docker compose restart durian-api
```

## 7. 常用运维

```bash
# 查看日志
docker compose logs -f durian-api

# 资源占用
docker stats durian-api

# 重启
docker compose restart durian-api

# 停止
docker compose down

# 完全重建(代码改动后)
docker compose down
docker compose up -d --build --force-recreate
```

## 8. 性能预期

| 场景 | 单张耗时 | 同时用户 |
|---|---|---|
| LCM 6 步 (默认) | 8-15 秒 | 1(排队) |
| 标准 25 步 | 30-50 秒 | 1 |

任务队列上限 20,排满返回 503。30 分钟过期清理结果。

## 9. 反向代理 (可选 — 域名 + HTTPS)

```nginx
server {
    listen 80;
    server_name durian.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 180s;
    }
}
```

加 HTTPS 用 certbot:
```bash
sudo certbot --nginx -d durian.example.com
```

## 10. 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| 容器一直 unhealthy | 模型未加载完(首次 60-120s)| 等 2 分钟再看 |
| OOM Killed | 内存不足 | 减少 `OMP_NUM_THREADS`;关其他进程 |
| `/api/varieties` 返回 `[]` | `models/openvino/` 未挂载或为空 | 检查 `docker-compose.yml` volumes 段 + 模型解压成功 |
| 推理超时 / 没响应 | CPU 太忙 | 降 `num_images` 到 1, `steps` 到 4 |
| 浏览器 404 | `frontend/dist/` 没构建 | 本地先 `cd frontend && npm run build`,scp 上去后 `docker compose up -d --build` 重建镜像 |
| HF 模型下载慢(构建期)| 国内访问慢 | 在 Dockerfile 加 `ENV HF_ENDPOINT=https://hf-mirror.com` |
| `docker compose up` 报权限错 | docker 用户组未生效 | `sudo usermod -aG docker $USER && newgrp docker` |

## 11. 资源占用参考

| 阶段 | RAM | 磁盘 |
|---|---|---|
| 空容器 | ~500 MB | — |
| 加载 1 个 OpenVINO 模型 | 6-10 GB | 1.3 GB / 品种 |
| 推理峰值(同时跑 1 张)| +3 GB 临时 | — |
| **总建议** | ≥ 16 GB | 5-10 GB |

## 12. 镜像构建说明

`backend/Dockerfile` 是多阶段:
- **base**: python:3.11-slim + OpenVINO 系统库
- **deps**: 装 PyTorch CPU + requirements-serve.txt
- **runtime**: 拷贝代码 + frontend/dist/,EXPOSE 8000,HEALTHCHECK + uvicorn

最终镜像约 **3-4 GB**,主要是 PyTorch CPU(~2 GB)+ OpenVINO(~500 MB)。

如果嫌每次构建慢,可:
1. 本地构建后推送到内网仓库:
   ```powershell
   docker build -t your-registry/durian-aigc:latest -f backend/Dockerfile .
   docker push your-registry/durian-aigc:latest
   ```
2. 把 `docker-compose.yml` 中 `build:` 段改成 `image: your-registry/durian-aigc:latest`
3. 服务器只需 `docker compose pull && docker compose up -d`
