# task-0418 过程笔记（2026-08-21）

## 定位修正（重要）
- 任务书给的会话目录 03260074 / 8fc31ca9 是误报：grep 打在 zstd 压缩流上不可靠。
- 真正含小红书/B站解析回合的会话：`/root/.dsh/sessions/--root-dsh-workspace--/session-791350d1-02c6-4949-b7ad-f75d64d4faf7/session.jsonl.zstd`
  - 解压后 2.6MB / 4985 行。L2565 = 用户发 xhslink 短链；L3318 = 用户发 b23.tv 短链要台词。
- 03260074 的命中全部来自内嵌 base64 插件源码（dsh-reports 安装任务），8fc31ca9 是量化评估会话、零命中。
- f374c2e8 仅 1 处无关命中（tool/result 里的噪声）。

## 小红书路径（turn 2）
- L2595 call / L2596 result：`curl -sS -L -A '<iPhone Safari UA>'` 跟随 xhslink.cn 302 →
  `www.xiaohongshu.com/discovery/item/<noteId>?...&xsec_token=...`，直接 200 拿到 SSR HTML（服务器自动 set-cookie acw_tc，无需手动 cookie）。
- L2640–2771：从 HTML 抠 `__INITIAL_STATE__=` 到 `</script>` 之间的 JSON，`undefined→null` 替换后 json.loads 成功。
- L2810/2811：笔记数据路径 `d['noteData']['data']['noteData']`：title/desc/user.nickName/interactInfo(赞藏评分)/type=video/lastUpdateTime。
- L2811 内证据：字幕块 `subtitles":{"en-US":[...],"source":[{zh-CN srt}],"zh-CN":[...]}`，signed URL（sns-subtitle-s1.xhscdn.com?sign=&t=）；视频流 `stream.h264[].masterUrl`（sns-video-qc.xhscdn.com signed）。
- L2842/2843：srt 直接 curl -L 下载成功（无 cookie），中文原文在 `subtitles.source[0].url`，ASR 版在 `subtitles["zh-CN"][0].url`。
- L2879/2880：SRT→纯文本（去序号/时间轴），240 行→1339 字。
- L2907：评论在 `d['noteData']['data']['commentData']['comments']`。
- L2995–3047：降级路径（若视频无字幕）：下载 mp4 → ffmpeg fps=1/10 抽帧 → tesseract chi_sim+eng OCR。本例未走此路（有字幕）。
- L3311：最终交付消息（标题/作者/数据表+转写全文）确认成功。

## B站路径（turn 3）
- L3341/3342：b23.tv 302 → `www.bilibili.com/video/BV1NvPmzzE75`，随后页面 **412 风控**（数据中心 IP 直接抓页面不可靠）。
- L3376/3377：`api.bilibili.com/x/web-interface/view?bvid=...`（iPhone UA + Referer，无 cookie）→ code 0，拿 title/desc/stat/owner/pages[].cid=36566338129。
- L3418–3467：`x/player/v2`、`x/player/wbi/v2` 字幕均为空；wbi 版显式 `need_login_subtitle: true` → CC/AI 字幕要登录。yt-dlp --list-subs 也拿不到。
- L3378/3560/3587/3588：**412 响应会 set-cookie X-BILI-SEC-TOKEN**；带 cookie jar（-c/-b）请求 `m.bilibili.com/video/<bvid>`（iPhone UA）→ 200，105KB HTML 含 `__INITIAL_STATE__`。
- L3640/3641：`api.bilibili.com/x/player/playurl?bvid&cid&fnval=16&fnver=0&fourk=1`（iPhone UA + m 站 Referer + cookie jar）→ code 0，`dash.audio[]` 带 signed upos-sz m4s URL。
- L3665/3666：取 `min(dash.audio, key=bandwidth)`，带 `-A 'Mozilla/5.0' -H 'Referer: https://www.bilibili.com/video/<bvid>/'` 下载 m4s。
- L3709–4160：ffmpeg 转 16k 单声道 wav → faster-whisper small/int8/cpu，`language='zh', vad_filter=True, beam_size=1, best_of=1, condition_on_previous_text=False, initial_prompt=<领域词>`；
  - **HF_ENDPOINT=https://hf-mirror.com**（本机 huggingface.co 直连失败，L3726 证据）；
  - 120s 分段 + .done 断点标记 + setsid -f 后台（防会话中断），offset=i*120。
- L3958/3978：可选增强：下载最低码率视频流 → ffmpeg fps=1/10 抽帧 → tesseract OCR 屏幕文字。
- L4736/4755：whisper 分段与 OCR 均实际产出（管线验证通过）；该 turn 后来被用户手动打断（L4984 turn/end reason=interrupted），但方法完整走通。

## 关键 UA/头
- xhs：`Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1`
- bili 探测：Windows Chrome UA；m 站/API/下载：iPhone UA（同上）+ 对应 Referer。

## 环境依赖
curl、zstd、python3、ffmpeg/ffprobe、tesseract-ocr + tesseract-ocr-chi-sim、faster-whisper（pip --break-system-packages）、hf-mirror 可达。

## 工具输出累计
约 60KB（受控，未超限）。
