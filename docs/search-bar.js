// 全局搜索栏
class SearchBar {
  constructor() {
    this.index = [];
    this.container = document.querySelector('.search-bar-container');
    if (!this.container) {
      console.warn('搜索栏容器未找到，搜索功能将不可用');
      return;
    }
    this.input = this.container.querySelector('.search-input');
    this.results = this.container.querySelector('.search-results');
    this.init();
  }
  
  async init() {
    if (!this.container) return;
    
    this.bindEvents();
    await this.loadIndex();
  }
  
  bindEvents() {
    if (!this.input || !this.results) return;
    
    let timeout;
    this.input.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        this.search(e.target.value);
      }, 300);
    });
    
    this.input.addEventListener('focus', () => {
      if (this.input.value.trim()) {
        this.search(this.input.value);
      }
    });
    
    // 点击外部关闭结果
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-box')) {
        this.results.classList.remove('active');
      }
    });
    
    // 键盘导航
    this.input.addEventListener('keydown', (e) => {
      const items = this.results.querySelectorAll('.search-result-item');
      if (!items.length) return;
      
      const currentActive = this.results.querySelector('.search-result-item.active');
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
        this.results.classList.remove('active');
        this.input.blur();
      }
    });
  }
  
  highlightItem(item) {
    const items = this.results.querySelectorAll('.search-result-item');
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
        '/java-backend-interview/search_index.json',  // 带baseurl的绝对路径
        '/search_index.json',      // 绝对路径（如果部署在根目录）
        'search_index.json',       // 相对路径
        '../search_index.json',    // 上一级目录
        './search_index.json',     // 当前目录
        '/java-backend-interview/docs/search_index.json',  // docs目录
        'docs/search_index.json',  // 相对路径到docs
        '../docs/search_index.json'  // 上一级的docs
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
        this.results.innerHTML = '<div class="search-no-results">搜索索引加载失败，请刷新重试</div>';
      }
    } catch (error) {
      console.error('加载搜索索引失败:', error);
    }
  }
  
  search(query) {
    if (!this.input || !this.results) return;
    
    query = query.trim().toLowerCase();
    
    if (!query) {
      this.results.classList.remove('active');
      return;
    }
    
    if (!this.index.length) {
      this.results.innerHTML = '<div class="search-no-results">搜索索引加载中...</div>';
      this.results.classList.add('active');
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
      this.results.innerHTML = `
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
        
        // 确保URL以正确的格式
        let url = item.url;
        // 如果URL以/开头但不是/java-backend-interview开头，且当前在GitHub Pages上，可能需要添加baseurl
        if (url.startsWith('/') && !url.startsWith('/java-backend-interview')) {
          // 我们可以尝试添加baseurl，但更好的方法是确保搜索索引中的URL是正确的
          // 暂时保持原样
        }
        
        html += `
          <div class="search-result-item" data-url="${url}">
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
      
      this.results.innerHTML = html;
      
      // 绑定点击事件
      this.results.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
          let url = item.getAttribute('data-url');
          // 如果当前页面不是根目录，可能需要调整相对路径
          if (url.startsWith('/') && !window.location.pathname.endsWith('/')) {
            // 我们已经在正确的绝对路径上
          }
          window.location.href = url;
        });
      });
    }
    
    this.results.classList.add('active');
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