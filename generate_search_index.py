#!/usr/bin/env python3
"""
生成全文搜索索引
为Java后端面试资料库生成搜索索引JSON文件
"""

import os
import json
import re
from pathlib import Path
import hashlib

def clean_markdown_content(content):
    """清理Markdown内容，移除格式标记"""
    # 移除HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    # 移除Markdown链接 [text](url)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    # 移除Markdown图片
    content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)
    # 移除代码块
    content = re.sub(r'```[\s\S]*?```', '', content)
    content = re.sub(r'`[^`]+`', '', content)
    # 移除标题标记
    content = re.sub(r'#+\s*', '', content)
    # 移除粗体/斜体
    content = re.sub(r'[\*_]{1,3}([^*_]+)[\*_]{1,3}', r'\1', content)
    # 移除多余空白
    content = re.sub(r'\s+', ' ', content)
    return content.strip()

def extract_title(content):
    """从Markdown内容中提取标题"""
    # 查找第一个一级标题
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1)
    
    # 如果没有一级标题，尝试从文件名推断
    return None

def extract_description(content, max_length=200):
    """从内容中提取描述（前几段）"""
    # 获取前500个字符，清理后截取
    preview = content[:500]
    preview = clean_markdown_content(preview)
    if len(preview) > max_length:
        preview = preview[:max_length] + '...'
    return preview

def read_markdown_file(filepath):
    """读取Markdown文件并解析内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取基本信息
    title = extract_title(content)
    clean_content = clean_markdown_content(content)
    description = extract_description(content)
    
    # 如果没有标题，使用文件名
    if not title:
        title = os.path.basename(filepath).replace('.md', '').replace('-', ' ').title()
    
    return {
        'content': clean_content,
        'title': title,
        'description': description
    }

def generate_search_index(docs_dir='docs'):
    """生成搜索索引"""
    search_index = []
    
    # 遍历所有Markdown文件
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                
                # 跳过根目录的index.md（首页）
                if file == 'index.md' and root == docs_dir:
                    continue
                
                # 计算相对路径
                rel_path = os.path.relpath(filepath, docs_dir)
                
                # 生成URL（GitHub Pages格式）
                url_path = rel_path.replace('\\', '/')  # Windows路径转换
                url = f'/{url_path}'.replace('.md', '.html')
                
                # 如果是目录的index.md，URL指向目录
                if file == 'index.md':
                    dir_url = os.path.dirname(url)
                    if dir_url != '.':
                        url = f'/{dir_url}/'
                
                # 读取和解析文件
                try:
                    file_info = read_markdown_file(filepath)
                    
                    # 添加到索引
                    search_index.append({
                        'id': hashlib.md5(url.encode()).hexdigest()[:8],
                        'title': file_info['title'],
                        'content': file_info['content'],
                        'description': file_info['description'],
                        'url': url,
                        'category': os.path.dirname(rel_path).replace('\\', '/') or '根目录'
                    })
                    
                    print(f"✓ 已索引: {rel_path}")
                    
                except Exception as e:
                    print(f"✗ 处理文件失败: {rel_path} - {e}")
    
    # 保存索引文件
    output_file = os.path.join(docs_dir, 'search_index.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 搜索索引已生成: {output_file}")
    print(f"   索引文档数: {len(search_index)}")
    
    return search_index

def create_search_page(docs_dir='docs'):
    """创建搜索页面HTML"""
    search_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>搜索 - Java 后端面试资料库</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .container