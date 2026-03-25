#!/usr/bin/env python3
"""
将搜索栏添加到所有HTML页面
"""
import os
import re

def add_searchbar_to_html(html_content):
    """在HTML中添加搜索栏相关资源"""
    # 在head中添加CSS链接
    css_link = '<link rel="stylesheet" href="search-bar.css">'
    
    # 检查是否已存在
    if 'search-bar.css' in html_content:
        return html_content
    
    # 在</head>前添加CSS
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', f'{css_link}\n</head>')
    
    # 在body结束前添加JS
    js_script = '<script src="search-bar.js"></script>'
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{js_script}\n</body>')
    else:
        # 如果没有</body>，在末尾添加
        html_content += f'\n{js_script}\n'
    
    return html_content

def process_html_files(docs_dir='docs'):
    """处理所有HTML文件"""
    processed = 0
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                # 跳过搜索页面本身
                if file == 'search.html':
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否是Jekyll生成的页面（包含layout）
                    if 'layout:' in content:
                        # 这是Markdown文件，不是最终HTML
                        continue
                    
                    new_content = add_searchbar_to_html(content)
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f'✓ 已更新: {os.path.relpath(filepath, docs_dir)}')
                        processed += 1
                    else:
                        print(f'○ 无需更新: {os.path.relpath(filepath, docs_dir)}')
                        
                except Exception as e:
                    print(f'✗ 处理失败: {filepath} - {e}')
    
    return processed

def main():
    print('正在将搜索栏添加到所有页面...')
    processed = process_html_files('docs')
    print(f'\n处理完成，更新了 {processed} 个文件')
    
    # 确保搜索栏资源在docs目录中
    if not os.path.exists('docs/search-bar.css'):
        print('警告: search-bar.css 不在 docs 目录中')
    if not os.path.exists('docs/search-bar.js'):
        print('警告: search-bar.js 不在 docs 目录中')

if __name__ == '__main__':
    main()