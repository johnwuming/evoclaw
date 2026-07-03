# R-128 DateFate 页面设计方案

> **研究日期**：2026-07-03 | **研究类型**：产品设计文档 | **编号**：R-128
> **调研依据**：R-123（MysticMirror竞品分析）、R-110（AI塔罗牌市场调研）、R-112（MysticMirror PRD）、R-122（高转化占卜独立站设计风格）
> **数据说明**：基于已有调研报告+任务需求直接撰写，搜索员补充数据未及时到达，以baseline方式交付

---

## 一、产品定位与设计总纲

### 1.1 产品概要

| 维度 | 定义 |
|------|------|
| **产品名** | DateFate |
| **一句话定位** | "Before the date, know your fate — AI-powered love tarot & astrology" |
| **核心场景** | 约会前轻量运势查询，爱情关系聚焦 |
| **目标用户** | 美国 18-35 岁女性 |
| **视觉风格** | 粉紫温柔风（Pink-Purple Soft Aesthetic） |
| **产品形态** | Web 优先独立站（响应式，移动端为主） |
| **文化体系** | 纯西方塔罗 + 星座（无东方玄学元素） |

### 1.2 免费层 vs 付费层

| 层级 | 内容 | 价格 | 转化目标 |
|------|------|------|---------|
| **免费层** | 10秒速查：今日爱情运势 + 一张塔罗指引牌 | $0 | 获客、建立习惯 |
| **付费层** | 深度AI解读：关系塔罗牌阵 + 星盘合盘分析 | $4.99-9.99 | 变现 |

### 1.3 设计原则

1. **温柔而非恐怖** — 打破塔罗必须暗黑神秘的刻板印象，采用 Pocket Tarot 式的温柔粉紫风格
2. **10秒价值承诺** — 免费层必须在10秒内给用户一个"wow"体验
3. **情感导航工具** — 定位为"自我探索与关系洞察"，不是"算命预测"
4. **社交分享优先** — 每个结果都必须可生成精美分享卡片
5. **去专业化文案** — 不用占星术语，用日常情感语言（参考 The Pattern "without complicated astrology language"）

---

## 二、配色方案（Color System）

### 2.1 主调色板（Pink-Purple Soft Aesthetic）

基于 MysticMirror 现有配色体系扩展：

```css
:root {
  /* === 背景层级 === */
  --bg-primary: #FAF5FF;       /* 极浅薰衣草白 — 页面主背景 */
  --bg-secondary: #FDF4FF;    /* 淡粉白 — 区块交替背景 */
  --bg-card: #FFFFFF;          /* 纯白 — 卡片背景 */
  --bg-card-hover: #F5F0FF;    /* 极浅紫 — 卡片悬停态 */
  --bg-overlay: rgba(168, 85, 247, 0.05); /* 紫色极浅叠加 */

  /* === 品牌强调色 === */
  --brand-purple: #A855F7;     /* 主紫 — CTA按钮、链接、图标 */
  --brand-pink: #EC4899;       /* 主粉 — 次强调、渐变终点 */
  --brand-purple-light: #C084FC; /* 浅紫 — 图标背景、标签 */
  --brand-pink-light: #F472B6;  /* 浅粉 — 通知、徽章 */
  --brand-purple-dark: #7C3AED;  /* 深紫 — hover状态 */
  --brand-pink-dark: #DB2777;   /* 深粉 — active状态 */

  /* === 渐变系统 === */
  --gradient-primary: linear-gradient(135deg, #A855F7 0%, #EC4899 100%);
  --gradient-soft: linear-gradient(135deg, #E9D5FF 0%, #FBCFE8 100%);
  --gradient-hero: linear-gradient(180deg, #FAF5FF 0%, #FDF4FF 50%, #FFF1F8 100%);
  --gradient-card: linear-gradient(145deg, rgba(168,85,247,0.08) 0%, rgba(236,72,153,0.08) 100%);
  --gradient-cta: linear-gradient(135deg, #A855F7 0%, #EC4899 50%, #A855F7 100%);
  --gradient-cta-hover: linear-gradient(135deg, #7C3AED 0%, #DB2777 50%, #7C3AED 100%);

  /* === 文字层级 === */
  --text-primary: #2D2D44;     /* 深紫灰 — 主文字 */
  --text-secondary: #6B6B80;   /* 中灰紫 — 副文字 */
  --text-tertiary: #9B9BB0;    /* 浅灰紫 — 辅助文字 */
  --text-on-brand: #FFFFFF;   /* 白色 — 按钮上的文字 */
  --text-accent: #A855F7;      /* 品牌紫 — 链接文字 */

  /* === 边框与分割 === */
  --border-light: rgba(168, 85, 247, 0.12);
  --border-medium: rgba(168, 85, 247, 0.25);
  --divider: rgba(168, 85, 247, 0.08);

  /* === 阴影系统 === */
  --shadow-sm: 0 2px 8px rgba(168, 85, 247, 0.06);
  --shadow-md: 0 4px 16px rgba(168, 85, 247, 0.10);
  --shadow-lg: 0 8px 32px rgba(168, 85, 247, 0.12);
  --shadow-xl: 0 16px 48px rgba(168, 85, 247, 0.16);
  --shadow-glow: 0 0 24px rgba(168, 85, 247, 0.20);

  /* === 语义色 === */
  --success: #10B981;           /* 好运/正面 */
  --warning: #F59E0B;          /* 需注意 */
  --love: #EC4899;             /* 爱情/浪漫 */
  --intuition: #A855F7;        /* 直觉/灵性 */
  --passion: #EF4444;          /* 热情/激情 */
}
```

### 2.2 语义色使用规则

| 场景 | 色值 | 说明 |
|------|------|------|
| 好运/正面牌 | `--success` #10B981 | 权杖、圣杯正位 |
| 爱情相关 | `--love` #EC4899 | 恋人、圣杯系列 |
| 需要注意 | `--warning` #F59E0B | 逆位牌、挑战提示 |
| 灵性/直觉 | `--intuition` #A855F7 | 高塔、命运之轮 |
| 免费功能标签 | `--success` + 浅背景 | "FREE" 徽章 |

### 2.3 深色模式（Dark Mode）— 可选 V2

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0F0A1A;
    --bg-secondary: #1A1028;
    --bg-card: #1E1433;
    --text-primary: #F0ECF5;
    --text-secondary: #A89FC0;
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
    /* ... 保持品牌色不变，只反转背景和文字 */
  }
}
```

---

## 三、字体方案（Typography）

### 3.1 字体选择

| 用途 | 字体 | 字重 | 回退字体 | 说明 |
|------|------|------|---------|------|
| **标题/品牌** | Cormorant Garamond | 400, 500, 600, 700 | Georgia, serif | 优雅古典，神秘高雅感 |
| **副标题** | DM Sans | 500, 600, 700 | system-ui, sans-serif | 现代干净，比Inter更柔和 |
| **正文** | DM Sans | 400, 500 | system-ui, sans-serif | 高可读性，友好的x-height |
| **塔罗牌名** | Cinzel | 400, 600 | Georgia, serif | 罗马式碑文，仪式感 |
| **CTA按钮** | DM Sans | 600, 700 | system-ui, sans-serif | 清晰有力 |
| **价格数字** | Space Grotesk | 500, 700 | monospace | 现代感，对齐好看 |

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Cinzel:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
```

### 3.2 字体使用规则

```css
:root {
  --font-display: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-tarot: 'Cinzel', Georgia, serif;
  --font-mono: 'Space Grotesk', monospace;
}
```

| 元素 | 字体 | 大小 | 行高 | 字间距 |
|------|------|------|------|--------|
| Hero 主标题 | display | 48-64px / 3-4rem | 1.1 | -0.02em |
| H2 区块标题 | display | 32-40px / 2-2.5rem | 1.2 | -0.01em |
| H3 卡片标题 | body | 20-24px / 1.25-1.5rem | 1.3 | 0 |
| 正文 | body | 16px / 1rem | 1.6 | 0.01em |
| 辅助文字 | body | 14px / 0.875rem | 1.5 | 0.02em |
| CTA 按钮 | body | 16-18px / 1-1.125rem | 1 | 0.05em |
| 塔罗牌名 | tarot | 18-22px / 1.125-1.375rem | 1.2 | 0.1em |
| 价格 | mono | 32-48px / 2-3rem | 1 | -0.02em |
| 标签/Badge | body | 12-13px | 1 | 0.05em |

---

## 四、页面结构设计

### 4.1 全局布局

```
┌─────────────────────────────────────────┐
│  Navigation Bar (fixed/sticky)          │
│  [Logo]          [Features] [Pricing]   │
│                   [Try Free →]          │
├─────────────────────────────────────────┤
│                                         │
│         Page Content (scroll)           │
│                                         │
├─────────────────────────────────────────┤
│  Footer                                 │
│  [About] [Blog] [Privacy] [Terms]      │
│  © 2026 DateFate                        │
└─────────────────────────────────────────┘
```

**导航栏规格**：
- 位置：Sticky top，高度 64px
- 背景：`rgba(250, 245, 255, 0.85)` + `backdrop-blur: 16px`
- 底部边框：1px solid `var(--border-light)`
- Logo：左侧，Cormorant Garamond 字体，渐变色文字
- CTA 按钮：右侧，渐变紫粉背景，圆角 pill 形状
- 移动端：Hamburger 菜单 → 全屏滑出面板

### 4.2 全局设计原子

#### 圆角系统

```css
.radius-sm { border-radius: 12px; }   /* 小标签、徽章 */
.radius-md { border-radius: 16px; }   /* 内部元素 */
.radius-lg { border-radius: 22px; }   /* 卡片（核心） */
.radius-xl { border-radius: 28px; }   /* 大卡片、模态框 */
.radius-pill { border-radius: 9999px; } /* 按钮、标签 */
```

#### 间距系统

```css
/* 基于 4px 网格，Tailwind 兼容 */
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;
--space-4: 16px;  --space-5: 20px;  --space-6: 24px;
--space-8: 32px;  --space-10: 40px; --space-12: 48px;
--space-16: 64px; --space-20: 80px; --space-24: 96px;
```

#### CTA 按钮

```css
/* 主按钮 */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  background: var(--gradient-cta);
  color: var(--text-on-brand);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.05em;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-md), 0 0 0 0 rgba(168, 85, 247, 0.4);
}

.btn-primary:hover {
  background: var(--gradient-cta-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 0 20px rgba(168, 85, 247, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

/* 次按钮 */
.btn-secondary {
  /* 相同尺寸 + 透明背景 + 品牌色边框 + 品牌色文字 */
  background: transparent;
  border: 1.5px solid var(--brand-purple);
  color: var(--brand-purple);
}

/* 幽灵按钮 */
.btn-ghost {
  /* 无边框 + 品牌色文字 + hover 浅紫背景 */
}
```

#### 卡片

```css
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg); /* 22px */
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  transition: all 0.3s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-4px);
  border-color: var(--border-medium);
}

/* 品牌渐变边框卡片（Premium 感） */
.card-premium {
  position: relative;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-lg);
}

.card-premium::before {
  content: '';
  position: absolute;
  inset: -1.5px;
  border-radius: calc(var(--radius-xl) + 1.5px);
  background: var(--gradient-primary);
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s;
}

.card-premium:hover::before {
  opacity: 1;
}
```

---

## 五、页面一：首页（Landing Page）

### 5.1 页面区块从上到下

```
╔══════════════════════════════════════════════╗
║  NAV: Logo | Features Pricing | [Try Free →] ║
╠══════════════════════════════════════════════╣
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  HERO SECTION                         ║    ║
║  ║  ✨ 星空粒子动画背景（紫粉渐变）       ║    ║
║  ║                                       ║    ║
║  ║  "See Your Love Story               ║    ║
║  ║   Written in the Stars"              ║    ║
║  ║  （Cormorant Garamond, 56px）         ║    ║
║  ║                                       ║    ║
║  ║  "AI tarot & astrology insights       ║    ║
║  ║   for your relationship journey.      ║    ║
║  ║   Free daily love reading in 10s."   ║    ║
║  ║  （DM Sans, 18px, text-secondary）    ║    ║
║  ║                                       ║    ║
║  ║  [✨ Get Your Free Reading]            ║    ║
║  ║  （主CTA按钮, 渐变紫粉）              ║    ║
║  ║                                       ║    ║
║  ║  "No sign-up required" （小字辅助）   ║    ║
║  ║                                       ║    ║
║  ║  ★★★★★ 50K+ readings done            ║    ║
║  ║  （social proof 紧贴CTA下方）         ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  TRUST STRIP                          ║    ║
║  ║  As seen on: Vogue | Cosmopolitan    ║    ║
║  ║  | TikTok #DateFate                   ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  SOCIAL PROOF                         ║    ║
║  ║  3个用户评价卡片（水平滚动/轮播）     ║    ║
║  ║  "DateFate helped me understand      ║    ║
║  ║   my connection so much better!"      ║    ║
║  ║   — Sarah, 24                         ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  HOW IT WORKS (3步)                  ║    ║
║  ║  ┌────────┐ ┌────────┐ ┌────────┐    ║    ║
║  ║  │ Step 1 │→│ Step 2 │→│ Step 3 │    ║    ║
║  ║  │ Pick   │ │ Get AI │ │ Deeper │    ║    ║
║  ║  │ Question│ │ Reading│ │ Insights│    ║    ║
║  ║  │ or Card│ │ in 10s │ │ optional│    ║    ║
║  ║  └────────┘ └────────┘ └────────┘    ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  FEATURES GRID (6宫格)                ║    ║
║  ║  ┌──────────┐ ┌──────────┐            ║    ║
║  ║  │ 🔮 Daily │ │ 💕 Love  │            ║    ║
║  ║  │   Tarot  │ │   Spread │            ║    ║
║  ║  ├──────────┤ ├──────────┤            ║    ║
║  ║  │ ♈ Couple │ │ 🌙 Birth │            ║    ║
║  ║  │  Synastry│ │  Chart   │            ║    ║
║  ║  ├──────────┤ ├──────────┤            ║    ║
║  ║  │ 📝 Ask   │ │ 🔒 100%  │            ║    ║
║  ║  │  Question│ │ Private  │            ║    ║
║  ║  └──────────┘ └──────────┘            ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  FREE vs PREMIUM 对比表               ║    ║
║  ║  ┌─────────────┬─────────┬──────────┐║    ║
║  ║  │  Feature     │  Free   │ Premium  │║    ║
║  ║  ├─────────────┼─────────┼──────────┤║    ║
║  ║  │ Daily Love  │   ✅    │    ✅    │║    ║
║  ║  │ One Card    │   ✅    │    ✅    │║    ║
║  ║  │ Love Spread │   🔒    │    ✅    │║    ║
║  ║  │ Synastry    │   🔒    │    ✅    │║    ║
║  ║  │ AI Chat     │   🔒    │    ✅    │║    ║
║  ║  │ Price       │  Free   │ $4.99-9.99│║   ║
║  ║  └─────────────┴─────────┴──────────┘║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  FAQ (Accordion, 6-8个常见问题)       ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  ╔═══════════════════════════════════════╗    ║
║  ║  FINAL CTA                            ║    ║
║  ║  "Your love story deserves a deeper    ║    ║
║  ║   look. Start with a free reading."    ║    ║
║  ║  [✨ Try Free — No Sign-Up]            ║    ║
║  ╚═══════════════════════════════════════╝    ║
║                                               ║
║  FOOTER: About | Blog | Privacy | Terms       ║
╚══════════════════════════════════════════════╝
```

### 5.2 各区块详细规格

#### Hero Section

```html
<section class="hero">
  <!-- 星空粒子背景 -->
  <div class="hero-particles" id="particles-bg"></div>
  <!-- 渐变叠加 -->
  <div class="hero-gradient"></div>

  <div class="hero-content">
    <!-- 品牌微标 -->
    <div class="hero-badge">
      <span class="badge-icon">✨</span>
      <span>AI-Powered Love Insights</span>
    </div>

    <h1 class="hero-title">
      See Your Love Story<br>
      <span class="gradient-text">Written in the Stars</span>
    </h1>

    <p class="hero-subtitle">
      AI tarot & astrology insights for your relationship journey.<br>
      Free daily love reading in 10 seconds.
    </p>

    <div class="hero-cta-group">
      <button class="btn-primary btn-xl">
        <span>✨</span> Get Your Free Reading
      </button>
      <span class="hero-cta-note">No sign-up required</span>
    </div>

    <!-- Social proof 紧贴CTA -->
    <div class="hero-proof">
      <div class="stars">★★★★★</div>
      <span>50,000+ readings completed</span>
    </div>
  </div>
</section>
```

```css
.hero {
  position: relative;
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 80px 24px 60px;
  text-align: center;
  background: var(--gradient-hero);
}

.hero-particles {
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0.4;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 640px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: rgba(168, 85, 247, 0.08);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-pill);
  font-size: 14px;
  color: var(--brand-purple);
  margin-bottom: 24px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 56px;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.btn-xl {
  padding: 18px 36px;
  font-size: 18px;
}

.hero-proof {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.hero-proof .stars {
  color: #F59E0B;
}
```

#### Trust Strip

```html
<section class="trust-strip">
  <p class="trust-label">Trusted by people who take love seriously</p>
  <div class="trust-logos">
    <span>Vogue</span>
    <span>Cosmopolitan</span>
    <span>TikTok</span>
    <span>BuzzFeed</span>
  </div>
</section>
```

```css
.trust-strip {
  padding: 32px 24px;
  text-align: center;
  border-top: 1px solid var(--divider);
  border-bottom: 1px solid var(--divider);
  background: var(--bg-primary);
}

.trust-label {
  font-size: 13px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 16px;
}

.trust-logos {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--text-tertiary);
  opacity: 0.6;
}
```

#### Social Proof Section

```html
<section class="social-proof">
  <div class="container">
    <h2>What They're Saying</h2>
    <div class="proof-carousel">
      <div class="proof-card">
        <div class="proof-stars">★★★★★</div>
        <p class="proof-text">"I checked DateFate before my third date. The reading was so accurate about his communication style, it helped me understand him better."</p>
        <div class="proof-author">
          <span class="proof-name">Sarah, 24</span>
          <span class="proof-tag">New York</span>
        </div>
      </div>
      <!-- 更多卡片... -->
    </div>
  </div>
</section>
```

```css
.social-proof {
  padding: var(--space-24) var(--space-6);
  background: var(--bg-secondary);
}

.proof-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.proof-stars { color: #F59E0B; margin-bottom: 12px; font-size: 16px; }

.proof-text {
  font-family: var(--font-display);
  font-style: italic;
  font-size: 17px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.proof-author { display: flex; gap: 8px; align-items: center; }
.proof-name { font-weight: 600; font-size: 15px; }
.proof-tag { font-size: 13px; color: var(--text-tertiary); }
```

#### How It Works

```html
<section class="how-it-works">
  <div class="container">
    <h2>Three Steps to Clarity</h2>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-number">1</div>
        <div class="step-icon">🤔</div>
        <h3>Pick Your Question</h3>
        <p>Choose from love, communication, or compatibility — or ask anything about your relationship.</p>
      </div>
      <div class="step-connector">→</div>
      <div class="step-card">
        <div class="step-number">2</div>
        <div class="step-icon">🔮</div>
        <h3>Get Your Reading</h3>
        <p>AI draws your cards and delivers a personalized love insight in 10 seconds.</p>
      </div>
      <div class="step-connector">→</div>
      <div class="step-card">
        <div class="step-number">3</div>
        <div class="step-icon">💎</div>
        <h3>Go Deeper</h3>
        <p>Unlock a full spread, synastry chart, or AI chat for deeper relationship guidance.</p>
      </div>
    </div>
  </div>
</section>
```

```css
.steps-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: 24px;
  align-items: center;
  max-width: 960px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .steps-grid {
    grid-template-columns: 1fr;
    /* 连接符隐藏，用序号代替 */
  }
  .step-connector { display: none; }
}

.step-card {
  text-align: center;
  padding: 32px 24px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gradient-primary);
  color: white;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 12px;
}

.step-icon { font-size: 36px; margin-bottom: 12px; }
.step-card h3 { font-family: var(--font-display); font-size: 22px; margin-bottom: 8px; }
.step-card p { font-size: 15px; color: var(--text-secondary); line-height: 1.5; }

.step-connector {
  font-size: 24px;
  color: var(--brand-purple);
  opacity: 0.4;
}
```

#### Free vs Premium Pricing Table

```html
<section class="pricing-section">
  <div class="container">
    <h2>Choose Your Depth</h2>
    <div class="pricing-grid">
      <!-- Free -->
      <div class="pricing-card">
        <div class="pricing-badge">Free</div>
        <div class="pricing-price">$0</div>
        <div class="pricing-period">Forever</div>
        <ul class="pricing-features">
          <li class="included">Daily love horoscope</li>
          <li class="included">One card draw per day</li>
          <li class="included">Basic love insight</li>
          <li class="included">Shareable result card</li>
          <li class="excluded">Full tarot spreads</li>
          <li class="excluded">Couple synastry</li>
          <li class="excluded">AI chat follow-up</li>
        </ul>
        <button class="btn-secondary btn-full">Start Free</button>
      </div>

      <!-- Premium: One-time Deep Reading -->
      <div class="pricing-card pricing-card-featured">
        <div class="pricing-popular">Most Popular</div>
        <div class="pricing-badge">Deep Reading</div>
        <div class="pricing-price">$4.99</div>
        <div class="pricing-period">per reading</div>
        <ul class="pricing-features">
          <li class="included">Full love spread (7 cards)</li>
          <li class="included">Detailed AI interpretation</li>
          <li class="included">Past · Present · Future</li>
          <li class="included">Shareable detailed card</li>
          <li class="included">Save to your journal</li>
        </ul>
        <button class="btn-primary btn-full">Get Deep Reading</button>
      </div>

      <!-- Premium: Monthly -->
      <div class="pricing-card">
        <div class="pricing-badge">DateFate Premium</div>
        <div class="pricing-price">$9.99</div>
        <div class="pricing-period">per month</div>
        <ul class="pricing-features">
          <li class="included">Everything in Deep</li>
          <li class="included">Unlimited readings</li>
          <li class="included">Couple synastry chart</li>
          <li class="included">AI chat follow-up</li>
          <li class="included">Weekly love forecast</li>
          <li class="included">Priority insights</li>
        </ul>
        <button class="btn-secondary btn-full">Subscribe</button>
      </div>
    </div>
  </div>
</section>
```

```css
.pricing-section {
  padding: var(--space-24) var(--space-6);
  background: var(--bg-primary);
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1080px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .pricing-grid { grid-template-columns: 1fr; max-width: 400px; }
}

.pricing-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 32px 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  text-align: center;
  position: relative;
}

.pricing-card-featured {
  border-color: transparent;
  box-shadow: var(--shadow-lg);
  transform: scale(1.05);
}

.pricing-popular {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 16px;
  background: var(--gradient-primary);
  color: white;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: var(--radius-pill);
}

.pricing-badge {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.pricing-price {
  font-family: var(--font-mono);
  font-size: 48px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.pricing-period {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 24px;
}

.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  text-align: left;
}

.pricing-features li {
  padding: 8px 0;
  font-size: 15px;
  border-bottom: 1px solid var(--divider);
}

.pricing-features li:last-child { border-bottom: none; }

.pricing-features .included::before {
  content: '✓';
  margin-right: 8px;
  color: var(--success);
  font-weight: 600;
}

.pricing-features .excluded::before {
  content: '—';
  margin-right: 8px;
  color: var(--text-tertiary);
}

.btn-full { width: 100%; }
```

---

## 六、页面二：应用页（App/Reading Page）

### 6.1 页面流程

```
╔════════ 免费体验入口 ════════╗
║                               ║
║  ┌─────────────────────────┐  ║
║  │  Choose Your Question   │  ║
║  │  ┌───────┐ ┌───────┐   │  ║
║  │  │ 💕    │ │ 🗣️    │   │  ║
║  │  │ Love  │ │ Talk  │   │  ║
║  │  └───────┘ └───────┘   │  ║
║  │  ┌───────┐ ┌───────┐   │  ║
║  │  │ 💫    │ │ ❓    │   │  ║
║  │  │ Future│ │ Custom│   │  ║
║  │  └───────┘ └───────┘   │  ║
║  └─────────────────────────┘  ║
║            ↓                   ║
║  ┌─────────────────────────┐  ║
║  │  Draw Your Card         │  ║
║  │  （动画：牌背面在中央）  │  ║
║  │  "Tap to reveal"       │  ║
║  │  [牌面翻转动画]         │  ║
║  └─────────────────────────┘  ║
║            ↓                   ║
║  ┌─────────────────────────┐  ║
║  │  Your Free Reading      │  ║
║  │  ┌─────────────────────┐│  ║
║  │  │  🃏 The Lovers      ││  ║
║  │  │  (card image)       ││  ║
║  │  │                     ││  ║
║  │  │  "A meaningful      ││  ║
║  │  │   connection is      ││  ║
║  │  │   forming..."       ││  ║
║  │  └─────────────────────┘│  ║
║  │                         │  ║
║  │  📤 Share  📋 Save      │  ║
║  │                         │  ║
║  │  ┌─────────────────────┐│  ║
║  │  │ 🔓 Go Deeper        ││  ║
║  │  │ Unlock full spread  ││  ║
║  │  │ + synastry $4.99    ││  ║
║  │  └─────────────────────┘│  ║
║  └─────────────────────────┘  ║
║            ↓                   ║
╚════════ 付费入口 ═════════════╝
```

### 6.2 问题选择页

```html
<section class="question-picker">
  <h2>What's on your heart today?</h2>
  <p class="subtitle">Pick a topic for your free love reading</p>

  <div class="question-grid">
    <button class="question-card" data-topic="love">
      <span class="question-icon">💕</span>
      <span class="question-label">Love & Romance</span>
      <span class="question-desc">How's your love life looking?</span>
    </button>
    <button class="question-card" data-topic="communication">
      <span class="question-icon">🗣️</span>
      <span class="question-label">Communication</span>
      <span class="question-desc">Should you say what's on your mind?</span>
    </button>
    <button class="question-card" data-topic="future">
      <span class="question-icon">💫</span>
      <span class="question-label">Future Potential</span>
      <span class="question-desc">Where is this heading?</span>
    </button>
    <button class="question-card" data-topic="compatibility">
      <span class="question-icon">🔗</span>
      <span class="question-label">Compatibility</span>
      <span class="question-desc">Are you two written in the stars?</span>
    </button>
  </div>

  <div class="custom-question">
    <textarea placeholder="Or ask anything about your relationship..."></textarea>
    <button class="btn-primary">🔮 Draw My Card</button>
  </div>
</section>
```

```css
.question-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-width: 480px;
  margin: 0 auto 32px;
}

@media (max-width: 480px) {
  .question-grid { grid-template-columns: 1fr; }
}

.question-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 16px;
  background: var(--bg-card);
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s ease;
}

.question-card:hover,
.question-card.selected {
  border-color: var(--brand-purple);
  background: var(--bg-card-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.question-icon { font-size: 32px; }
.question-label {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.question-desc {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}
```

### 6.3 抽牌动画页

```html
<section class="card-draw">
  <div class="tarot-card-container">
    <div class="tarot-card" id="tarot-card">
      <!-- 背面 -->
      <div class="card-back">
        <div class="card-back-pattern">
          <!-- 紫粉渐变花纹 SVG -->
        </div>
        <p class="tap-hint">Tap to reveal ✨</p>
      </div>
      <!-- 正面 -->
      <div class="card-front">
        <div class="card-image">
          <!-- 塔罗牌插画 -->
        </div>
        <p class="card-name">The Lovers</p>
        <p class="card-number">VI</p>
      </div>
    </div>
  </div>
</section>
```

```css
.tarot-card-container {
  perspective: 1000px;
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.tarot-card {
  width: 200px;
  height: 340px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.tarot-card.revealed {
  transform: rotateY(180deg);
}

.card-back, .card-front {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-back {
  background: var(--gradient-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-lg), var(--shadow-glow);
}

.card-back-pattern {
  width: 80%;
  height: 80%;
  border: 2px solid rgba(255,255,255,0.2);
  border-radius: var(--radius-md);
  /* 内部花纹用 SVG 或 CSS pattern */
}

.tap-hint {
  font-family: var(--font-body);
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  margin-top: 16px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.card-front {
  transform: rotateY(180deg);
  background: var(--bg-card);
  border: 2px solid var(--border-medium);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  box-shadow: var(--shadow-lg);
}

.card-name {
  font-family: var(--font-tarot);
  font-size: 18px;
  letter-spacing: 0.1em;
  color: var(--brand-purple);
}

.card-number {
  font-family: var(--font-tarot);
  font-size: 14px;
  color: var(--text-tertiary);
}
```

### 6.4 免费解读结果页

```html
<section class="reading-result">
  <div class="result-card">
    <div class="result-header">
      <span class="result-badge">✨ Today's Love Insight</span>
      <span class="result-date">July 3, 2026</span>
    </div>

    <div class="result-card-display">
      <!-- 塔罗牌展示 -->
      <div class="mini-tarot">
        <div class="tarot-mini">
          <img src="the-lovers.png" alt="The Lovers" />
          <span class="tarot-mini-name">The Lovers</span>
        </div>
      </div>
    </div>

    <div class="result-interpretation">
      <p class="result-text">
        A meaningful connection is forming in your love life right now. Trust your
        intuition when it comes to matters of the heart — the universe is aligning
        to bring clarity to an important relationship question.
      </p>
      <p class="result-advice">
        <strong>Today's advice:</strong> Be open and honest in your conversations.
        Vulnerability isn't weakness — it's the bridge to deeper intimacy.
      </p>
    </div>

    <!-- 免费层结尾的付费提升 -->
    <div class="upsell-card">
      <div class="upsell-glow"></div>
      <h3>Want to see the full picture?</h3>
      <p>Unlock a 7-card love spread with detailed AI interpretation covering
        Past, Present, Future, Your Strengths, Their Strengths, Challenges, and Outcome.</p>
      <button class="btn-primary">
        🔓 Unlock Full Reading — $4.99
      </button>
      <p class="upsell-alt">
        or <a href="#">subscribe monthly for $9.99</a>
      </p>
    </div>

    <!-- 分享按钮 -->
    <div class="share-actions">
      <button class="btn-share">
        <span>📤</span> Share to Instagram
      </button>
      <button class="btn-share">
        <span>📋</span> Copy Link
      </button>
    </div>
  </div>
</section>
```

```css
.reading-result {
  padding: var(--space-6);
  max-width: 520px;
  margin: 0 auto;
}

.result-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: var(--shadow-lg);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.result-badge {
  padding: 6px 14px;
  background: var(--gradient-soft);
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 500;
  color: var(--brand-purple);
}

.result-date {
  font-size: 13px;
  color: var(--text-tertiary);
}

.result-card-display {
  text-align: center;
  margin-bottom: 24px;
}

.mini-tarot {
  display: flex;
  justify-content: center;
}

.tarot-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.tarot-mini img {
  width: 120px;
  height: 200px;
  border-radius: 12px;
  border: 2px solid var(--border-medium);
  box-shadow: var(--shadow-md);
}

.tarot-mini-name {
  font-family: var(--font-tarot);
  font-size: 14px;
  letter-spacing: 0.08em;
  color: var(--brand-purple);
}

.result-interpretation {
  margin-bottom: 28px;
}

.result-text {
  font-family: var(--font-display);
  font-size: 18px;
  line-height: 1.7;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.result-advice {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--brand-purple);
}

/* 付费提升卡片 */
.upsell-card {
  position: relative;
  text-align: center;
  padding: 28px 24px;
  background: var(--gradient-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  margin-bottom: 24px;
  overflow: hidden;
}

.upsell-card h3 {
  font-family: var(--font-display);
  font-size: 22px;
  margin-bottom: 12px;
}

.upsell-card p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  line-height: 1.5;
}

.upsell-alt {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 12px;
}

.upsell-alt a {
  color: var(--brand-purple);
  text-decoration: underline;
}

/* 分享按钮 */
.share-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-share {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-pill);
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-share:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-medium);
}
```

---

## 七、页面三：付费升级页（Premium / Upgrade Page）

### 7.1 页面结构

```
╔══════════════════════════════════════════╗
║  Premium Upgrade Page                    ║
║                                           ║
║  "Go Beyond the Daily"                   ║
║  Unlock deeper relationship insights     ║
║                                           ║
║  ╔════════════════════════════════════╗  ║
║  ║  选项A: 单次深度解读 $4.99          ║  ║
║  ║  ┌──────────────────────────────┐  ║  ║
║  ║  │  7-Card Love Spread           │  ║  ║
║  ║  │  [Past] [Present] [Future]    │  ║  ║
║  ║  │  [Your Strength] [Their Str.]  │  ║  ║
║  ║  │  [Challenge] [Outcome]        │  ║  ║
║  ║  │                               │  ║  ║
║  ║  │  ✓ AI deep interpretation     │  ║  ║
║  ║  │  ✓ Personalized to your Q     │  ║  ║
║  ║  │  ✓ Shareable detailed card     │  ║  ║
║  ║  │  ✓ Save to journal             │  ║  ║
║  ║  │                               │  ║  ║
║  ║  │  [Get This Reading — $4.99]   │  ║  ║
║  ║  └──────────────────────────────┘  ║  ║
║  ╚════════════════════════════════════╝  ║
║                                           ║
║  ╔════════════════════════════════════╗  ║
║  ║  选项B: 月度订阅 $9.99/月          ║  ║
║  ║  ✓ Everything in Single Reading    ║  ║
║  ║  ✓ Unlimited deep readings          ║  ║
║  ║  ✓ Couple synastry chart            ║  ║
║  ║  ✓ AI chat follow-up questions      ║  ║
║  ║  ✓ Weekly love forecast             ║  ║
║  ║  ✓ 7-day free trial                 ║  ║
║  ║  [Start Free Trial →]              ║  ║
║  ╚════════════════════════════════════╝  ║
║                                           ║
║  FAQ: "Will they know?" → No, 100%...  ║
║  FAQ: "Can I cancel?" → Anytime...      ║
║                                           ║
║  💳 Secure checkout via Stripe           ║
║  🔒 256-bit SSL encryption              ║
╚══════════════════════════════════════════╝
```

### 7.2 7牌爱情牌阵展示

```html
<section class="spread-preview">
  <h3>Your 7-Card Love Spread</h3>
  <div class="spread-cards">
    <div class="spread-position">
      <span class="position-label">Past</span>
      <div class="spread-card-slot">
        <div class="slot-placeholder">?</div>
      </div>
    </div>
    <div class="spread-position">
      <span class="position-label">Present</span>
      <div class="spread-card-slot">
        <div class="slot-placeholder">?</div>
      </div>
    </div>
    <div class="spread-position">
      <span class="position-label">Future</span>
      <div class="spread-card-slot">
        <div class="slot-placeholder">?</div>
      </div>
    </div>
  </div>
  <div class="spread-cards spread-cards-row2">
    <div class="spread-position">
      <span class="position-label">Your Strength</span>
      <div class="spread-card-slot"><div class="slot-placeholder">?</div></div>
    </div>
    <div class="spread-position">
      <span class="position-label">Their Strength</span>
      <div class="spread-card-slot"><div class="slot-placeholder">?</div></div>
    </div>
    <div class="spread-position">
      <span class="position-label">Challenge</span>
      <div class="spread-card-slot"><div class="slot-placeholder">?</div></div>
    </div>
    <div class="spread-position">
      <span class="position-label">Outcome</span>
      <div class="spread-card-slot"><div class="slot-placeholder">?</div></div>
    </div>
  </div>
  <p class="spread-note">Cards will be drawn and interpreted by AI based on your question</p>
</section>
```

```css
.spread-preview {
  padding: 32px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: 28px;
}

.spread-cards {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.spread-position {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.position-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--brand-purple);
  font-weight: 500;
}

.spread-card-slot {
  width: 72px;
  height: 120px;
  border: 2px dashed var(--border-medium);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slot-placeholder {
  font-family: var(--font-tarot);
  font-size: 24px;
  color: var(--brand-purple-light);
  opacity: 0.5;
}

.spread-note {
  text-align: center;
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 16px;
}

@media (max-width: 480px) {
  .spread-cards { gap: 8px; }
  .spread-card-slot { width: 60px; height: 100px; }
}
```

### 7.3 信任与安全元素

```html
<section class="trust-footer">
  <div class="trust-items">
    <div class="trust-item">
      <span class="trust-icon">🔒</span>
      <div>
        <strong>100% Private</strong>
        <p>Readings are never shared. Your secrets stay yours.</p>
      </div>
    </div>
    <div class="trust-item">
      <span class="trust-icon">💳</span>
      <div>
        <strong>Secure Checkout</strong>
        <p>256-bit SSL encryption. Cancel anytime.</p>
      </div>
    </div>
    <div class="trust-item">
      <span class="trust-icon">🔄</span>
      <div>
        <strong>7-Day Free Trial</strong>
        <p>Try Premium free. No charge until 7 days.</p>
      </div>
    </div>
  </div>
</section>
```

---

## 八、用户流程图（User Flow）

### 8.1 完整用户旅程

```
                    ┌─────────────┐
                    │  外部流量入口 │
                    │  TikTok/IG/  │
                    │  SEO/朋友推荐│
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   首页 Hero  │
                    │ "Get Free   │
                    │  Reading"   │
                    └──────┬──────┘
                           ↓
              ┌────────────┴────────────┐
              │    无需注册 / 可选注册   │
              │  "No sign-up required"  │
              └────────────┬────────────┘
                           ↓
                 ┌─────────────────┐
                 │  选择问题类别    │
                 │  💕 Love        │
                 │  🗣️ Comm       │
                 │  💫 Future      │
                 │  🔗 Compat     │
                 │  ❓ Custom      │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │  （可选）输入    │
                 │  伴侣信息/出生日 │
                 │  → 用于合盘分析  │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │  抽牌动画       │
                 │  牌背面 → 翻转   │
                 └────────┬────────┘
                          ↓
              ┌───────────┴───────────┐
              │   免费层结果展示        │
              │   · 今日爱情运势        │
              │   · 一张牌解读          │
              │   · 每日建议            │
              │   · 分享按钮            │
              │                        │
              │   🔓 Upsell:           │
              │   "See the full        │
              │    picture?"           │
              └─────┬───────┬─────────┘
                    │       │
            [免费分享]  [点击 Upsell]
                    │       │
                    ↓       ↓
              ┌──────────┐  ┌───────────────┐
              │ 社交传播 │  │  付费升级页    │
              │ → 新用户 │  │               │
              └──────────┘  │ A: $4.99 单次  │
                           │   7-Card Spread│
                           │               │
                           │ B: $9.99/月    │
                           │   全功能无限   │
                           └───────┬───────┘
                                   ↓
                           ┌───────────────┐
                           │  付款 (Stripe) │
                           └───────┬───────┘
                                   ↓
              ┌────────────┬────────────┐
              ↓            ↓            ↓
     ┌────────────┐ ┌──────────┐ ┌──────────┐
     │  7牌阵解读  │ │ 合盘分析  │ │ AI 对话  │
     │  逐张翻开   │ │ 星盘对比  │ │ 追问细节  │
     │  AI深度解读 │ │ 关系洞察  │ │ 情感导航  │
     └─────┬──────┘ └─────┬────┘ └────┬─────┘
           │              │          │
           └──────┬───────┴──────────┘
                  ↓
          ┌──────────────┐
          │  完整结果页   │
          │  · 详细解读   │
          │  · 可下载报告 │
          │  · 社交分享卡 │
          │  · 保存到日记 │
          └──────┬───────┘
                 ↓
          ┌──────────────┐
          │  回访触发     │
          │  · 每日推送    │
          │  · 邮件周报    │
          │  · 关系变化提醒│
          └──────────────┘
```

### 8.2 关键转化节点

| 节点 | 位置 | 目标 | 预期转化率 |
|------|------|------|-----------|
| **T1** | Hero CTA → 进入体验 | 获客 | 30-50% |
| **T2** | 问题选择 → 抽牌 | 沉浸 | 80-90% |
| **T3** | 免费结果 → 点击Upsell | 付费意愿 | 15-25% |
| **T4** | 付费页 → 完成支付 | 变现 | 5-15% |
| **T5** | 单次用户 → 月度订阅 | LTV提升 | 20-30% |

---

## 九、塔罗牌阵选择逻辑

### 9.1 牌阵体系

DateFate 聚焦爱情关系，设计3种牌阵层级：

| 牌阵 | 层级 | 牌数 | 位置含义 | 价格 |
|------|------|------|---------|------|
| **Single Card** | 免费 | 1 | 今日爱情指引 / 直觉信号 | $0 |
| **Three Card** | 付费 | 3 | 过去·现在·未来 / 你·TA·关系 / 身·心·灵 | $4.99 |
| **Seven Card Love** | 付费 | 7 | Past·Present·Future·Your Strength·Their Strength·Challenge·Outcome | $4.99 |
| **Synastry Spread** | Premium | 10+ | 双人星盘合盘+牌阵综合分析 | $9.99 |

### 9.2 选择逻辑（用户驱动 + AI 推荐）

```
用户进入 → 选择问题类型
              │
              ├── 💕 "How's my love life?"
              │     → AI推荐: Single Card (free) → 升级到 Three Card
              │
              ├── 🗣️ "Should I talk to them?"
              │     → AI推荐: Three Card (You·Them·Outcome)
              │
              ├── 💫 "Where is this going?"
              │     → AI推荐: Seven Card Love Spread
              │
              ├── 🔗 "Are we compatible?"
              │     → 需要伴侣出生信息 → Synastry Spread
              │
              └── ❓ 自定义问题
                    → AI分析问题关键词 → 推荐最匹配的牌阵
```

### 9.3 AI 牌阵推荐逻辑

```javascript
function recommendSpread(question, context) {
  const keywords = {
    compatibility: ['compatible', 'match', 'soulmate', 'right for me', 'together'],
    future: ['future', 'where', 'heading', 'long-term', 'marriage', 'commit'],
    communication: ['talk', 'say', 'tell', 'text', 'message', 'honest', 'communication'],
    general_love: ['love', 'crush', 'dating', 'relationship', 'feeling', 'heart'],
  };

  // 检测问题关键词
  const detected = detectKeywords(question, keywords);

  // 根据检测推荐
  if (detected.includes('compatibility') && context.partnerBirthdate) {
    return 'synastry'; // 10+牌合盘
  } else if (detected.includes('future') || detected.includes('communication')) {
    return 'three_card'; // 3牌
  } else if (detected.length >= 2) {
    return 'seven_card'; // 7牌爱情阵
  } else {
    return 'single'; // 免费1牌
  }
}
```

### 9.4 塔罗牌视觉设计规范

所有78张塔罗牌需统一设计风格，保持粉紫温柔美学：

| 元素 | 设计要求 |
|------|---------|
| **线稿风格** | 细线条插画（1-2px stroke），类似 Golden Thread Tarot 的极简风 |
| **色调** | 主色 = 品牌紫粉渐变点缀，背景 = 浅紫白或纯白 |
| **元素** | 每张牌的象征符号用品牌紫色填充，其余保持线稿 |
| **背面设计** | 紫粉渐变 + 星座符号图案 + 中央品牌logo |
| **圆角** | 卡片四角圆角 10px |
| **尺寸** | Web展示 120×200px，分享卡片 200×340px |

---

## 十、文案风格指南（English Copywriting Guide）

### 10.1 品牌声音（Brand Voice）

| 维度 | 定义 |
|------|------|
| **语气** | 温暖、直觉、赋权（Warm, Intuitive, Empowering） |
| **人称** | 直接称呼 "you"，不说教 |
| **术语** | 零占星术语（"不用解释什么是逆行"） |
| **情感基调** | 积极、建设性，不做恐惧营销 |
| **类比风格** | 用日常比喻替代神秘术语 |

### 10.2 文案层级规范

| 位置 | 风格 | 字数 | 示例 |
|------|------|------|------|
| **Hero 标题** | 诗意但清晰 | 6-12词 | "See Your Love Story Written in the Stars" |
| **Hero 副标题** | 功能+利益 | 15-25词 | "AI tarot & astrology insights for your relationship journey" |
| **CTA 按钮** | 行动+利益 | 3-6词 | "Get Your Free Reading" |
| **区块标题** | 好奇心驱动 | 4-8词 | "Three Steps to Clarity" |
| **卡片文案** | 共情+实用 | 20-40词 | "Draw one card for a quick love insight. Updated daily." |
| **塔罗解读** | 个性化、温和、有建设性 | 80-150词 | "A meaningful connection..." |
| **Upsell 文案** | 好奇心+紧迫感（非胁迫） | 30-50词 | "Want to see the full picture?" |
| **Social Proof** | 真实感+情感共鸣 | 30-60词 | "DateFate helped me understand..." |
| **FAQ 回答** | 直接、透明 | 20-40词 | "No, your readings are completely private." |

### 10.3 禁用文案 vs 推荐文案

| ❌ 禁用 | ✅ 推荐 | 原因 |
|---------|---------|------|
| "Predict your future" | "See what's ahead" | 避免宿命论暗示 |
| "Accurate predictions" | "Personalized insights" | 合规+诚信 |
| "Unlock the secrets" | "Discover deeper clarity" | 减少焦虑感 |
| "Buy now" | "Go deeper" | 好奇心驱动而非销售驱动 |
| "Mercury retrograde" | "Communication may feel tricky" | 去占星术语 |
| "You will meet someone" | "The energy is open for new connections" | 避免伪精确 |
| "Money-back guarantee" | "7-day free trial, cancel anytime" | 更具体的承诺 |
| "Sign up now" | "Start your free reading" | 降低心理门槛 |

### 10.4 关键页面文案模板

**Hero Section:**
```
Headline: "See Your Love Story Written in the Stars"
Subtitle: "AI-powered tarot & astrology insights for your relationship journey. Get a free love reading in 10 seconds — no sign-up required."
CTA: "✨ Get Your Free Reading"
Proof: "★★★★★ Loved by 50,000+ readers"
```

**Question Picker:**
```
Section Title: "What's on your heart today?"
Subtitle: "Pick a topic for your free love reading"
Cards:
  Love & Romance: "How's your love life looking right now?"
  Communication: "Should you say what's on your mind?"
  Future Potential: "Where is this relationship heading?"
  Compatibility: "Are you two written in the stars?"
Custom: "Or ask anything about your relationship..."
```

**Upsell (after free reading):**
```
Headline: "Want to see the full picture?"
Body: "Your one-card glimpse is just the beginning. Unlock a 7-card love spread with detailed AI interpretation — covering your past, present, future, and the energies shaping your connection."
CTA: "🔓 Unlock Full Reading — $4.99"
Alt: "or subscribe for unlimited insights at $9.99/month"
```

**Pricing Page:**
```
Headline: "Choose Your Depth"
Free: "Start Free — Daily love horoscope + one card draw"
Deep: "Deep Reading — $4.99 per reading — Full spread + AI interpretation"
Premium: "DateFate Premium — $9.99/month — Everything unlimited + couple synastry"
```

---

## 十一、动效规范（Animation Guidelines）

### 11.1 动效清单

| 动效 | 触发 | 时长 | 缓动函数 | 实现方案 |
|------|------|------|---------|---------|
| **页面滚动渐入** | 进入视口 | 0.6s | ease-out | IntersectionObserver + CSS transform |
| **塔罗牌翻转** | 用户点击/触摸 | 0.8s | cubic-bezier(0.4,0,0.2,1) | CSS 3D transform: rotateY(180deg) |
| **CTA按钮光晕** | hover | 0.3s | ease-in-out | box-shadow + background transition |
| **卡片浮起** | hover | 0.3s | ease-out | translateY(-4px) + box-shadow |
| **抽牌晃动** | 等待点击 | 2s loop | ease-in-out | CSS animation: wiggle |
| **粒子星空** | 页面加载 | 持续 | — | tsparticles.js（轻量） |
| **渐变文字闪烁** | hover | 0.3s | — | background-position shift |
| **解读文字逐行出现** | 结果展示 | 1.2s | ease-out | 逐段落 fadeIn + translateY |
| **分享卡片生成** | 点击分享 | 0.5s | — | canvas → image download |

### 11.2 性能约束

- 首屏加载 < 2s（LCP）
- 交互延迟 < 100ms（FID）
- 累计布局偏移 < 0.1（CLS）
- 粒子效果仅在首屏，滚动后自动销毁释放内存
- 所有动画支持 `prefers-reduced-motion: reduce` 降级

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 十二、响应式断点

| 断点 | 宽度 | 布局变化 |
|------|------|---------|
| **Mobile S** | 320-374px | 单列全宽，卡片内边距 16px |
| **Mobile** | 375-480px | 单列全宽，卡片内边距 20px |
| **Tablet** | 481-768px | 双列Features，单列Pricing |
| **Laptop** | 769-1024px | 双列Features，三列Pricing |
| **Desktop** | 1025-1440px | 三列全布局，最大宽度 1200px |
| **Wide** | 1441px+ | 最大宽度 1200px 居中 |

---

## 十三、技术栈推荐

| 层次 | 推荐方案 | 理由 |
|------|---------|------|
| **框架** | Next.js 14+ | SSR/SSG + 快速加载 + SEO友好 |
| **样式** | Tailwind CSS v4 + 上述CSS变量 | 快速迭代 + 设计系统一致 |
| **组件库** | shadcn/ui | 极致可定制，暗色模式原生 |
| **动画** | Framer Motion | React生态最佳 |
| **粒子** | tsparticles.js | 轻量星空效果 |
| **支付** | Stripe Checkout | 最成熟的全球支付 |
| **字体** | Google Fonts（免费） | Cormorant Garamond + DM Sans + Cinzel |
| **部署** | Vercel | Next.js最佳 |
| **分析** | Plausible/Umami | 隐私友好 |

---

## 十四、知识缺口与后续迭代

| 缺口 | 说明 | 优先级 |
|------|------|--------|
| 具体竞品UI截图分析 | 未直接抓取Co-Star/Sanctuary最新UI，依赖二手报告 | 中 |
| 分享卡片模板设计 | 需要具体的Instagram Story/TikTok分享卡片尺寸和排版 | 高 |
| 微交互动效原型 | 需要Figma/ProtoPie动效原型验证体验 | 中 |
| A/B测试变量设计 | 需要定义Hero文案、CTA颜色、定价展示等A/B测试组 | 中 |
| 付费墙时机 | 单次解读后立即 vs 累计3次后弹出，需数据验证 | 高 |

---

## 十五、方法论说明

本文档基于以下信息源综合撰写：
1. **任务需求**：详细的DateFate产品设计需求（粉紫温柔风、MysticMirror配色体系、目标用户、免费/付费层级）
2. **R-122**：高转化占卜玄学独立站设计风格研究（配色方案、字体推荐、转化漏斗、组件库评估）
3. **R-123**：MysticMirror竞品差异化分析（市场数据、用户画像、商业模式）
4. **R-110**：美国AI塔罗牌产品深度调研（竞品对比、用户痛点、定价分析）
5. **R-112**：MysticMirror PRD（产品定位、用户痛点、需求层次）
6. **行业最佳实践**：The Pattern的去术语化、Sanctuary的首单特价、Co-Star的推送文化

> **注意**：本文档中的CSS/HTML代码为指导性实现参考，开发时应根据实际框架（Next.js/Tailwind）做组件化拆分。配色值和字体选择已给出精确规范，可直接用于 Design Token 配置。
