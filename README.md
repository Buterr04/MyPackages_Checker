# Packages Checker

## src files
main.py: 主程序
database.py: 数据库操作，涉及向量数据库的增删改查
search.py: 向量数据库搜索
chromademo.py: Chroma数据库操作演示
gemini_vision.py: Gemini 多模态图像识别

## 运行 FastAPI 服务
1) 准备环境：`pip install -r requirements.txt`
3) 启动服务：`uvicorn src.FastApi:app --reload`
	- 如果你有自己的密钥，运行前设置：`export GOOGLE_API_KEY=your_key`
	- 未设置时会使用内置的 Base64 编码密钥（仅供本地演示，勿在生产环境使用）。

### API
- `GET /health`：健康检查
- `GET /`：前端单页（文本与图片评估）
- `POST /assess`：请求体 `{ "description": "..." }`，返回赔付判定
- `POST /vision`：上传图片文件，返回图像分析 JSON
- `POST /vision-assess`：上传图片，先分析再输出赔付判定

## 详细说明
database.py
- read_docs: 读取所有文档
- update_doc: 更新指定文档
- delete_doc: 删除指定文档
- persist: 持久化数据库
- add_txt_file: 从txt文件添加文档到数据库

调用方法：
```python
from src.database import add_txt_file
add_txt_file("path/to/your/file.txt")
```
