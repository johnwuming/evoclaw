# R-183 研究笔记

## 调研对象

### 开源支付系统（支付宝+微信支付）
1. **DaxPay** (dromara/dax-pay) - Apache License 2.0 → 后改 LGPL v3.0, Spring Boot 3.5.x + Vue3, JDK 21+, PostgreSQL, GitHub Stars ~3000+
2. **Jeepay** (jeequan/jeepay) - LGPL-3.0, Spring Boot 3.3.7 + JDK 17 + Ant Design Vue, MySQL, GitHub Stars ~4.5k+
3. **独角数卡 Dujiaoka** (assimon/dujiaoka) - Laravel (PHP), 已归档(2026.03), GitHub Stars ~11k+, 继任者 Dujiao-Next (Go)
4. **彩虹易支付 EPay** (lopinx/epay) - PHP, 商业源码非真正开源
5. **YunGouOS** - 开源SDK (微信/支付宝官方服务商模式), 支持个人接入
6. **XxPay** - Java聚合支付, Jeepay前身
7. **Ping++** - 商业聚合支付SDK, 非开源

### SaaS API门控/付费解锁方案
- Stripe (国际) - API key + 订阅 + Entitlements
- Paddle (国际, Merchant of Record) - 5% + $0.50/笔
- Lemon Squeezy (国际, MoR) - 5% + $0.50/笔
- 国内: SaaS paywall 模式（功能分级 + API调用次数限制）

### 开发成本参考
- IT外包人天单价: 800-1500元/人天（中级），1500-2500元/人天（高级）
- 支付系统定制开发: 简单聚合支付接入 3-8万，中型支付中台 10-30万，企业级 30-100万+
- Jeepay Plus 商业版: 需联系销售（约2-5万/年授权费）
- DaxPay 商业版: 三档（开源版/商业版/SaaS版）

## 支付渠道费率
- 微信支付官方费率: 0.6%-1%
- 支付宝官方费率: 0.6%
- 聚合支付服务商费率: 0.38%-0.6%
- PAYJS: 开通费300元 + 0.6%官方费率 + 1.78%服务费
- 七相PAY: 开通费148元 + 1.2%平台费 + 0.6%官方费率
