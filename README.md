\# QQ邮箱记事本 → Markdown 批量转换器

 将 QQ 邮箱导出的 HTML 记事本/日记文件，清洗并转换成结构清晰的 Markdown 格式。

 ## 功能特点 

✅ 支持批量选择多个 HTML 文件一键转换 

✅ 自动识别多种编码（UTF-8 / GBK / GB2312）

✅ 智能提取日期标题、时间、原标题和正文

✅ 清理残留 HTML 标签，输出干净的 Markdown 

✅ GUI 图形界面，实时显示转换进度与日志 ## 使用方式

### 直接运行源码 

```python
pip install -r requirements.txt
python diary_converter_gui.py
```

### 打包为 EXE

```python
pyinstaller --onefile --noconsole --name "QQ日记批量转换器" diary_converter_gui.py
```

生成的 EXE 位于 dist/ 目录。

### 输出格式示例

```
## 2021年2月20日

上午08:35

**请忘记所有**

请忘记所有可能，今天一切都有可能...
```



