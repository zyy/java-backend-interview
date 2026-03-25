#!/usr/bin/env python3
"""
生成全文搜索索引并创建搜索页面
"""
import os
import json
import re

def clean_markdown(text):
    """移除markdown格式"""
    # 移除代码块
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # 移除内联代码
    text = re.sub(r'`[^`]+`', '', text)
    # 移除链接
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    # 移除标题标记
    text = re.sub(r'#+\s*', '', text)
    # 移除粗体/斜体
    text = re.sub(r'[\*_]{1,3}([^*_]+)[\*_]{1,3}', r'\1', text)
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 合并空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_title(content):
    """提取标题"""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1)
    return None

def process_md_files(docs_dir='docs'):
    """处理所有md文件"""
    index = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            if file == 'index.md' and root == docs_dir:
                continue  # 跳过根目录的index.md
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            title = extract_title(content) or file.replace('.md', '').replace('-', ' ').title()
            # 生成URL - GitHub Pages格式：去掉.md后缀
            rel_path = os.path.relpath(path, docs_dir)
            url = '/' + rel_path.replace('\\', '/').replace('.md', '')
            if file == 'index.md':
                # 目录索引页面，确保以斜杠结尾
                if url.endswith('/index'):
                    url = url[:-5]  # 去掉'/index'
                if url != '/':
                    url = url + '/'
            # 清理内容
            clean = clean_markdown(content)
            # 截取前500字符作为描述
            description = clean[:500] + ('...' if len(clean) > 500 else '')
            category = os.path.dirname(rel_path)
            if category == '.':
                category = '根目录'
            index.append({
                'title': title,
                'url': url,
                'description': description,
                'category': category,
                'content': clean[:5000]  # 限制长度
            })
    return index

def write_index(index, output_path='docs/search_index.json'):
    """写入索引文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f'Generated {len(index)} entries to {output_path}')

def create_search_html(output_path='docs/search.html'):
    """创建搜索页面"""
    html = '''<!DOCTYPE html>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .search-box {
            margin-bottom: 30px;
        }
        #searchInput {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }
        #searchInput:focus {
            border-color: #667eea;
        }
        #results {
            margin-top: 20px;
        }
        .result-item {
            padding: 20px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }
        .result-item:hover {
            background: #f9f9f9;
        }
        .result-title {
            font-size: 18px;
            color: #667eea;
            text-decoration: none;
            display: block;
            margin-bottom: 5px;
        }
        .result-title:hover {
            text-decoration: underline;
        }
        .result-description {
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }
        .result-category {
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .no-results {
            color: #999;
            text-align: center;
            padding: 40px;
        }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 全文搜索</h1>
        <p class="subtitle">搜索 Java 后端面试资料库中的内容</p>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="输入关键词，如：HashMap、线程池、Spring...">
        </div>
        
        <div id="results"></div>
        
        <a href="/" class="back-link">← 返回首页</a>
    </div>

    <script>
        let searchIndex = [];
        
        // 加载索引文件
        fetch('/search_index.json')
            .then(response => response.json())
            .then(data => {
                searchIndex = data;
                console.log('Loaded', searchIndex.length, 'documents');
            })
            .catch(error => {
                console.error('Error loading search index:', error);
                document.getElementById('results').innerHTML = 
                    '<div class="no-results">加载搜索索引失败，请刷新重试。</div>';
            });
        
        // 搜索函数
        function performSearch(query) {
            if (!searchIndex.length) return [];
            query = query.toLowerCase().trim();
            if (!query) return [];
            
            return searchIndex.filter(item => {
                const text = (item.title + ' ' + item.description + ' ' + item.content).toLowerCase();
                return text.includes(query);
            });
        }
        
        // 渲染结果
        function renderResults(results) {
            const container = document.getElementById('results');
            if (!results.length) {
                container.innerHTML = '<div class="no-results">没有找到相关结果，请尝试其他关键词。</div>';
                return;
            }
            
            let html = '';
            results.forEach(item => {
                html += `
                <div class="result-item">
                    <a href="${item.url}" class="result-title">${item.title}</a>
                    <div class="result-description">${item.description}</div>
                    <span class="result-category">${item.category}</span>
                </div>`;
            });
            container.innerHTML = html;
        }
        
        // 输入事件处理
        let searchTimeout;
        document.getElementById('searchInput').addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const results = performSearch(e.target.value);
                renderResults(results);
            }, 300);
        });
        
        // 初始加载空结果
        renderResults([]);
    </script>
</body>
</html>'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Search page created at {output_path}')

def main():
    print('Generating search index...')
    index = process_md_files('docs')
    write_index(index, 'docs/search_index.json')
    create_search_html('docs/search.html')
    print('Done!')

if __name__ == '__main__':
    main()