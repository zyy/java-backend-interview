// 全局搜索栏
class SearchBar {
  constructor() {
    this.index = [];
    this.init();
  }
  
  async init() {
    this.createHTML();
    this.bindEvents();
    await this.loadIndex();
  }
  
  createHTML() {
    // 首先添加CSS样式
    if (!document.querySelector('#search-bar-styles')) {
      const style = document.createElement('style');
      style.id = 'search-bar-styles';
      style.textContent = `
        /* 全局搜索栏样式 */
        .search-bar-container {
          position: fixed;
          top: 10px;
          right: 20px;
          z-index: 1000;
        }
        
        .search-box {
          position: relative;
          width: 300px;
        }
        
        .search-input {
          width: 100%;
          padding: 10px 15px;
          font-size: 14px;
          border: 2px solid #ddd;
          border-radius: 25px;
          outline: none;
          transition: all 0.3s;
          background: white;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .search-input:focus {
          border-color: #667eea;
          box-shadow: 0 2px 15px rgba(102, 126, 234, 0.3);
          width: 400px;
        }
        
        .search-results {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: white;
          border-radius: 10px;
          box-shadow: 0 5px 20px rgba(0,0,0,0.15);
          max-height: 500px;
          overflow-y: auto;
          display: none;
          margin-top: 5px;
        }
        
        .search-results.active {
          display: block;
        }
        
        .search-result-item {
          padding: 15px;
          border-bottom: 1px solid #eee;
          cursor: pointer;
          transition: background 0.2s;
        }
        
        .search-result-item:hover {
          background: #f8f9fa;
        }
        
        .search-result-title {
          font-weight: 600;
          color: #667eea;
          margin-bottom: 5px;
          font-size: 14px;
        }
        
        .search-result-description {
          color: #666;
          font-size: 12px;
          margin-bottom: 5px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
        
        .search-result-category {
          display: inline-block;
          background: #e9ecef;
          color: #495057;
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 11px;
        }
        
        .search-no-results {
          padding: 20px;
          text-align: center;
          color: #999;
        }
        
        .search-loading {
          padding: 20px;
          text-align: center;
          color: #667eea;
        }
        
        /* 移动端适配 */
        @media (max-width: 768px) {
          .search-bar-container {
            top: 5px;
            right: 10px;
            left: 10px;
          }
          
          .search-box {
            width: 100%;
          }
          
          .search-input {
            width: 100%;
          }
          
          .search-input:focus {
            width: 100%;
          }
        }
      `;
      document.head.appendChild(style);
    }
    
    // 创建搜索栏HTML结构
    const container = document.createElement('div');
    container.className = 'search-bar-container';
    container.innerHTML = `
      <div class="search-box">
        <input type="text" class="search-input" placeholder="搜索面试题..." autocomplete="off">
        <div class="search-results"></div>
      </div>
    `;
    
    // 添加到页面顶部
    document.body.prepend(container);
  }
  
  bindEvents() {
    const input = document.querySelector('.search-input');
    const results = document.querySelector('.search-results');
    
    let timeout;
    input.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        this.search(e.target.value);
      }, 300);
    });
    
    input.addEventListener('focus', () => {
      if (input.value.trim()) {
        this.search(input.value);
      }
    });
    
    // 点击外部关闭结果
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-box')) {
        results.classList.remove('active');
      }
    });
    
    // 键盘导航
    input.addEventListener('keydown', (e) => {
      const items = results.querySelectorAll('.search-result-item');
      if (!items.length) return;
      
      const currentActive = results.querySelector('.search-result-item.active');
      let index = currentActive ? Array.from(items).indexOf(currentActive) : -1;
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        index = (index + 1) % items.length;
        this.highlightItem(items[index]);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        index = (index - 1 + items.length) % items.length;
        this.highlightItem(items[index]);
      } else if (e.key === 'Enter' && currentActive) {
        e.preventDefault();
        currentActive.click();
      } else if (e.key === 'Escape') {
        results.classList.remove('active');
        input.blur();
      }
    });
  }
  
  highlightItem(item) {
    const items = document.querySelectorAll('.search-result-item');
    items.forEach(i => i.classList.remove('active'));
    if (item) {
      item.classList.add('active');
      item.scrollIntoView({ block: 'nearest' });
    }
  }
  
  async loadIndex() {
    try {
      // 尝试多种路径（考虑GitHub Pages的baseurl）
      const paths = [
        '/java-backend-interview/docs/search_index.json',  // 带baseurl的绝对路径
        '/docs/search_index.json',      // 绝对路径（如果部署在根目录）
        'docs/search_index.json',       // 相对路径
        '../docs/search_index.json',    // 上一级目录
        './docs/search_index.json',     // 当前目录下的docs
        '/search_index.json',           // 根目录（备用）
        'search_index.json',            // 当前目录
        '/java-backend-interview/search_index.json'  // baseurl根目录
      ];
      
      let response;
      for (const path of paths) {
        try {
          response = await fetch(path);
          if (response.ok) {
            console.log('搜索索引加载成功，路径:', path);
            break;
          }
        } catch (e) {
          // 继续尝试下一个路径
        }
      }
      
      if (response && response.ok) {
        this.index = await response.json();
        console.log('搜索索引加载成功:', this.index.length, '条记录');
      } else {
        console.error('无法加载搜索索引');
      }
    } catch (error) {
      console.error('加载搜索索引失败:', error);
    }
  }
  
  search(query) {
    query = query.trim().toLowerCase();
    const results = document.querySelector('.search-results');
    
    if (!query) {
      results.classList.remove('active');
      return;
    }
    
    if (!this.index.length) {
      results.innerHTML = '<div class="search-no-results">搜索索引加载中...</div>';
      results.classList.add('active');
      return;
    }
    
    // 执行搜索
    const startTime = performance.now();
    const matches = this.index.filter(item => {
      const text = (item.title + ' ' + item.description + ' ' + item.content).toLowerCase();
      return text.includes(query);
    });
    const endTime = performance.now();
    
    // 渲染结果
    if (matches.length === 0) {
      results.innerHTML = `
        <div class="search-no-results">
          没有找到"${query}"的相关结果<br>
          <small>耗时 ${(endTime - startTime).toFixed(2)}ms</small>
        </div>
      `;
    } else {
      let html = '';
      matches.slice(0, 20).forEach(item => {
        // 高亮关键词
        const title = this.highlightText(item.title, query);
        const desc = this.highlightText(item.description, query);
        
        html += `
          <div class="search-result-item" data-url="${item.url}">
            <div class="search-result-title">${title}</div>
            <div class="search-result-description">${desc}</div>
            <span class="search-result-category">${item.category}</span>
          </div>
        `;
      });
      
      if (matches.length > 20) {
        html += `<div class="search-no-results">找到 ${matches.length} 条结果，显示前 20 条</div>`;
      } else {
        html += `<div class="search-no-results">找到 ${matches.length} 条结果，耗时 ${(endTime - startTime).toFixed(2)}ms</div>`;
      }
      
      results.innerHTML = html;
      
      // 绑定点击事件
      results.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
          const url = item.getAttribute('data-url');
          window.location.href = url;
        });
      });
    }
    
    results.classList.add('active');
  }
  
  highlightText(text, query) {
    if (!text || !query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }
}

// 页面加载完成后初始化搜索栏
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new SearchBar();
  });
} else {
  new SearchBar();
}