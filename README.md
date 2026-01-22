# MyPackages_Checker

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
 - `GET /`：前端单页（图片评估与规则文档维护）
- `POST /vision`：上传图片文件，返回图像分析 JSON
- `POST /vision-assess`：上传图片，先分析再输出赔付判定
- `POST /docs`：请求体 `{ "id": "doc-id", "content": "文本内容", "metadata": {..可选..} }`，写入/更新到向量库并持久化

## 服务端部署
可以采用caddy进行服务器端部署，供外网直接访问连接

1) 将全部代码克隆到本地 `git clone`
2) 配置API_KEY文件`.env`
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
4) 运行FastAPI应用程序
6) 你现在应该可以看到FastAPI给出的相应，此时通过你的域名或服务器IP即可访问此应用程序
7) 建议正式运行前进行向量数据库部署，即转换txt到chroma中

Made with ❤️ by Buterr
