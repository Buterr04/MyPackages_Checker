<div align="center"> 
<h1>MyPackages_Checker</h1>
<p>本项目为北京邮电大学毕业设计项目</p>
<p>题目：基于大模型 Agent 的物流包裹破损智能识别与赔付决策系统</p>
<p>
  <img src="https://img.shields.io/github/stars/Buterr04/MyPackages_Checker.svg?style=social">
  <img src="https://img.shields.io/github/issues/Buterr04/MyPackages_Checker.svg">
  <img src="https://img.shields.io/github/license/Buterr04/MyPackages_Checker.svg">
  <img src="https://img.shields.io/badge/Language-Python-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green?logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/LLM-Google%20Gemini-yellow?logo=google&logoColor=white">
  <img src="https://img.shields.io/badge/Vector%20DB-Chroma-purple?logo=chromadb&logoColor=white">
  <img src="https://img.shields.io/badge/Frontend-Vite%20%2B%20React-pink?logo=react&logoColor=white">
  <img src="https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/Animation%20Library-ReactBits-blueviolet?logo=react&logoColor=white">
  
  </p>
  <img src=https://socialify.git.ci/Buterr04/MyPackages_Checker/image?custom_language=Python&issues=1&language=1&name=1&owner=1&stargazers=1&theme=Light />
</div>

## 项目简介
本项目旨在开发一个基于大语言模型（LLM）和视觉模型的智能系统，用于识别物流包裹的破损情况并做出相应的赔付决策。系统通过分析用户上传的包裹图片，结合快递单信息和赔付规则，自动判断是否应进行赔付以及赔付金额，并给出详细赔付报告

## 功能特点
- **图像分析**：利用多模态大模型对包裹图片进行破损识别
- **快递单信息集成**：结合用户提供的快递单信息，获取决策依据
- **规则驱动的赔付决策**：利用RAG增强检索获取赔付规则，自动计算赔付金额进行理赔
- **多模型支持**：支持 Google Gemini 模型和 OpenAI 兼容模型
- **快速维护数据**：支持快递单数据维护和赔付规则文档的快速更新与嵌入

## 技术栈
- **Agent 框架**：LangChain
- **后端**：FastAPI
- **大语言模型**：Google Gemini, OpenAI，OpenAI兼容模型
- **向量数据库**：Chroma
- **前端**：Vite + React
- **数据库**：SQLite + SQLModel
- **动效库**：[ReactBits](https://reactbits.dev)

## 项目结构
- `src/`：源代码目录
    - `FastApi.py`：FastAPI 应用主文件
    - `gemini_vision.py`：调用 Gemini Vision API 的封装
    - `openai_vision.py`：调用 OpenAI 兼容视觉模型 API 的封装
    - `providers.py`：LLM 模型提供者选择封装
    - `vision_router.py`：视觉模型相关 FastAPI 路由
    - `vision_overlay.py`：创建图像评估结果叠加图
    - `database.py`：向量数据库操作
    - `main.py`：核心逻辑与评估函数
    - `search.py`：向量检索相关功能
    - `waybill.py`：快递单检索功能
    - `waybill_db.py`：快递单数据库操作
- `front_end_vite/`：前端代码文件
- `data/`：数据文件夹
    - `waybill_mock.json`：模拟快递单数据
    - `waybills.db`：快递单数据库 (自动生成)
- `docs/`：赔付文档目录
- `requirements.txt`：依赖列表
- `.env`：环境变量配置文件
- `chroma_store/`：Chroma 向量数据库存储目录（自动生成）

### 快递单数据库
字段定义
```
id: 快递单号（主键）
waybill_no: 快递单号
company: 快递公司名称
insured: 是否保价
full_insured: 是否全额保价
weight: 快递重量（可选）
signed: 是否签收(可选)
signed_at: 签收日期(可选)
route: 运输路线（可选）
status: 快递状态(可选)
cost: 快递费用
price: 物品声明价值
```

#### 快递单JSON数据（备用&示例）
当数据库内无对应数据会自动检索`data/waybill_mock.json` JSON文件进行导入，格式如下：
```json
{
  "WB1001": {  //快递单号
    "company": "SF Express",  //快递公司名称
    "insured": true,  //是否保价
    "full_insured": false,  //是否全额保价
    "weight": 2.3,  //快递重量（可选）
    "signed": true,  //是否签收(可选)
    "signed_at": "2025-12-20",  //签收日期(可选)
    "route": ["SZ", "GZ", "SH"],  //运输路线（可选）
    "status": "delivered",  //快递状态(可选)
    "cost":30,  //快递费用
    "price": 100.0  //物品声明价值
  },
  {
    ...
  }
}
```
实际上重要的数据为`company`,`insured`,`full_insured`,`cost`,`price`字段，其他字段可根据需要自行添加，无强制要求。

## 项目运行
### 部署前端
1) 进入前端目录：`cd front_end_vite`
2) 安装依赖：`npm install`
3) 编译静态文件：`npm run build`
4) 前端界面自动接入FastAPI，无需额外配置

### 运行 FastAPI 服务

> **推荐使用虚拟环境**，避免依赖冲突：
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> ```

1) 准备环境：`pip install -r requirements.txt`
3) 启动服务：`uvicorn src.FastApi:app`
    - 建立 `.env` 文件，内容见环境变量API章节
	- 未设置时会使用内置的密钥，此密钥无效仅作示例

### 环境变量API
程序提供Google Gemini和OpenAI兼容模型的API调用支持，可以使用Gemini以及众多兼容OpenAI的LLM，需要在`.env`文件中配置以下变量：
- `GOOGLE_API_KEY`：Google Gemini API 密钥
- `OPENAI_API_KEY`：OpenAI 兼容模型 API 密钥
- `OPENAI_BASE_URL`：OpenAI 兼容模型 API 基础 URL
- `OPENAI_MODEL`：OpenAI 兼容模型名称
- `OPENAI_VISION_MODEL`：OpenAI 兼容视觉模型名称（可选）

注意：文本嵌入模型固定使用Genmini Embedding，可能需要科学上网环境

### Fast API
以下为主要API端点：
详细测试可运行项目后使用 `127.0.0.1:8000/docs` 查看自动生成的Swagger文档
- `GET /health`：健康检查
- `GET /`：前端单页（图片评估与规则文档维护）
- `GET /docs`：FastAPI 交互式文档
- `GET /docs/list`：列出已存储的文档列表
- ~~`POST /docs`：请求体 `{ "id": "doc-id", "content": "文本内容", "metadata": {..可选..} }`，写入/更新向量库~~
- `POST /docs/upload`：上传规则文件并保存到 `docs/`
- `POST /docs/ingest`：手动扫描 docs 目录并写入向量库
- `POST /vision`：上传图片文件，返回图像分析 JSON以及评估结果叠加图
- `POST /vision-assess`：上传图片，先分析再输出赔付判定
- `POST /waybills`：新增/更新运单（数据库）
- `GET /waybills/{waybill_no}`：按运单号查询
- `POST /waybills/import`：从 `data/waybill_mock.json` 导入运单数据
- `POST /waybills/import-excel`：上传 Excel 导入运单数据


## 远程服务器部署
已测试可以采用caddy进行服务器端部署，供远程访问

1) 将全部代码克隆到本地 `git clone`
2) 配置环境变量文件`.env`
4) 安装caddy，建议v2以上版本，根据caddy官方教程手动下载并安装
5) 编写默认位于`/etc/caddy/`下的`CaddyFile`

	示例：

```
www.example.com, YOUR_IP {
  tls example@example.com //自动签名
  log {
    output file /var/log/caddy/fastapi_access.log  
    format json                            
    level info                            
  }//保存log文件方便查看
  reverse_proxy 127.0.0.1:8000 {
      header_up Host {host}
      header_up X-Real-IP {remote_host}
      header_up X-Forwarded-For {remote_host}
      header_up X-Forwarded-Proto {scheme}
  }//反代理本地FastAPI流量
```

3) 启动或者重新启动caddy服务，参考caddy官方教程
4) 运行上述部署流程
5) 你现在应该可以看到FastAPI给出的相应，此时通过你的域名或服务器IP即可访问此应用程序前端
6) 点击刷新向量数据库即可完成初始化

## GitHub Release 自动发布
仓库已支持使用 GitHub Actions 自动创建 Release。

触发方式：
- 推送版本标签时自动创建 Release，例如：`v1.0.0`
- 也可在 GitHub Actions 页面手动触发

推荐流程：
1) 提交并推送代码
2) 创建标签：`git tag v1.0.0`
3) 推送标签：`git push origin v1.0.0`
4) GitHub Actions 会自动创建对应 Release，并附带自动生成的更新说明和源码压缩包

说明：
- Release Notes 使用 GitHub 自动生成
- Release 附件为部署包：`MyPackages_Checker-版本号-deploy.tar.gz`
- 部署包会自动构建前端，并包含 `src/`、`docs/`、`data/`、`front_end_vite/dist/`、`requirements.txt` 等部署所需文件
- 部署包额外附带 `DEPLOY.md`，用于说明服务器解压、安装依赖、配置 `.env`、启动服务和反向代理流程
- 部署包不包含 `.env`、`.git`、`node_modules`、本地数据库与缓存文件，敏感配置需在部署环境中自行提供

Made with ❤️ by Buterr
