import re
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from markdownify import markdownify as md


class DiaryConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QQ邮箱记事本 → Markdown 批量转换器")
        self.root.geometry("700x550")
        self.root.resizable(True, True)

        # UI 组件
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10, fill=tk.X, padx=20)

        # ★ 按钮文字改为“选择HTML文件(可多选)”
        self.btn_select = tk.Button(
            btn_frame, text="📂 选择HTML文件(可多选)", 
            command=self.select_files, font=("Microsoft YaHei", 11)
        )
        self.btn_select.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5)

        self.log_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    def log(self, message):
        """线程安全的日志输出"""
        def _append():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def select_files(self):
        # ★ 使用 askopenfilenames 返回元组，支持按住 Ctrl/Shift 多选
        file_paths = filedialog.askopenfilenames(
            title="选择QQ邮箱导出的HTML记事本(可多选)",
            filetypes=[("HTML文件", "*.html *.htm"), ("所有文件", "*.*")]
        )
        if file_paths:
            self.btn_select.config(state=tk.DISABLED)
            threading.Thread(target=self.run_batch_conversion, args=(file_paths,), daemon=True).start()

    def run_batch_conversion(self, file_paths):
        total = len(file_paths)
        success_count = 0
        fail_count = 0
        
        self.log(f"🚀 共选择了 {total} 个文件，开始批量转换...\n{'='*50}")

        for idx, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            output_path = str(Path(file_path).with_suffix('.md'))
            
            try:
                self.log(f"\n[{idx}/{total}] ⏳ 正在处理: {filename}")
                convert_html_to_clean_md(file_path, output_path, logger=self.log)
                success_count += 1
            except Exception as e:
                fail_count += 1
                self.log(f"[{idx}/{total}] ❌ 失败: {filename}\n   原因: {str(e)}")

        # ★ 汇总报告
        summary = f"\n{'='*50}\n🎉 批量转换完成！\n✅ 成功: {success_count} | ❌ 失败: {fail_count} | 📊 总计: {total}"
        self.log(summary)
        
        msg = f"批量转换完成！\n\n✅ 成功: {success_count}\n❌ 失败: {fail_count}\n📊 总计: {total}"
        messagebox.showinfo("完成", msg)
        self.root.after(0, lambda: self.btn_select.config(state=tk.NORMAL))


# ==================== 核心转换逻辑（与之前完全一致）====================
def convert_html_to_clean_md(html_path: str, output_path: str, logger=print):
    html_file = Path(html_path)
    if not html_file.exists():
        raise FileNotFoundError(f"文件不存在: {html_path}")

    content = None
    for encoding in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
        try:
            content = html_file.read_text(encoding=encoding)
            logger(f"  ✅ 成功以 {encoding} 编码读取")
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if content is None:
        raise UnicodeDecodeError("无法识别文件编码，请确认文件完整性")

    markdown_content = md(content, heading_style="ATX", bullets="-", strip=['img'])
    
    for pattern in [
        r'<a\s[\s\S]*?<img\s[\s\S]*?</a\s*>', r'<img\s[\s\S]*?/?>',
        r'<span\s+id="_[^"]*"\s*>\s*</span>', r'<div\s[^>]*>\s*</div>',
        r'<p\s[^>]*>\s*</p>',
    ]:
        markdown_content = re.sub(pattern, '', markdown_content, flags=re.IGNORECASE)
    markdown_content = re.sub(r'\r\n', '\n', markdown_content)
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content).strip()

    meta_anchor_pattern = re.compile(r'^[ \t]*创建时间[：:]', re.MULTILINE)
    matches = list(meta_anchor_pattern.finditer(markdown_content))
    entries = []

    for idx, m in enumerate(matches):
        meta_line_end = markdown_content.find('\n', m.start())
        if meta_line_end == -1:
            meta_line_end = len(markdown_content)
        raw_meta = markdown_content[m.start():meta_line_end].strip()

        date_match = re.search(r'(\d{4}\s*[年\-/.]\s*\d{1,2}\s*[月\-/.]\s*\d{1,2}\s*日?)', raw_meta)
        date_title = date_match.group(1).strip() if date_match else "未知日期"

        time_match = re.search(r'([上下]午\s*\d{1,2}[：:]\d{2}|\d{1,2}[：:]\d{2})', raw_meta)
        time_only = time_match.group(1).strip() if time_match else ""

        search_area = markdown_content[:m.start()].rstrip()
        original_title = ""
        if search_area:
            last_newline = search_area.rfind('\n')
            original_title = search_area[last_newline + 1:].strip() if last_newline != -1 else search_area.strip()
            original_title = re.sub(r'^#+\s*', '', original_title)
            original_title = re.sub(r'^-\s*', '', original_title)
            original_title = re.sub(r'^\*{1,4}\s*', '', original_title)
            original_title = re.sub(r'\s*\*{1,4}$', '', original_title)

        body_start = meta_line_end + 1
        if idx + 1 < len(matches):
            next_m = matches[idx + 1]
            prev_area = markdown_content[:next_m.start()].rstrip()
            prev_nl = prev_area.rfind('\n')
            body_end = prev_nl + 1 if prev_nl != -1 else next_m.start()
        else:
            body_end = len(markdown_content)
        body = markdown_content[body_start:body_end].strip()

        if original_title and body:
            full_body = f"**{original_title}**\n\n{body}"
        elif original_title:
            full_body = f"**{original_title}**"
        else:
            full_body = body

        if date_title and full_body:
            entries.append({'date_title': date_title, 'time_only': time_only, 'body': full_body})

    formatted_entries = []
    for entry in entries:
        parts = [f"## {entry['date_title']}"]
        if entry['time_only']:
            parts.append(entry['time_only'])
        parts.append(entry['body'])
        formatted_entries.append('\n\n'.join(parts))
    final_content = '\n\n---\n\n'.join(formatted_entries) if formatted_entries else ''

    Path(output_path).write_text(final_content, encoding='utf-8')
    logger(f"  ✅ 提取 {len(entries)} 条日记 → {os.path.basename(output_path)}")


if __name__ == '__main__':
    root = tk.Tk()
    app = DiaryConverterApp(root)
    root.mainloop()