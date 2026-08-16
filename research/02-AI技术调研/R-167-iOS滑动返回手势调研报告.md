# iOS 左侧边缘滑动返回功能调研报告

> 调研日期：2026-07-07  
> 调研目标：在手机端（尤其是 iOS）Web 应用 / PWA / 混合 App 中实现类似 iOS 原生的「左侧从左向右滑动返回」功能

---

## 目录

1. [iOS 原生滑动返回机制](#1-ios-原生滑动返回机制)
2. [Web 端实现的核心挑战](#2-web-端实现的核心挑战)
3. [技术方案总览](#3-技术方案总览)
4. [方案一：Touch/Pointer Events + History API（纯 Web 方案）](#4-方案一touchpointer-events--history-api纯-web-方案)
5. [方案二： overscroll-behavior + 边缘检测](#5-方案二overscroll-behavior--边缘检测)
6. [方案三：View Transitions API + 手势驱动](#6-方案三view-transitions-api--手势驱动)
7. [方案四：混合 App（WKWebView）原生桥接](#7-方案四混合-appwkwebview原生桥接)
8. [框架层面实现](#8-框架层面实现)
9. [关键 CSS 属性详解](#9-关键-css-属性详解)
10. [iOS Safari 特殊行为与限制](#10-ios-safari-特殊行为与限制)
11. [最佳实践与避坑指南](#11-最佳实践与避坑指南)
12. [方案对比与推荐](#12-方案对比与推荐)
13. [参考代码：完整实现示例](#13-参考代码完整实现示例)

---

## 1. iOS 原生滑动返回机制

### 1.1 原生交互描述

iOS 系统中，当用户处于 `UINavigationController` 管理的视图栈中时，从屏幕左边缘（约 0~30pt 宽度区域）向右滑动可以触发 **interactive pop gesture**（交互式返回手势），实现：

- **实时跟手**：当前页面随手指右移，露出下方上一层页面
- **可取消**：滑动距离不够时松手会自动弹回
- **完成/取消阈值**：滑动超过屏幕宽度约 50% 时松手即完成返回
- **流畅动画**：使用 iOS 系统级别的弹性动画

### 1.2 原生实现原理

```swift
// iOS 原生通过 UINavigationController 的 interactivePopGestureRecognizer
// 这是一个 UIScreenEdgePanGestureRecognizer 实例
navigationController?.interactivePopGestureRecognizer?.isEnabled = true
```

`UIScreenEdgePanGestureRecognizer` 专门用于检测从屏幕边缘开始的手势，只有起点在指定边缘区域内才会识别。

### 1.3 关键特性

| 特性 | 说明 |
|------|------|
| 触发区域 | 左边缘约 0-30pt |
| 方向 | 从左向右（水平为主） |
| 阈值 | 约 50% 屏幕宽度 |
| 动画 | 实时跟手 + 弹性回弹 |
| 导航栈 | 基于 UINavigationController 的 push/pop |

---

## 2. Web 端实现的核心挑战

在 Web 应用中复现这一交互存在以下挑战：

### 2.1 浏览器手势冲突
- iOS Safari 自身在 `pushState` 导航时有内置的边缘滑动返回行为，但仅对**真实的历史导航**生效
- 如果 Web 应用使用 SPA 路由（如 Vue Router、React Router），Safari 的原生滑动返回可能与 SPA 路由冲突
- `overscroll-behavior` 可以禁用浏览器的默认滚动链行为

### 2.2 触摸事件拦截
- 浏览器可能在手势开始时就将其识别为页面滚动，导致 `pointercancel`
- 需要通过 `touch-action` CSS 属性提前告知浏览器意图

### 2.3 视觉效果实现
- 原生滑动返回有两个页面同时移动（当前页面右移、下层页面可见）
- Web 端需要通过 CSS `transform` + 层叠上下文模拟

### 2.4 导航历史管理
- SPA 需要正确配合 `history.pushState()` / `history.back()` / `popstate` 事件
- 需要处理历史栈的边界情况

---

## 3. 技术方案总览

| 方案 | 适用场景 | 复杂度 | 还原度 | 兼容性 |
|------|----------|--------|--------|--------|
| Touch Events + History API | 纯 Web/PWA | 中 | ★★★☆ | 优秀 |
| overscroll-behavior + 边缘检测 | 简单场景 | 低 | ★★☆ | iOS 16+ |
| View Transitions API + 手势 | 现代浏览器 | 高 | ★★★★ | iOS 18.2+ |
| WKWebView 原生桥接 | 混合 App | 中 | ★★★★★ | 仅 Hybrid |
| 框架插件（vue-swipe-back 等） | Vue/React | 低 | ★★★ | 依框架 |

---

## 4. 方案一：Touch/Pointer Events + History API（纯 Web 方案）

### 4.1 核心思路

1. 监听 `touchstart` / `touchmove` / `touchend`（或 `pointerdown` / `pointermove` / `pointerup`）
2. 判断触摸起点是否在左边缘区域（如 `clientX < 30`）
3. 判断滑动方向是否为从左到右（`deltaX > 0`）
4. 实时更新当前页面的 `transform: translateX()` 实现跟手效果
5. 松手时根据滑动距离/速度决定是否执行返回

### 4.2 关键代码结构

```javascript
class SwipeBackHandler {
  constructor(options = {}) {
    this.edgeWidth = options.edgeWidth || 30;       // 边缘触发宽度
    this.threshold = options.threshold || 0.3;       // 完成阈值（屏宽比例）
    this.maxOpacity = options.maxOpacity || 0.6;     // 下层页面阴影
    this.active = false;
    this.startX = 0;
    this.startY = 0;
    this.currentX = 0;
    this.currentPage = null;
    this.underPage = null;
    
    this.onTouchStart = this.onTouchStart.bind(this);
    this.onTouchMove = this.onTouchMove.bind(this);
    this.onTouchEnd = this.onTouchEnd.bind(this);
  }

  init() {
    document.addEventListener('touchstart', this.onTouchStart, { passive: false });
    document.addEventListener('touchmove', this.onTouchMove, { passive: false });
    document.addEventListener('touchend', this.onTouchEnd, { passive: false });
  }

  destroy() {
    document.removeEventListener('touchstart', this.onTouchStart);
    document.removeEventListener('touchmove', this.onTouchMove);
    document.removeEventListener('touchend', this.onTouchEnd);
  }

  onTouchStart(e) {
    const touch = e.touches[0];
    
    // 仅在左边缘区域触发
    if (touch.clientX > this.edgeWidth) return;
    
    // 确保有历史记录可返回
    if (!window.history.length || window.history.length <= 1) return;
    
    this.active = true;
    this.startX = touch.clientX;
    this.startY = touch.clientY;
    this.currentX = touch.clientX;
    
    // 创建/获取下层页面预览
    this.preparePages();
  }

  onTouchMove(e) {
    if (!this.active) return;
    
    const touch = e.touches[0];
    const deltaX = touch.clientX - this.startX;
    const deltaY = touch.clientY - this.startY;
    
    // 如果垂直移动大于水平移动，取消手势
    if (Math.abs(deltaY) > Math.abs(deltaX) && deltaX < 10) {
      this.cancel();
      return;
    }
    
    // 阻止默认行为（页面滚动）
    e.preventDefault();
    
    this.currentX = touch.clientX;
    const progress = Math.min(deltaX / window.innerWidth, 1);
    
    // 实时更新当前页位置
    this.updateTransform(deltaX, progress);
  }

  onTouchEnd(e) {
    if (!this.active) return;
    
    const deltaX = this.currentX - this.startX;
    const threshold = window.innerWidth * this.threshold;
    
    if (deltaX > threshold) {
      // 完成返回
      this.complete();
    } else {
      // 取消，弹回
      this.cancel();
    }
  }

  preparePages() {
    this.currentPage = document.querySelector('.page-current');
    // 可以创建下层页面的快照或使用已缓存的 DOM
    this.underPage = document.querySelector('.page-previous');
    if (this.underPage) {
      this.underPage.style.display = 'block';
      this.underPage.style.transform = 'translateX(-30%) scale(0.95)';
      this.underPage.style.opacity = '0.8';
      this.underPage.style.transition = 'none';
    }
  }

  updateTransform(deltaX, progress) {
    if (this.currentPage) {
      this.currentPage.style.transform = `translateX(${deltaX}px)`;
      this.currentPage.style.transition = 'none';
      // 添加阴影增强深度感
      this.currentPage.style.boxShadow = 
        `${-10 * progress}px 0 30px rgba(0,0,0,${0.3 * progress})`;
    }
    if (this.underPage) {
      const underProgress = Math.min(progress / 0.3, 1);
      this.underPage.style.transform = 
        `translateX(${-30 * (1 - underProgress)}%) scale(${0.95 + 0.05 * underProgress})`;
      this.underPage.style.opacity = `${0.8 + 0.2 * underProgress}`;
    }
  }

  complete() {
    if (this.currentPage) {
      this.currentPage.style.transition = 'transform 0.3s ease-out';
      this.currentPage.style.transform = `translateX(100%)`;
    }
    if (this.underPage) {
      this.underPage.style.transition = 'all 0.3s ease-out';
      this.underPage.style.transform = 'translateX(0) scale(1)';
      this.underPage.style.opacity = '1';
    }
    
    setTimeout(() => {
      window.history.back();
      this.reset();
    }, 300);
  }

  cancel() {
    this.active = false;
    if (this.currentPage) {
      this.currentPage.style.transition = 'transform 0.3s ease-out';
      this.currentPage.style.transform = 'translateX(0)';
      this.currentPage.style.boxShadow = 'none';
    }
    if (this.underPage) {
      this.underPage.style.transition = 'all 0.3s ease-out';
      this.underPage.style.transform = 'translateX(-30%) scale(0.95)';
      this.underPage.style.opacity = '0.8';
    }
    
    setTimeout(() => this.reset(), 300);
  }

  reset() {
    this.active = false;
    this.startX = 0;
    this.startY = 0;
    this.currentX = 0;
    // 清理样式
    if (this.currentPage) {
      this.currentPage.style.transition = '';
      this.currentPage.style.transform = '';
      this.currentPage.style.boxShadow = '';
    }
    if (this.underPage) {
      this.underPage.style.display = '';
      this.underPage.style.transition = '';
      this.underPage.style.transform = '';
      this.underPage.style.opacity = '';
    }
    this.currentPage = null;
    this.underPage = null;
  }
}
```

### 4.3 配套 CSS

```css
/* 确保页面容器是相对定位 */
.page-current,
.page-previous {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  will-change: transform;
  z-index: 2; /* 当前页在上层 */
}

.page-previous {
  z-index: 1;
  display: none; /* 默认隐藏 */
}

/* 关键：设置 touch-action 避免浏览器拦截水平手势 */
.swipe-back-enabled {
  touch-action: pan-y; /* 允许垂直滚动，水平交给 JS 处理 */
}

/* 或者更精确地控制边缘区域 */
.edge-zone {
  touch-action: none;
}
```

---

## 5. 方案二：overscroll-behavior + 边缘检测

### 5.1 原理

利用 `overscroll-behavior-x: contain` 禁用浏览器默认的水平滑动导航行为，然后在 JS 中自行处理边缘手势。

### 5.2 实现

```css
html, body {
  overscroll-behavior-x: contain; /* 禁用浏览器默认水平滑动导航 */
}
```

```javascript
// 配合方案一的 Touch Events 逻辑
// overscroll-behavior 确保浏览器不会抢先处理手势
```

### 5.3 注意事项

- `overscroll-behavior: contain` 可以禁用 iOS Safari 的原生边缘滑动返回
- 如果想**保留** Safari 原生返回行为同时添加自定义效果，需要小心处理
- 在 iOS Safari 中，`overscroll-behavior-x: none` 也可以阻止边缘滑动

---

## 6. 方案三：View Transitions API + 手势驱动

### 6.1 概述

View Transitions API（iOS 18.2+ Safari 支持）提供了原生的页面过渡动画能力，可以与手势结合实现更流畅的效果。

### 6.2 基本用法

```javascript
// 页面导航时启动 View Transition
function navigateBack() {
  if (!document.startViewTransition) {
    window.history.back();
    return;
  }
  
  const transition = document.startViewTransition(() => {
    window.history.back();
  });
  
  // 自定义动画
  transition.ready.then(() => {
    document.documentElement.animate(
      {
        transform: ['translateX(0)', 'translateX(100%)'],
      },
      {
        duration: 300,
        easing: 'ease-out',
        pseudoElement: '::view-transition-old(root)',
      }
    );
  });
}
```

### 6.3 与手势结合

```javascript
// 在 touchmove 中实时更新 View Transition
// 注意：View Transitions API 的手势集成仍在演进中
// 目前需要手动配合 transform 实现

let vtTransition = null;

async function startSwipeBackTransition() {
  if (!document.startViewTransition) return null;
  
  // 捕获当前页面快照
  vtTransition = document.startViewTransition(() => {
    // 回调中不做实际 DOM 变更，仅捕获快照
  });
  
  await vtTransition.ready;
  return vtTransition;
}
```

### 6.4 兼容性

| 浏览器 | 支持版本 |
|--------|----------|
| Safari iOS | 18.2+ |
| Chrome Android | 111+ |
| Firefox | 不支持（截至 2025） |

> ⚠️ View Transitions API 在 iOS 上支持较新，需要做降级处理。

---

## 7. 方案四：混合 App（WKWebView）原生桥接

### 7.1 适用场景

如果 Web 内容运行在 iOS 原生 App 的 `WKWebView` 中，可以：

1. 在原生层实现 `UIScreenEdgePanGestureRecognizer`
2. 通过 `WKScriptMessageHandler` 将手势事件传递给 Web 层
3. Web 层接收事件后执行页面动画和路由返回

### 7.2 原生侧代码

```swift
// ViewController.swift
import WebKit

class WebViewController: UIViewController {
    var webView: WKWebView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // 配置 WebView
        let config = WKWebViewConfiguration()
        let contentController = WKUserContentController()
        contentController.add(self, name: "swipeBack")
        config.userContentController = contentController
        
        webView = WKWebView(frame: view.bounds, configuration: config)
        view.addSubview(webView)
        
        // 添加原生边缘手势
        let edgePan = UIScreenEdgePanGestureRecognizer(
            target: self,
            action: #selector(handleEdgePan(_:))
        )
        edgePan.edges = .left
        view.addGestureRecognizer(edgePan)
    }
    
    @objc func handleEdgePan(_ gesture: UIScreenEdgePanGestureRecognizer) {
        let translation = gesture.translation(in: view)
        let progress = min(translation.x / view.bounds.width, 1.0)
        
        switch gesture.state {
        case .changed:
            // 实时传递进度给 Web
            let js = "window.__swipeBackProgress(\(progress));"
            webView.evaluateJavaScript(js)
            
        case .ended, .cancelled:
            let shouldComplete = progress > 0.5 || 
                gesture.velocity(in: view).x > 500
            
            let js = shouldComplete 
                ? "window.__swipeBackComplete();" 
                : "window.__swipeBackCancel();"
            webView.evaluateJavaScript(js)
            
        default:
            break
        }
    }
}
```

### 7.3 Web 侧接收

```javascript
// Web 层接收原生手势事件
window.__swipeBackProgress = function(progress) {
  const currentPage = document.querySelector('.page-current');
  if (currentPage) {
    currentPage.style.transition = 'none';
    currentPage.style.transform = `translateX(${progress * 100}%)`;
    currentPage.style.boxShadow = `0 0 30px rgba(0,0,0,${0.3 * progress})`;
  }
};

window.__swipeBackComplete = function() {
  const currentPage = document.querySelector('.page-current');
  if (currentPage) {
    currentPage.style.transition = 'transform 0.3s ease-out';
    currentPage.style.transform = 'translateX(100%)';
    setTimeout(() => {
      window.history.back(); // 或调用原生 pop
    }, 300);
  }
};

window.__swipeBackCancel = function() {
  const currentPage = document.querySelector('.page-current');
  if (currentPage) {
    currentPage.style.transition = 'transform 0.3s ease-out';
    currentPage.style.transform = '';
    currentPage.style.boxShadow = '';
  }
};
```

### 7.4 优势

- **最高还原度**：原生手势识别精度高，不与 WebView 滚动冲突
- **性能优秀**：原生 `UIScreenEdgePanGestureRecognizer` 无延迟
- **不依赖浏览器兼容性**

---

## 8. 框架层面实现

### 8.1 Vue Router

```javascript
// plugins/swipe-back.js
const SwipeBack = {
  install(Vue, options) {
    const handler = new SwipeBackHandler(options);
    
    // 在路由守卫中管理页面栈
    let routeStack = [];
    
    router.afterEach((to, from) => {
      if (router.direction === 'back') {
        routeStack.pop();
      } else {
        routeStack.push(from.path);
      }
    });
    
    // 初始化手势
    Vue.nextTick(() => handler.init());
    
    Vue.prototype.$swipeBack = handler;
  }
};
```

### 8.2 React

```jsx
// hooks/useSwipeBack.js
import { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function useSwipeBack(options = {}) {
  const navigate = useNavigate();
  const handlerRef = useRef(null);
  
  useEffect(() => {
    const handler = new SwipeBackHandler({
      ...options,
      onComplete: () => navigate(-1),
    });
    handler.init();
    handlerRef.current = handler;
    
    return () => handler.destroy();
  }, [navigate]);
  
  return handlerRef;
}

// 使用
function Page() {
  useSwipeBack({ edgeWidth: 30, threshold: 0.3 });
  return <div className="page">...</div>;
}
```

### 8.3 现成库推荐

| 库名 | 框架 | 特点 |
|------|------|------|
| `vue-page-transition` | Vue 3 | 内置多种页面过渡，可配合手势 |
| `react-swipeable` | React | 通用手势识别，需自行实现动画 |
| `swiper` | 框架无关 | 主要用于轮播，但可适配页面切换 |
| `sheetjs/swipe-back` | 通用 | 轻量级滑动返回 |

---

## 9. 关键 CSS 属性详解

### 9.1 `touch-action`

控制浏览器对触摸手势的处理方式，是实现自定义手势的基础。

```css
/* 允许垂直滚动，水平手势交给 JS */
.swipe-back-zone {
  touch-action: pan-y;
}

/* 完全禁用浏览器手势处理 */
.swipe-back-zone {
  touch-action: none;
}

/* 仅允许向右滑动（即从左边缘开始的滑动） */
.swipe-back-zone {
  touch-action: pan-right;
}
```

**关键值说明：**
- `pan-y`：允许垂直滚动，水平交给 JS — **推荐用于边缘区域**
- `pan-right`：仅允许向右方向的滚动 — 适合左边缘返回
- `none`：完全交给 JS — 适合全屏手势场景

### 9.2 `overscroll-behavior`

控制滚动到边界时的行为。

```css
/* 禁用水平方向的滚动链和边缘滑动导航 */
html {
  overscroll-behavior-x: contain;
}
```

**与滑动返回的关系：**
- `contain`：禁用 Safari 的原生边缘滑动返回，让 JS 完全接管
- `none`：禁用所有 overscroll 效果（包括弹性滚动）
- `auto`（默认）：保持浏览器默认行为

### 9.3 `will-change`

优化动画性能：

```css
.page-current {
  will-change: transform;
}
```

### 9.4 `position: sticky` / `fixed`

确保页面容器在滑动时不脱离视口：

```css
.page-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
```

---

## 10. iOS Safari 特殊行为与限制

### 10.1 Safari 原生边缘滑动

iOS Safari 在以下条件下会触发原生滑动返回：
- 使用了真实的 `pushState` / `history.back()` 导航
- 触摸起点在屏幕左边缘
- 页面没有 `overscroll-behavior-x: contain/none`

### 10.2 与 SPA 路由的冲突

**问题：** SPA 路由使用 `pushState` 但不真正加载新页面，Safari 仍然会在边缘滑动时触发 `popstate`。

**解决方案：**

```javascript
// 方案 A：保留 Safari 原生行为，监听 popstate 处理 SPA 路由
window.addEventListener('popstate', (event) => {
  if (event.state && event.state.route) {
    router.replace(event.state.route);
  }
});

// 方案 B：禁用 Safari 原生行为，完全自定义
html { overscroll-behavior-x: contain; }
```

### 10.3 `position: fixed` 在 iOS 上的问题

iOS Safari 中 `position: fixed` 元素在页面滚动时可能错位，建议使用：

```css
.app-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: scroll;
  -webkit-overflow-scrolling: touch;
}
```

### 10.4 安全区适配

```css
.page-content {
  padding-top: env(safe-area-inset-top);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
```

### 10.5 100vh 问题

iOS Safari 的地址栏伸缩会导致 `100vh` 不准确：

```css
.page-container {
  height: 100dvh; /* 动态视口高度，推荐 */
  /* 降级方案 */
  height: 100vh;
}
```

---

## 11. 最佳实践与避坑指南

### 11.1 性能优化

1. **使用 `will-change: transform`** 告知浏览器即将变化的属性
2. **仅使用 `transform` 和 `opacity`** 做动画，避免触发 layout/paint
3. **使用 `requestAnimationFrame`** 节流 touchmove 中的更新
4. **避免在 touchmove 中读取布局属性**（如 `getBoundingClientRect`）

```javascript
let ticking = false;

function onTouchMove(e) {
  if (!active || ticking) return;
  ticking = true;
  
  requestAnimationFrame(() => {
    updateTransform(e.touches[0].clientX);
    ticking = false;
  });
}
```

### 11.2 手势判断优化

```javascript
// 初始手势方向判断，避免误触发
const ANGLE_THRESHOLD = Math.PI / 6; // 30度

function isHorizontalSwipe(deltaX, deltaY) {
  const angle = Math.atan2(Math.abs(deltaY), Math.abs(deltaX));
  return angle < ANGLE_THRESHOLD && deltaX > 0;
}

// 速度判断
function shouldComplete(velocity, distance, screenWidth) {
  return distance > screenWidth * 0.3 || velocity > 500;
}
```

### 11.3 常见坑

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 手势不触发 | 浏览器先处理为滚动 | 设置 `touch-action: pan-y` |
| 页面跟随卡顿 | 没有用 transform | 只用 `translateX` 而非 `left` |
| 动画结束后页面残留 | transition 未清除 | 在 `transitionend` 中重置样式 |
| iOS 底部白条遮挡 | 安全区未适配 | 使用 `env(safe-area-inset-*)` |
| 多次触发返回 | 事件未销毁 | 在 `destroy` 中 `removeEventListener` |
| iframe 中不生效 | touch-action 无法穿透 | 在 iframe 内部也设置相关 CSS |

### 11.4 辅助功能

```javascript
// 尊重用户的减少动画偏好
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion) {
  // 直接执行返回，不做动画
  window.history.back();
  return;
}
```

---

## 12. 方案对比与推荐

### 12.1 决策树

```
应用类型？
├── 混合 App (WKWebView)
│   └── → 方案四：原生桥接（还原度最高）
├── PWA / 纯 Web
│   ├── 需要支持 iOS 18.2+？
│   │   └── → 方案三：View Transitions API（体验最好）
│   └── 需要广泛兼容？
│       └── → 方案一 + 方案二：Touch Events + overscroll-behavior
└── 框架项目 (Vue/React)
    └── → 方案一封装为组件/Hook
```

### 12.2 推荐配置

对于大多数 Web 应用，推荐 **方案一 + 方案二** 的组合：

```css
/* 1. 禁用浏览器默认边缘滑动 */
html {
  overscroll-behavior-x: contain;
}

/* 2. 边缘区域设置 touch-action */
body {
  touch-action: pan-y;
}
```

```javascript
// 3. 初始化手势处理器
const swipeBack = new SwipeBackHandler({
  edgeWidth: 30,      // 左边缘 30px 触发
  threshold: 0.3,     // 滑动 30% 屏宽完成返回
  velocityThreshold: 500, // 或速度 > 500px/s
});
swipeBack.init();
```

---

## 13. 参考代码：完整实现示例

以下是可直接使用的完整 HTML 示例：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" 
        content="width=device-width, initial-scale=1.0, 
        maximum-scale=1.0, user-scalable=no, 
        viewport-fit=cover">
  <title>Swipe Back Demo</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }
    
    html {
      overscroll-behavior-x: contain;
    }
    
    body {
      touch-action: pan-y;
      overflow: hidden;
    }
    
    .app {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100dvh;
      overflow: hidden;
    }
    
    .page {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      will-change: transform;
      padding-top: env(safe-area-inset-top);
      padding-bottom: env(safe-area-inset-bottom);
    }
    
    .page-current {
      z-index: 10;
      background: #fff;
      transform: translateX(0);
    }
    
    .page-previous {
      z-index: 5;
      background: #f0f0f0;
      transform: translateX(-30%) scale(0.95);
      opacity: 0.6;
      display: none;
    }
    
    .page-content {
      padding: 20px;
      padding-top: calc(env(safe-area-inset-top) + 60px);
    }
    
    .nav-bar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: calc(44px + env(safe-area-inset-top));
      padding-top: env(safe-area-inset-top);
      display: flex;
      align-items: center;
      padding-left: 16px;
      padding-right: 16px;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      z-index: 100;
      border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    
    .nav-back {
      font-size: 17px;
      color: #007aff;
      cursor: pointer;
    }
    
    .nav-title {
      flex: 1;
      text-align: center;
      font-size: 17px;
      font-weight: 600;
    }
    
    .item {
      padding: 16px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
    }
    
    .item:active {
      background: #f5f5f5;
    }
  </style>
</head>
<body>
  <div class="app" id="app">
    <!-- 页面内容动态渲染 -->
  </div>
  
  <script>
    // —— 路由管理 ——
    const pages = [
      { title: '首页', items: Array.from({length: 20}, (_, i) => `列表项 ${i+1}`) },
    ];
    let pageIndex = 0;
    
    function renderPage(page, isPrevious = false) {
      const className = isPrevious ? 'page page-previous' : 'page page-current';
      return `
        <div class="${className}" data-index="${page.index}">
          <div class="nav-bar">
            ${page.index > 0 ? '<span class="nav-back" onclick="goBack()">‹ 返回</span>' : '<span></span>'}
            <span class="nav-title">${page.title}</span>
            <span></span>
          </div>
          <div class="page-content">
            ${page.items.map(item => `<div class="item" onclick="navigateTo(${page.index + 1})">${item}</div>`).join('')}
          </div>
        </div>
      `;
    }
    
    function navigateTo(index) {
      const newPage = {
        index,
        title: `页面 ${index + 1}`,
        items: Array.from({length: 15}, (_, i) => `页面${index+1} - 项目 ${i+1}`),
      };
      pages.push(newPage);
      history.pushState({ index }, '', `#page${index}`);
      updateView();
    }
    
    function goBack() {
      if (pages.length > 1) {
        history.back();
      }
    }
    
    function updateView() {
      const app = document.getElementById('app');
      const current = pages[pages.length - 1];
      const previous = pages.length > 1 ? pages[pages.length - 2] : null;
      
      app.innerHTML = renderPage(current) + (previous ? renderPage(previous, true) : '');
    }
    
    window.addEventListener('popstate', (e) => {
      if (pages.length > 1) {
        pages.pop();
        updateView();
      }
    });
    
    // —— 滑动返回手势 ——
    class SwipeBack {
      constructor() {
        this.edgeWidth = 30;
        this.threshold = 0.3;
        this.active = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.startTime = 0;
      }
      
      init() {
        document.addEventListener('touchstart', this.onStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.onMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.onEnd.bind(this), { passive: false });
      }
      
      onStart(e) {
        if (pages.length <= 1) return;
        
        const touch = e.touches[0];
        if (touch.clientX > this.edgeWidth) return;
        
        this.active = true;
        this.startX = touch.clientX;
        this.startY = touch.clientY;
        this.currentX = touch.clientX;
        this.startTime = Date.now();
        
        // 显示下层页面
        const prev = document.querySelector('.page-previous');
        if (prev) prev.style.display = 'block';
      }
      
      onMove(e) {
        if (!this.active) return;
        
        const touch = e.touches[0];
        const deltaX = touch.clientX - this.startX;
        const deltaY = touch.clientY - this.startY;
        
        // 垂直滑动则取消
        if (Math.abs(deltaY) > Math.abs(deltaX) && deltaX < 10) {
          this.cancel();
          return;
        }
        
        e.preventDefault();
        this.currentX = touch.clientX;
        
        const current = document.querySelector('.page-current');
        const prev = document.querySelector('.page-previous');
        
        if (current) {
          current.style.transition = 'none';
          current.style.transform = `translateX(${Math.max(0, deltaX)}px)`;
          const progress = Math.min(deltaX / window.innerWidth, 1);
          current.style.boxShadow = `0 0 ${30 * progress}px rgba(0,0,0,${0.3 * progress})`;
        }
        
        if (prev) {
          const progress = Math.min(deltaX / window.innerWidth, 1);
          prev.style.transition = 'none';
          prev.style.transform = `translateX(${-30 * (1 - progress)}%) scale(${0.95 + 0.05 * progress})`;
          prev.style.opacity = `${0.6 + 0.4 * progress}`;
        }
      }
      
      onEnd(e) {
        if (!this.active) return;
        
        const deltaX = this.currentX - this.startX;
        const duration = Date.now() - this.startTime;
        const velocity = duration > 0 ? (deltaX / duration) * 1000 : 0;
        const threshold = window.innerWidth * this.threshold;
        
        if (deltaX > threshold || velocity > 500) {
          this.complete();
        } else {
          this.cancel();
        }
      }
      
      complete() {
        const current = document.querySelector('.page-current');
        const prev = document.querySelector('.page-previous');
        
        if (current) {
          current.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          current.style.transform = 'translateX(100%)';
        }
        if (prev) {
          prev.style.transition = 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          prev.style.transform = 'translateX(0) scale(1)';
          prev.style.opacity = '1';
        }
        
        setTimeout(() => {
          goBack();
          this.reset();
        }, 300);
      }
      
      cancel() {
        this.active = false;
        const current = document.querySelector('.page-current');
        const prev = document.querySelector('.page-previous');
        
        if (current) {
          current.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          current.style.transform = '';
          current.style.boxShadow = '';
        }
        if (prev) {
          prev.style.transition = 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          prev.style.transform = 'translateX(-30%) scale(0.95)';
          prev.style.opacity = '0.6';
          setTimeout(() => { prev.style.display = 'none'; }, 300);
        }
        
        setTimeout(() => this.reset(), 300);
      }
      
      reset() {
        this.active = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
      }
    }
    
    // 初始化
    updateView();
    const swipeBack = new SwipeBack();
    swipeBack.init();
    
    // 尊重减少动画偏好
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      swipeBack.edgeWidth = 0; // 禁用滑动返回
    }
  </script>
</body>
</html>
```

---

## 总结

| 维度 | 推荐 |
|------|------|
| **纯 Web/PWA** | Touch Events + `overscroll-behavior: contain` + `touch-action: pan-y` |
| **现代浏览器 (iOS 18.2+)** | 可叠加 View Transitions API 获得更好体验 |
| **Hybrid App** | WKWebView + `UIScreenEdgePanGestureRecognizer` 原生桥接 |
| **关键 CSS** | `touch-action`, `overscroll-behavior`, `will-change: transform` |
| **关键 JS** | Touch/Pointer Events, `history.pushState/back()`, `popstate` |
| **性能要点** | 仅用 `transform`/`opacity` 做动画, 用 `requestAnimationFrame` 节流 |
| **iOS 适配** | `env(safe-area-inset-*)`, `100dvh`, `-webkit-overflow-scrolling: touch` |

核心实现思路：**在左边缘区域监听触摸事件 → 实时 `translateX` 跟手 → 松手后根据距离/速度决定返回或弹回 → 配合 `history.back()` 完成导航**。配合 CSS `touch-action` 和 `overscroll-behavior` 避免与浏览器默认行为冲突。
