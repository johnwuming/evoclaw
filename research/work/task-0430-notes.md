# task-0430 南京 9/25-10/5 自驾三方案 + 聚合页 部署笔记

## 需求口径
- 用户：南京出发，2026-09-25 出发，10-05 返程。日历上 9/25–10/5 = 11 天 10 晚（任务书写 10 天 9 晚，按真实日历跨度 11 天设计，页面如实标注）。
- 3 套差异化方案 + 聚合页部署 www.zhanqiangnan.cn/triple。

## 服务器现状（2026-08-21 探测）
- `zhanqiangnan.cn`（任务原文拼写）：**NXDOMAIN，域名不存在**。
- `zhengqiangnan.cn`（带 g）：apex 指向 58.212.197.84（非本机）；`www.zhengqiangnan.cn` → **82.156.124.186 = 本机**，nginx 已有 443 server 块（sites-enabled/www-zhengqiangnan，root 代理到 8055 任务中心面板）。
- 结论：任务里的 `zhanqiangnan.cn` 高概率是 `zhengqiangnan.cn` 的笔误。按部署预案「DNS 未解析到本机→本地可访问状态 + IP 直连」处理，同时挂到现有 zhengqiangnan 443 站点 `/triple` 路径，使 https://www.zhengqiangnan.cn/triple/ 立即可用。

## 部署方案
1. 文件落 `/var/www/triple/`（index.html + a-qinggan.html + b-huyang.html + c-chuanxi.html）
2. `/var/www/html/triple` → symlink 到 /var/www/triple（default 80 站点 root=/var/www/html，IP 直连 http://82.156.124.186/triple/ 即可访问）
3. 现有 www-zhengqiangnan 443 块新增 `location ^~ /triple`（改前 cp 备份，nginx -t 后 reload）
4. 新增 80 口 server 块 server_name zhanqiangnan.cn www.zhanqiangnan.cn → /var/www/triple（域名将来注册/解析后即生效，纯增量）

## 三方案设计（里程为高速主干经验值估算）
- A 青甘大环线（湖蓝）：车托运+落地自驾模式，环线 ~2600km，强度低，9 月底人少茶卡镜面。附硬驾全程 5300km/12天 说明。
- B 蒙西胡杨线（金橙）：南京-银川-额济纳-嘉峪关-兰州 全程硬驾 ~5050km，强度高，胡杨 10/1-10/15 正当时。
- C 川西北环线（松绿）：南京-成都-九寨-若尔盖-唐克-理县 全程硬驾 ~4440km，强度中高，彩林前哨（巅峰 10 月中下旬）。

## 验证记录（2026-08-21 19:41）
- nginx -t 通过，reload 成功；原配置备份 /root/www-zhengqiangnan.bak.20260821-194056
- HTTPS 域名路径 7 项全部 200：/triple/、/triple/index.html、a/b/c 三个方案页
- IP 直连 200：http://82.156.124.186/triple/ 及子页（经 /var/www/html/triple 符号链接走 default 80 站点）
- 内链检查：index ↔ a/b/c 五对链接全部指向存在文件，无断链
- 既有服务未受影响：https://www.zhengqiangnan.cn/ （任务中心面板）仍 200；/df0s6p 网关块未动
- 新增 80 口 server 块（zhanqiangnan.cn）为纯增量，域名 NXDOMAIN 下无实际流量

## 遗留/风险
- zhanqiangnan.cn 域名不存在；若用户确有此域名需注册并解析到 82.156.124.186，80 口 server 块已备好。
- 额济纳 10/1-3 住宿需立即预订（房价 3-5 倍仍一房难求）。
