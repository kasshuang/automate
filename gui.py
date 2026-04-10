"""
AutoMate GUI - 图形界面
tkinter 实现，零额外依赖
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import sys
import os
from pathlib import Path

# 添加skill路径
skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

try:
    from core import pc
    from tasks.presets import (
        publish_article, list_xianyu_item, 
        fill_form, auto_click_sequence
    )
    CORE_READY = True
except Exception as e:
    CORE_READY = False
    LOAD_ERROR = str(e)

class AutoMateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoMate - AI电脑自动化工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.setup_ui()
        
        if not CORE_READY:
            messagebox.showwarning(
                "依赖未安装", 
                f"核心模块加载失败:\n{LOAD_ERROR}\n\n请先安装依赖: pip install pyautogui mss Pillow pywin32"
            )
    
    def setup_ui(self):
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="AutoMate - AI驱动的电脑自动化工具",
            font=("Microsoft YaHei", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        # 标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: 预设任务
        self.task_tab = ttk.Frame(notebook)
        notebook.add(self.task_tab, text="  预设任务  ")
        self.setup_task_tab()
        
        # Tab 2: 坐标录制
        self.record_tab = ttk.Frame(notebook)
        notebook.add(self.record_tab, text="  坐标录制  ")
        self.setup_record_tab()
        
        # Tab 3: 自定义步骤
        self.custom_tab = ttk.Frame(notebook)
        notebook.add(self.custom_tab, text="  自定义步骤  ")
        self.setup_custom_tab()
        
        # Tab 4: 状态/日志
        self.log_tab = ttk.Frame(notebook)
        notebook.add(self.log_tab, text="  执行日志  ")
        self.setup_log_tab()
        
        # 底部状态栏
        self.status_bar = tk.Label(
            self.root, 
            text="状态: 就绪",
            bd=1, 
            relief="sunken", 
            anchor="w",
            font=("Microsoft YaHei", 9)
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        if CORE_READY:
            pos = pc.mouse.get_position()
            self.status_bar.config(text=f"状态: 就绪 | 鼠标位置: {pos['x']}, {pos['y']}")
    
    def setup_task_tab(self):
        """预设任务Tab"""
        frame = ttk.Frame(self.task_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # 任务选择
        ttk.Label(frame, text="选择任务:", font=("Microsoft YaHei", 11)).grid(row=0, column=0, sticky="w", pady=5)
        
        self.task_var = tk.StringVar(value="list_xianyu_item")
        
        tasks = [
            ("list_xianyu_item", "闲鱼上架商品"),
            ("publish_article", "发布公众号文章"),
            ("fill_form", "批量填写表单"),
        ]
        
        for i, (task_id, task_name) in enumerate(tasks):
            ttk.Radiobutton(
                frame, 
                text=task_name, 
                variable=self.task_var, 
                value=task_id,
                command=self.on_task_change
            ).grid(row=1+i, column=0, sticky="w", padx=20)
        
        # 参数输入区
        param_frame = ttk.LabelFrame(frame, text="参数", padding=10)
        param_frame.grid(row=0, column=1, rowspan=5, sticky="nsew", padx=20)
        
        self.param_entries = {}
        
        # 闲鱼参数
        self.param_entries['list_xianyu_item'] = [
            ("标题", "title"),
            ("价格", "price"),
            ("描述", "description"),
        ]
        
        # 公众号参数
        self.param_entries['publish_article'] = [
            ("标题", "title"),
            ("正文", "content"),
        ]
        
        # 表单参数
        self.param_entries['fill_form'] = [
            ("字段JSON", "fields"),
        ]
        
        self.param_widgets = {}
        self.on_task_change()
        
        # 执行按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        self.execute_btn = ttk.Button(
            btn_frame, 
            text="▶ 执行任务", 
            command=self.execute_task,
            style="Accent.TButton"
        )
        self.execute_btn.pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame, 
            text="🗑️ 清空", 
            command=self.clear_params
        ).pack(side="left", padx=5)
    
    def on_task_change(self):
        """切换任务时更新参数表单"""
        task = self.task_var.get()
        
        # 清除旧控件
        for w in self.param_widgets.values():
            w.destroy()
        self.param_widgets = {}
        
        # 重建控件
        if task in self.param_entries:
            for i, (label, key) in enumerate(self.param_entries[task]):
                ttk.Label(self.param_widgets.setdefault('_frame', ttk.Frame(self.task_tab.winfo_children()[1])), 
                         text=f"{label}:").grid(row=i, column=0, sticky="w", pady=3)
                
                if key == 'content' or key == 'description':
                    entry = tk.Text(self.param_widgets['_frame'], height=6, width=40, font=("Microsoft YaHei", 9))
                elif key == 'fields':
                    entry = tk.Text(self.param_widgets['_frame'], height=6, width=40, font=("Microsoft YaHei", 9))
                    entry.insert("1.0", '[{"label":"字段1","value":"值1"},{"label":"字段2","value":"值2"}]')
                else:
                    entry = ttk.Entry(self.param_widgets['_frame'], width=40)
                
                entry.grid(row=i, column=1, pady=3, padx=5)
                self.param_widgets[key] = entry
    
    def setup_record_tab(self):
        """坐标录制Tab"""
        frame = ttk.Frame(self.record_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # 说明
        info = tk.Label(
            frame,
            text="点击"开始录制"，然后点击屏幕上的目标位置。\n录制的坐标会自动保存为点击序列任务。",
            font=("Microsoft YaHei", 9),
            fg="#666"
        )
        info.pack(pady=10)
        
        # 录制列表
        list_frame = ttk.LabelFrame(frame, text="录制的点击序列", padding=10)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.record_listbox = tk.Listbox(list_frame, height=10, font=("Consolas", 9))
        self.record_listbox.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.record_listbox.yview)
        self.record_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 录制的数据
        self.recorded_clicks = []
        
        # 按钮区
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, 
            text="📍 开始录制(获取当前鼠标位置)",
            command=self.get_current_pos
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="➕ 添加到列表",
            command=self.add_to_record_list
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="▶ 执行录制序列",
            command=self.execute_recorded
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="💾 保存任务",
            command=self.save_recorded
        ).pack(side="left", padx=5)
        
        # 当前坐标显示
        self.pos_label = tk.Label(
            frame, 
            text="当前鼠标位置: 点击按钮获取",
            font=("Consolas", 10),
            bg="#f0f0f0",
            relief="sunken",
            padx=10,
            pady=5
        )
        self.pos_label.pack(fill="x", pady=10)
    
    def setup_custom_tab(self):
        """自定义步骤Tab"""
        frame = ttk.Frame(self.custom_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(
            frame,
            text="输入自定义步骤JSON，点击执行:",
            font=("Microsoft YaHei", 10)
        ).pack(anchor="w")
        
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True, pady=5)
        
        self.custom_text = tk.Text(
            text_frame, 
            height=15, 
            font=("Consolas", 9),
            wrap="none"
        )
        self.custom_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.custom_text.yview)
        self.custom_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 示例JSON
        example = '''[
  {"action": "click", "params": {"x": 100, "y": 200}, "desc": "点击标题框"},
  {"action": "type", "params": {"text": "商品标题"}, "desc": "输入标题"},
  {"action": "press", "params": {"key": "tab"}, "desc": "跳到下一字段"},
  {"action": "screenshot", "params": {}, "desc": "截图确认"}
]'''
        self.custom_text.insert("1.0", example)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="▶ 执行自定义步骤",
            command=self.execute_custom
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="💾 保存步骤",
            command=self.save_custom_steps
        ).pack(side="left", padx=5)
    
    def setup_log_tab(self):
        """日志Tab"""
        frame = ttk.Frame(self.log_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(frame, font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def log(self, message, color=None):
        """写日志"""
        self.log_text.config(state="normal")
        if color:
            self.log_text.insert("end", message + "\n", color)
        else:
            self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def get_current_pos(self):
        """获取当前鼠标位置"""
        if CORE_READY:
            pos = pc.mouse.get_position()
            self.pos_label.config(text=f"当前鼠标位置: X={pos['x']}, Y={pos['y']}")
            self._last_pos = pos
            self.log(f"获取位置: X={pos['x']}, Y={pos['y']}")
    
    def add_to_record_list(self):
        """添加到录制列表"""
        if hasattr(self, '_last_pos'):
            pos = self._last_pos
            desc = f"点击 X={pos['x']}, Y={pos['y']}"
            self.recorded_clicks.append({'x': pos['x'], 'y': pos['y'], 'desc': desc})
            self.record_listbox.insert("end", desc)
            self.log(f"添加: {desc}")
    
    def execute_recorded(self):
        """执行录制的序列"""
        if not self.recorded_clicks:
            messagebox.showwarning("空列表", "请先录制点击序列")
            return
        
        def run():
            self.execute_btn.config(state="disabled")
            self.log("=== 开始执行录制序列 ===", "header")
            for i, click in enumerate(self.recorded_clicks):
                self.log(f"[{i+1}/{len(self.recorded_clicks)}] {click['desc']}")
                if CORE_READY:
                    pc.mouse.click(click['x'], click['y'])
                    import time; time.sleep(0.5)
            self.log("=== 执行完成 ===", "success")
            self.execute_btn.config(state="normal")
        
        threading.Thread(target=run, daemon=True).start()
    
    def save_recorded(self):
        """保存录制的任务"""
        if not self.recorded_clicks:
            messagebox.showwarning("空列表", "请先录制点击序列")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.recorded_clicks, f, ensure_ascii=False, indent=2)
            self.log(f"已保存: {filepath}")
    
    def execute_task(self):
        """执行预设任务"""
        if not CORE_READY:
            messagebox.showerror("错误", "核心模块未就绪")
            return
        
        task = self.task_var.get()
        
        # 收集参数
        params = {}
        for key, entry in self.param_widgets.items():
            if key == '_frame':
                continue
            if isinstance(entry, tk.Text):
                value = entry.get("1.0", "end").strip()
            else:
                value = entry.get().strip()
            params[key] = value
        
        def run():
            self.execute_btn.config(state="disabled")
            self.status_bar.config(text=f"状态: 执行中... | 任务: {task}")
            self.log(f"=== 开始执行: {task} ===", "header")
            
            try:
                if task == 'list_xianyu_item':
                    result = list_xianyu_item(pc, **params)
                elif task == 'publish_article':
                    result = publish_article(pc, **params)
                elif task == 'fill_form':
                    params['fields'] = json.loads(params.get('fields', '[]'))
                    result = fill_form(pc, **params)
                
                self.log(f"执行结果: {result}")
                self.log("=== 执行完成 ===", "success")
                messagebox.showinfo("完成", f"任务执行完成\n{result}")
                
            except Exception as e:
                self.log(f"错误: {e}", "error")
                messagebox.showerror("执行错误", str(e))
            
            self.execute_btn.config(state="normal")
            self.status_bar.config(text="状态: 就绪")
        
        threading.Thread(target=run, daemon=True).start()
    
    def execute_custom(self):
        """执行自定义步骤"""
        if not CORE_READY:
            messagebox.showerror("错误", "核心模块未就绪")
            return
        
        try:
            steps_json = self.custom_text.get("1.0", "end").strip()
            steps = json.loads(steps_json)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON错误", f"JSON格式错误:\n{e}")
            return
        
        def run():
            self.log(f"=== 执行自定义步骤 ({len(steps)}步) ===", "header")
            try:
                for i, step in enumerate(steps):
                    action = step.get('action')
                    params = step.get('params', {})
                    desc = step.get('desc', f'Step {i+1}')
                    self.log(f"[{i+1}/{len(steps)}] {desc}: {action}")
                    result = pc.execute_step(action, **params)
                    self.log(f"    → {result}")
                    import time; time.sleep(0.5)
                self.log("=== 完成 ===", "success")
            except Exception as e:
                self.log(f"错误: {e}", "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def save_custom_steps(self):
        """保存自定义步骤"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.custom_text.get("1.0", "end").strip())
            self.log(f"已保存: {filepath}")
    
    def clear_params(self):
        """清空参数"""
        for key, entry in self.param_widgets.items():
            if key == '_frame':
                continue
            if isinstance(entry, tk.Text):
                entry.delete("1.0", "end")
            else:
                entry.delete(0, "end")


def main():
    root = tk.Tk()
    
    # 样式
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass
    
    # 配置颜色标签
    root.tk.call('proc', 'InitStyles')
    
    app = AutoMateGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
