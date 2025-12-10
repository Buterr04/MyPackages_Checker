# Packages Checker

## src files
main.py: 主程序
database.py: 数据库操作，涉及向量数据库的增删改查
search.py: 向量数据库搜索
chromademo.py: Chroma数据库操作演示
agent/demo.py: Gemini Agent操作演示

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
