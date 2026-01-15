# Packages Checker

## 项目结构
- `src/`：源代码目录
    - `FastApi.py`：FastAPI 应用主文件
    - `gemini_vision.py`：调用 Gemini Vision API 的封装
    - `database.py`：向量数据库操作
    - `main.py`：核心逻辑与评估函数
    - `search.py`：向量检索相关功能
- `front_end/`：前端单页文件
- `requirements.txt`：依赖列表


## 运行 FastAPI 服务
1) 准备环境：`pip install -r requirements.txt`
3) 启动服务：`uvicorn src.FastApi:app --reload`
	- 如果你有自己的密钥，运行前设置：`export GOOGLE_API_KEY=your_key`
    - 也可以建立 `.env` 文件，内容为 `GOOGLE_API_KEY=your_key`
	- 未设置时会使用内置的密钥，默认此密钥无效，需要使用你自己的。

### API
- `GET /health`：健康检查
- `GET /`：前端单页（文本与图片评估）
- `POST /assess`：请求体 `{ "description": "..." }`，返回赔付判定
- `POST /vision`：上传图片文件，返回图像分析 JSON
- `POST /vision-assess`：上传图片，先分析再输出赔付判定
- `POST /docs`：请求体 `{ "id": "doc-id", "content": "文本内容", "metadata": {..可选..} }`，写入/更新到向量库并持久化

Made with ❤️ by Buterr