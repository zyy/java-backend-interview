#!/usr/bin/env python3
"""
为所有Markdown文件添加front matter
"""
import os
import re

def add_frontmatter_to_file(filepath):
    """为单个文件添加front matter"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有front matter
    if content.startswith('---'):
        # 已经有front matter，检查是否有layout
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            # 如果已经有layout，跳过
            if 'layout:' in frontmatter:
                return False
            # 否则添加layout
            new_frontmatter = frontmatter + '\nlayout: default'
            new_content = content.replace(frontmatter, new_frontmatter, 1)
        else:
            # front matter格式错误，跳过
            return False
    else:
        # 没有front matter，添加
        # 提取标题（第一个#标题）
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(filepath).replace('.md', '')
        
        frontmatter = f"""---
layout: default
title: {title}
---
"""
        new_content = frontmatter + content
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def process_md_files(directory='.'):
    """处理目录下所有.md文件"""
    count = 0
    for root, dirs, files in os.walk(directory):
        # 跳过_layouts和_sass等特殊目录
        if any(skip in root for skip in ['_layouts', '_sass', '_site', '.git']):
            continue
            
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                try:
                    if add_frontmatter_to_file(filepath):
                        print(f'✓ 已更新: {os.path.relpath(filepath, directory)}')
                        count += 1
                    else:
                        print(f'○ 已跳过: {os.path.relpath(filepath, directory)}')
                except Exception as e:
                    print(f'✗ 处理失败: {filepath} - {e}')
    
    return count

def main():
    print('正在为Markdown文件添加front matter...')
    count = process_md_files('docs')
    print(f'\n处理完成，更新了 {count} 个文件')

if __name__ == '__main__':
    main()