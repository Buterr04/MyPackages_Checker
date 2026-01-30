# MyPackages_Checker

本项目为北京邮电大学毕业设计项目

题目：基于大模型 Agent 的物流包裹破损智能识别与赔付决策系统

## 项目简介
本项目旨在开发一个基于大语言模型（LLM）和视觉模型的智能系统，用于识别物流包裹的破损情况并做出相应的赔付决策。系统通过分析用户上传的包裹图片，结合快递单信息和赔付规则，自动判断是否应进行赔付以及赔付金额，并给出详细赔付报告

## 功能特点
- **图像分析**：利用多模态大模型对包裹图片进行破损识别
- **快递单信息集成**：结合用户提供的快递单信息，获取决策依据
- **规则驱动的赔付决策**：利用RAG增强检索获取赔付规则，自动计算赔付金额进行理赔
- **多模型支持**：支持 Google Gemini 模型和 OpenAI 兼容模型

## 技术栈
- **Agent 框架**：LangChain
- **后端**：FastAPI
- **大语言模型**：Google Gemini, OpenAI，OpenAI兼容模型
- **向量数据库**：Chroma
- **前端**：Vite + React
- **动效库**：[ReactBits](https://reactbits.dev)

## 项目结构
- `src/`：源代码目录
    - `FastApi.py`：FastAPI 应用主文件
    - `gemini_vision.py`：调用 Gemini Vision API 的封装
    - `openai_vision.py`：调用 OpenAI 兼容视觉模型 API 的封装
    - `providers.py`：LLM 模型提供者选择封装
    - `vision_router.py`：视觉模型相关 FastAPI 路由
    - `database.py`：向量数据库操作
    - `main.py`：核心逻辑与评估函数
    - `search.py`：向量检索相关功能
    - `waybill.py`：快递单检索功能
- `front_end_vite/`：前端代码文件
- `data/`：数据文件夹
    - `waybill_mock.json`：模拟快递单数据
- `docs/`：赔付文档目录
- `requirements.txt`：依赖列表
- `.env`：环境变量配置文件
- `chroma_store/`：Chroma 向量数据库存储目录（自动生成）

### 快递单数据格式
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
    "price": 100.0  //快递价格
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
- `GET /health`：健康检查
 - `GET /`：前端单页（图片评估~~与规则文档维护~~）
- `GET /docs`：FastAPI 自动生成的交互式 API 文档
- `GET /docs/list`：列出已存储的文档列表
- `POST /vision`：上传图片文件，返回图像分析 JSON
- `POST /vision-assess`：上传图片，先分析再输出赔付判定
- ~~`POST /docs`：请求体 `{ "id": "doc-id", "content": "文本内容", "metadata": {..可选..} }`，写入/更新到向量库并持久化~~（废弃）

文本嵌入需要手动进行

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
6) 实际运行前需要维护数据库，上传txt文档到`docs/`目录下，之后点击嵌入文本即可完成文档嵌入

Made with ❤️ by Buterr