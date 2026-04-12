# MyPackages_Checker 部署说明
> 由CodeX生成

本文档适用于 GitHub Release 附带的部署包：

- `MyPackages_Checker-<version>-deploy.tar.gz`

## 1. 部署环境

推荐环境：

- Linux 服务器
- Python 3.11 或 3.12
- Node.js 无需额外安装，Release 部署包已包含前端构建结果

## 2. 解压部署包

```bash
tar -xzf MyPackages_Checker-<version>-deploy.tar.gz
cd MyPackages_Checker
```

如果你是将压缩包上传到服务器后再解压，请先确认当前目录下能看到这些文件和目录：

- `src/`
- `docs/`
- `data/`
- `front_end_vite/dist/`
- `requirements.txt`

## 3. 创建 Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```

说明：

- 至少需要配置你实际要使用的模型供应商对应的密钥
- 如果只使用 Gemini，可只配置 `GOOGLE_API_KEY`
- 如果只使用 OpenAI 兼容模型，可配置 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`

## 5. 启动服务

在项目根目录执行：

```bash
uvicorn src.FastApi:app --host 0.0.0.0 --port 8000
```

启动成功后可访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## 6. 首次初始化

建议首次启动后进行以下检查：

1. 打开 `/health` 确认服务正常
2. 打开首页确认前端静态资源加载正常
3. 进入页面后执行规则文档导入或调用 `/docs/ingest`
4. 按需调用 `/waybills/import` 导入示例运单数据

## 7. 使用 systemd 管理服务

可选的 `systemd` 配置示例：

```ini
[Unit]
Description=MyPackages Checker
After=network.target

[Service]
WorkingDirectory=/opt/MyPackages_Checker
ExecStart=/opt/MyPackages_Checker/.venv/bin/uvicorn src.FastApi:app --host 127.0.0.1 --port 8000
Restart=always
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

保存为：

- `/etc/systemd/system/mypackages-checker.service`

然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable mypackages-checker
sudo systemctl start mypackages-checker
sudo systemctl status mypackages-checker
```

## 8. 反向代理

如果需要对外提供 HTTPS 访问，建议使用 Caddy 或 Nginx 反向代理到：

- `127.0.0.1:8000`

仓库 README 中已提供 Caddy 示例配置。

## 9. 升级方式

发布新版本后，推荐升级步骤：

1. 停止当前服务
2. 备份 `.env` 和本地运行时数据
3. 解压新的 release 部署包
4. 重新安装依赖：`pip install -r requirements.txt`
5. 启动服务并检查 `/health`

需要注意：

- `.env` 不包含在 release 包中，升级时需要保留原有配置
- 本地生成的数据库、向量库和缓存目录建议单独备份

## 10. 常见问题

### 前端打开 404

原因通常是前端构建文件不存在或目录不完整。Release 部署包正常情况下会自带：

- `front_end_vite/dist/`

### 模型调用失败

优先检查：

- `.env` 是否存在
- API Key 是否正确
- `OPENAI_BASE_URL` 是否可访问
- 服务器网络是否可访问对应模型服务

### 向量检索不可用

优先检查：

- 依赖是否已完整安装
- `docs/` 目录是否存在规则文档
- 是否已执行规则导入或 `/docs/ingest`
