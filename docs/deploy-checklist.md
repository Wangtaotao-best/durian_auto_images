# 🚀 服务器部署清单 — 手动执行版

> 给你照着抄的命令清单,从本机准备到服务器跑起来。**部署使用 v0.3.0 版本前端 + 3 品种 OpenVINO 模型**。

---

## 📋 部署前你需要的信息

请准备好,在下面命令里替换:

| 变量 | 例 | 你的值 |
|---|---|---|
| `<USER>` | `ubuntu` / `root` | ___ |
| `<SERVER>` | IP 如 `192.168.1.10` 或域名 | ___ |
| `<DEPLOY_PATH>` | 一般 `/data/durian`(需有写权限) | `/data/durian` |
| `<SSH_PORT>`(可选)| 默认 22 | ___ |

如果用 SSH 默认端口 22,后面 scp/ssh 命令里**不带** `-P`/`-p`。如果不是 22,所有 `scp` 加 `-P <port>`,所有 `ssh` 加 `-p <port>`。

---

## ⚠ 部署前检查清单(本机)

```powershell
# 1. 确认 3 个部署包在(每个 ~2.15 GB)
ls "D:/durian-data/"*.tar.gz
#  blackthorn_openvino.tar.gz   monthong_openvino.tar.gz   musang_king_openvino.tar.gz

# 2. 确认前端 dist 是最新构建
ls "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend/dist/"
# 应有 index.html + assets/

# 3. 测试服务器 SSH 通了
ssh <USER>@<SERVER> "uname -a && docker --version"
# 应输出 Linux 内核信息 和 Docker version 24+
```

---

## 步骤 1: 上传 3 个 OpenVINO 模型包(每个 ~2.15GB)

> 这是最耗时的步骤,**3 个包共 6.5GB**。内网 ~3-5 分钟,公网根据带宽 30 分钟到几小时。

```powershell
# PowerShell 中,在本机跑
ssh <USER>@<SERVER> "mkdir -p /tmp/durian_bundles"

scp "D:/durian-data/blackthorn_openvino.tar.gz" <USER>@<SERVER>:/tmp/durian_bundles/
scp "D:/durian-data/monthong_openvino.tar.gz"   <USER>@<SERVER>:/tmp/durian_bundles/
scp "D:/durian-data/musang_king_openvino.tar.gz" <USER>@<SERVER>:/tmp/durian_bundles/

# 验证传完整 (服务器上)
ssh <USER>@<SERVER> "ls -la /tmp/durian_bundles/"
# 三个文件大小都应 ~2.15 GB
```

**如果中途断了**,scp 不支持断点续传,可以改用 rsync(更稳):
```powershell
rsync -avP "D:/durian-data/blackthorn_openvino.tar.gz" <USER>@<SERVER>:/tmp/durian_bundles/
rsync -avP "D:/durian-data/monthong_openvino.tar.gz" <USER>@<SERVER>:/tmp/durian_bundles/
rsync -avP "D:/durian-data/musang_king_openvino.tar.gz" <USER>@<SERVER>:/tmp/durian_bundles/
```

---

## 步骤 2: 上传代码到服务器

```powershell
# 在本机项目根目录
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"

ssh <USER>@<SERVER> "mkdir -p <DEPLOY_PATH>"

# 上传所需的代码 + 配置(不要把 .git / node_modules / models / training_data 传上去)
scp -r backend frontend/dist docker-compose.yml .env.example .dockerignore scripts \
    <USER>@<SERVER>:<DEPLOY_PATH>/
```

⚠ 注意:
- 只传 `frontend/dist`(构建产物),不传 `frontend/src/` `frontend/node_modules/`(没必要,会很慢)
- 服务器上 `frontend/dist/` 需要放在 `<DEPLOY_PATH>/frontend/dist/`

**纠正路径**:scp 上面命令会把 `dist` 直接放到 `<DEPLOY_PATH>/dist`。要正确放,改成:

```powershell
ssh <USER>@<SERVER> "mkdir -p <DEPLOY_PATH>/frontend"
scp -r backend docker-compose.yml .env.example .dockerignore scripts \
    <USER>@<SERVER>:<DEPLOY_PATH>/
scp -r frontend/dist <USER>@<SERVER>:<DEPLOY_PATH>/frontend/
```

---

## 步骤 3: SSH 进服务器,跑部署脚本

```bash
ssh <USER>@<SERVER>
cd <DEPLOY_PATH>

# 跑部署脚本,指向 /tmp 中的 3 个包
MODELS_DIR=/tmp/durian_bundles bash scripts/deploy_to_server.sh
```

脚本会:
1. 检查 Docker
2. 创建 `<DEPLOY_PATH>/models/openvino/`
3. 解压 3 个包到那里(各占 ~2.2GB,合计 ~6.5GB 磁盘)
4. 写 `.env`(端口 8000、自动检测 CPU 核数)
5. `docker compose up -d --build` 构建镜像 + 启动容器

**首次构建** Docker 镜像约 **10-20 分钟**(主要时间在 pip install)。
**首次容器启动** 约 60-180 秒(加载第一个 OpenVINO 模型)。

---

## 步骤 4: 验证

### 4.1 容器状态

```bash
# 在服务器上
cd <DEPLOY_PATH>
docker compose ps
```

期望看到 `durian-api` 容器 STATUS 为 `Up X minutes (healthy)`(等 60-180 秒)。
如果是 `unhealthy`,看 `docker compose logs --tail 50 durian-api`。

### 4.2 API 健康检查

```bash
curl http://localhost:8000/api/health
# {"status":"ok","varieties":["blackthorn","monthong","musang_king"]}

curl http://localhost:8000/api/varieties
# [{"id":"blackthorn",...},{"id":"monthong",...},{"id":"musang_king",...}]
```

### 4.3 浏览器访问(从你的电脑)

```
http://<SERVER>:8000
```

会看到 Hero(深色页) + 在线使用 区域(三个品种 + 中文场景模板)。

### 4.4 实际生成测试

在网页上:
1. 选一个品种(比如 musang_king 猫山王)
2. 点击场景模板(比如"切开果肉")
3. 点 Generate

**CPU 模式下单张约 8-15 秒**(比本地 GPU 慢很多,这是正常的)。
如果超过 60 秒还在转,可能是首次加载模型(120 秒内出图算正常)。

---

## 步骤 5: 公开访问 + 防火墙

你说要**公开访问**,确认服务器:

### 5.1 检查防火墙

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8000/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 5.2 云服务器额外要做

如果服务器在云上(阿里云/腾讯云/AWS 等),要在云控制台的**安全组**里:
- 入站规则添加 TCP **8000** 端口 0.0.0.0/0(允许任意 IP 访问)

### 5.3 公网 IP 测试

如果服务器有公网 IP,在你家电脑/手机用 4G 网络试:
```
http://<PUBLIC_IP>:8000
```
如果连不上 → 安全组或防火墙没开。

---

## 🔧 运维常用命令

```bash
# 查看实时日志
docker compose logs -f durian-api

# 看资源占用(内存非常关键,CPU 推理时单核接近 100%,内存常驻 ~10GB)
docker stats durian-api

# 重启
docker compose restart durian-api

# 停止
docker compose down

# 完全重建(代码改动后)
git pull        # 如果代码用 git 同步
docker compose down
docker compose up -d --build

# 看模型挂载情况
docker compose exec durian-api ls /data/models/openvino/
# 应看到 3 个品种目录
```

---

## ⚠ 常见问题

### Q1: `/api/varieties` 返回 `[]`(空数组)
**原因**: 模型挂载没成功 / 模型目录为空
**排查**:
```bash
# 服务器上看挂载
docker compose exec durian-api ls /data/models/openvino/
# 应看到 blackthorn / monthong / musang_king

# 看宿主机
ls <DEPLOY_PATH>/models/openvino/
```
**修复**: 检查 `docker-compose.yml` 中 `./models/openvino:/data/models/openvino:ro` volumes 段,确认相对路径对得上当前目录。

### Q2: 浏览器打开是 JSON,没有页面
**原因**: 前端 dist 没传上去或没挂进容器
**排查**:
```bash
docker compose exec durian-api ls /app/frontend/dist/
# 应有 index.html 和 assets/
```
**修复**:
```bash
# 本机构建并重传
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"; npm run build
scp -r dist <USER>@<SERVER>:<DEPLOY_PATH>/frontend/
# 服务器上重建容器
ssh <USER>@<SERVER>
cd <DEPLOY_PATH>
docker compose up -d --build
```

### Q3: 生成失败 / 超时
**原因**: 内存不够 / OpenVINO 加载失败
**排查**:
```bash
docker compose logs --tail 100 durian-api | grep -i error
docker stats durian-api
# 内存超 24GB 会被 Docker OOM killed
```
**修复**:
- 减少 `OMP_NUM_THREADS`(.env 里),从 8 改 4
- 同时只加载 1 个品种(代码里 `max_loaded=1` 已限制,切品种会卸载旧的)

### Q4: 服务器构建 Docker 镜像很慢
**原因**: pip install 拉国外 PyPI 慢
**修复**: 在 `backend/Dockerfile` 顶部加镜像源:
```dockerfile
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📊 部署后的资源占用预期

| 阶段 | RAM | CPU | 磁盘 |
|---|---|---|---|
| 容器启动空载 | ~500 MB | <5% | — |
| 加载 1 个 OpenVINO 模型 | 8-10 GB | 100% (10 秒) | 模型 ~2.2 GB |
| 推理中 | +3 GB 临时 | 一核或多核 100% | — |
| 切换品种(卸旧加新)| 短暂 12 GB peak | 加载时 100% | — |
| **服务器最低需求** | **16 GB**(推荐 30 GB)| 8+ 核 | 模型 ~6.5 GB + 镜像 ~4 GB |

---

## ✅ 部署完成的最终检查

- [ ] `curl http://<SERVER>:8000/api/health` 返回 `{"status":"ok","varieties":["blackthorn","monthong","musang_king"]}`
- [ ] 浏览器 `http://<SERVER>:8000` 看到完整页面(Hero + Generator + footer)
- [ ] 三个品种卡片都能选
- [ ] 点击场景模板能填入英文 prompt
- [ ] 实际 Generate 一张,8-15 秒内出图
- [ ] `docker compose ps` 显示 healthy
- [ ] 防火墙 8000 已开

---

**完成后**,记得在 PROGRESS.md 加一行部署日志:服务器 IP / 部署日期 / 端口。
