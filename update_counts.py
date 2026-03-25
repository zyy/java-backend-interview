#!/usr/bin/env python3
import os
import re

docs_dir = 'docs'

modules = [
    'java-core',
    'jvm',
    'spring',
    'database',
    'middleware',
    'microservices',
    'design-patterns',
    'algorithm',
    'projects'
]

counts = {}
total_articles = 0
for module in modules:
    module_path = os.path.join(docs_dir, module)
    if os.path.exists(module_path):
        # count all .md files
        md_files = [f for f in os.listdir(module_path) if f.endswith('.md')]
        counts[module] = len(md_files)
        total_articles += len(md_files)
    else:
        counts[module] = 0

print('Module counts:')
for module, cnt in counts.items():
    print(f'{module}: {cnt}')

print(f'Total articles: {total_articles}')

# Now update README.md
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

# Replace each line with pattern like "| [Java 核心](./docs/java-core/) | 基础语法、集合、并发、IO | 18 篇 |"
for module, cnt in counts.items():
    # Determine Chinese name mapping
    name_map = {
        'java-core': 'Java 核心',
        'jvm': 'JVM 原理',
        'spring': 'Spring 框架',
        'database': '数据库',
        'middleware': '中间件',
        'microservices': '微服务',
        'design-patterns': '设计模式',
        'algorithm': '算法',
        'projects': '项目实战'
    }
    chinese = name_map.get(module, module)
    # pattern: | [Java 核心](./docs/java-core/) | ... | 18 篇 |
    pattern = rf'\| \[{re.escape(chinese)}\]\(\./docs/{re.escape(module)}/\) \| .*? \| \d+ 篇 \|'
    replacement = f'| [{chinese}](./docs/{module}/) | ... | {cnt} 篇 |'
    # We need to capture the existing description and keep it.
    # Better approach: replace only the count part.
    # Let's match the whole line and replace the count.
    # We'll use a more precise pattern: capture before the count.
    pattern2 = rf'(\| \[{re.escape(chinese)}\]\(\./docs/{re.escape(module)}/\) \| .*? \| )\d+( 篇 \|)'
    replacement2 = rf'\g<1>{cnt}\g<2>'
    readme = re.sub(pattern2, replacement2, readme)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)

print('README.md updated.')

# Update index.md badges
with open('index.md', 'r', encoding='utf-8') as f:
    index = f.read()

# Replace badges in cards. Each card has <span class="badge">X 篇</span>
# Need to map module to card title.
card_map = {
    'java-core': 'Java 核心',
    'jvm': 'JVM 原理',
    'spring': 'Spring 框架',
    'database': '数据库',
    'middleware': '中间件',
    'design-patterns': '设计模式',
    'algorithm': '算法',
    'microservices': '微服务'
}
for module, cnt in counts.items():
    if module in card_map:
        chinese = card_map[module]
        # Find card section for this module. The badge is inside a card with href containing module.
        pattern = rf'(<a class="card" href=".*?{re.escape(module)}/".*?<span class="badge">)\d+( 篇</span>)'
        replacement = rf'\g<1>{cnt}\g<2>'
        index = re.sub(pattern, replacement, index)

# Also update stats: "33+", "100+", "50+"
# Need to calculate total number of modules (interview topics) maybe 9?
total_modules = len(modules)
# total articles we already have
# code examples? we don't have that data, maybe keep as is or estimate.
# For now, update only the first two stats.
# Find <div class="stat-number">33+</div> and <div class="stat-number">100+</div>
# We'll replace with total_modules and total_articles
# But careful: there are three stats. We'll replace first two.
# Use regex to match each stat-number div.
# We'll do a simple replacement for the first occurrence (33+) and second occurrence (100+).
# This is fragile but works for this file.
# Let's split by lines and process.
lines = index.split('\n')
stat_count = 0
for i, line in enumerate(lines):
    if 'stat-number' in line:
        if stat_count == 0:
            lines[i] = line.replace('33+', f'{total_modules}+')
            stat_count += 1
        elif stat_count == 1:
            lines[i] = line.replace('100+', f'{total_articles}+')
            stat_count += 1
        else:
            # third stat (code examples) keep as is
            pass
index = '\n'.join(lines)

with open('index.md', 'w', encoding='utf-8') as f:
    f.write(index)

print('index.md updated.')