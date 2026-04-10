"""
预设任务 - 常见场景的自动化任务
"""
import time
import sys

def publish_article(pc, title, content, platform='公众号'):
    """
    发布文章到公众号
    注意：需要先手动打开公众号后台并登录
    """
    print(f"=== 发布文章到 {platform} ===")
    print(f"标题: {title}")
    
    steps = [
        {'action': 'get_clipboard', 'params': {}, 'desc': '读取当前剪贴板'},
        {'action': 'set_clipboard', 'params': {'text': title}, 'desc': '复制标题'},
        {'action': 'paste', 'params': {}, 'desc': '粘贴标题', 'delay': 0.5},
        {'action': 'set_clipboard', 'params': {'text': content}, 'desc': '复制正文'},
        {'action': 'press', 'params': {'key': 'tab'}, 'desc': '切换到正文输入框', 'delay': 0.3},
        {'action': 'paste', 'params': {}, 'desc': '粘贴正文', 'delay': 0.5},
        {'action': 'screenshot', 'params': {'path': 'screenshot.png'}, 'desc': '截图确认'},
    ]
    
    task = sys.modules[__name__]
    from tasks.base import GenericTask
    t = GenericTask(pc)
    return t.execute_steps(steps)

def list_xianyu_item(pc, title, price, description, images=None):
    """
    闲鱼上架商品
    注意：需要先打开闲鱼App并进入发布页面
    """
    print(f"=== 闲鱼上架商品 ===")
    print(f"标题: {title}")
    print(f"价格: {price}")
    
    steps = [
        {'action': 'set_clipboard', 'params': {'text': title}, 'desc': '复制标题'},
        {'action': 'paste', 'params': {}, 'desc': '粘贴标题', 'delay': 0.5},
        {'action': 'press', 'params': {'key': 'tab'}, 'desc': '下一个字段', 'delay': 0.3},
        {'action': 'set_clipboard', 'params': {'text': price}, 'desc': '复制价格'},
        {'action': 'paste', 'params': {}, 'desc': '粘贴价格', 'delay': 0.3},
        {'action': 'press', 'params': {'key': 'tab'}, 'desc': '下一个字段', 'delay': 0.3},
        {'action': 'set_clipboard', 'params': {'text': description[:200]}, 'desc': '复制描述(前200字)'},
        {'action': 'paste', 'params': {}, 'desc': '粘贴描述', 'delay': 0.5},
    ]
    
    from tasks.base import GenericTask
    t = GenericTask(pc)
    return t.execute_steps(steps)

def fill_form(pc, fields):
    """
    批量填写表单
    fields: [{'label': '姓名', 'value': '张三'}, ...]
    """
    print(f"=== 批量填写表单 ({len(fields)}个字段) ===")
    
    steps = []
    for i, field in enumerate(fields):
        steps.append({'action': 'set_clipboard', 'params': {'text': str(field['value'])}, 'desc': f'复制{field["label"]}'})
        steps.append({'action': 'paste', 'params': {}, 'desc': f'填写{field["label"]}', 'delay': 0.3})
        if i < len(fields) - 1:
            steps.append({'action': 'press', 'params': {'key': 'tab'}, 'desc': '下一个字段', 'delay': 0.2})
    
    from tasks.base import GenericTask
    t = GenericTask(pc)
    return t.execute_steps(steps)

def auto_click_sequence(pc, clicks):
    """
    自动点击序列
    clicks: [{'x': 100, 'y': 200, 'desc': '点击发布按钮'}, ...]
    """
    print(f"=== 自动点击序列 ({len(clicks)}次点击) ===")
    
    steps = []
    for i, click in enumerate(clicks):
        steps.append({
            'action': 'click',
            'params': {'x': click['x'], 'y': click['y']},
            'desc': click.get('desc', f'点击#{i+1}'),
            'delay': click.get('delay', 0.5),
            'screenshot': click.get('screenshot', False)
        })
    
    from tasks.base import GenericTask
    t = GenericTask(pc)
    return t.execute_steps(steps)
