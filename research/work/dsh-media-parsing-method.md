# DSH 小红书 / B站 链接解析方法论（task-0418）

> 结论先行：DSH 解析小红书/B站链接靠的不是专用工具，而是 **curl 直连 + 页面内嵌 JSON（__INITIAL_STATE__）+ 官方 web API + （B站无字幕时）下载音频流跑 faster-whisper 本地 ASR** 的组合拳。全程无需登录账号（截至 2026-08-17 实测），核心是把「分享短链 → 最终 URL → 结构化数据」的每一跳用对的 UA / Referer / cookie jar 走通。本文给出可直接照做的命令级步骤，全部步骤均有会话文件行号可溯源。

---

## 1. 方法与数据来源

- 来源会话：`/root/.dsh/sessions/--root-dsh-workspace--/session-791350d1-02c6-4949-b7ad-f75d64d4faf7/session.jsonl.zstd`（1.26MB 压缩，解压 2.6MB / 4985 行）
- 读取方式：`zstd -d session.jsonl.zstd -o /tmp/s.jsonl`，之后按行号用 python json.loads 抽取 `user/message`、`tool/call`（data.arguments）、`tool/result`（data.message.content[].content[].text）三类事件。
- 两个解析回合：
  - 小红书：用户消息 L2565「…https://xhslink.cn/o/AbuLbFw22PJ 跳转【小红书】看看笔记详情~把这个帖子内容给我扒下来」→ turn 2，工具链 L2595–L3126，最终交付 L3311。
  - B站：用户消息 L3318「【5 年 15 倍的小市值量化策略…-哔哩哔哩】 https://b23.tv/cAgbtEB获取这视频的台词」→ turn 3，工具链 L3341–L4755。
- 注：任务书原给的 03260074 / 8fc31ca9 两个会话为误报（grep 压缩流所致）；真正回合只在 791350d1。

通用 UA（下文简称 `$IPHONE_UA` / `$CHROME_UA`）：

```
IPHONE_UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CHROME_UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
```

---

## 2. 小红书解析路径（实测走通，无需登录）

### 2.1 短链展开 + 拿 SSR 页面

```bash
curl -sS -L --max-time 30 \
  -A "$IPHONE_UA" \
  -D /tmp/xhs_headers.txt \
  'https://xhslink.cn/o/<code>' \
  -o /tmp/xhs_body.html
```

- 证据 L2596：302 → `https://www.xiaohongshu.com/discovery/item/<noteId>?...&xsec_token=<token>&xhsshare=CopyLink...`，再 200 返回 HTML。
- **关键点**：App 分享短链自带 `xsec_token`，`curl -L` 跟随后服务端直接渲染 `__INITIAL_STATE__`，并自动下发 `acw_tc` cookie（同一 curl 会话内自动携带）。不需要手动准备 cookie。
- 局限：`xsec_token` 与短链绑定且会过期；直接拼 `xiaohongshu.com/explore/<noteId>`（无 token）大概率被风控。**必须从分享短链进入**。

### 2.2 抠出 __INITIAL_STATE__ JSON

```python
import json, re
s = open('/tmp/xhs_body.html', encoding='utf-8', errors='replace').read()
i = s.find('__INITIAL_STATE__=')
j = s.find('</script>', i)
raw = s[i+len('__INITIAL_STATE__='):j].strip()
raw = re.sub(r'\bundefined\b', 'null', raw)      # 页面 JS 字面量含 undefined
data = json.loads(raw)
```

- 证据：L2640/L2676/L2701（首次 parse 失败 → 定位 undefined）→ L2771（替换后成功）。直接 `json.loads` 会报错，**必须先做 undefined→null 替换**。

### 2.3 字段提取（证据 L2810/L2811）

| 内容 | JSON 路径（`d = __INITIAL_STATE__`） |
|---|---|
| 笔记主体 | `d['noteData']['data']['noteData']` |
| 标题 / 正文 | `.title` / `.desc` |
| 作者 | `.user.nickName` |
| 互动数据 | `.interactInfo`（likedCount/commentCount/shareCount/collectedCount） |
| 类型/时长 | `.type`（"video" 或 "normal"）、`.video.media.video.duration` |
| 发布时间 | `.lastUpdateTime`（毫秒时间戳，+8h 转北京时间，证据 L3126） |
| 评论 | `d['noteData']['data']['commentData']['comments'][]`（user.nickname / content / likeCount / subComments），证据 L2907 |

### 2.4 视频笔记：字幕与视频流（signed CDN URL，免 cookie）

- 字幕在 `noteData` 内 `…subtitles` 块（证据 L2811 原文）：
  - 原文转写：`subtitles.source[0].url`（zh-CN，sns-subtitle-s1.xhscdn.com/…srt?sign=…&t=…）
  - ASR 版：`subtitles['zh-CN'][0].url`；英文：`subtitles['en-US'][0].url`
- 视频流：`…stream.h264[].masterUrl`（sns-video-qc.xhscdn.com…mp4?sign=…&t=…）+ `backupUrls`；封面图在 `sns-webpic-qc.xhscdn.com`。
- 下载 + 转纯文本：

```bash
curl -sS -L --max-time 60 '<srt_url>' -o /tmp/xhs_subtitle.srt
python3 - <<'PY'
import re
lines = open('/tmp/xhs_subtitle.srt', encoding='utf-8').read().splitlines()
text = ''.join(l.strip() for l in lines
               if l.strip() and not re.fullmatch(r'\d+', l.strip()) and '-->' not in l)
open('/tmp/xhs_transcript.txt','w').write(text)
PY
```

- 证据 L2842/2843（srt 下载成功且即中文原文，240 行）、L2879/2880（→1339 字纯文本）。
- **注意**：srt/mp4 URL 的 `sign`/`t` 参数有时效，拿到后应立即下载，不要落盘 URL 隔天再用。

### 2.5 降级路径（视频无 subtitles 时）

下载 masterUrl 的 mp4 → `ffmpeg -i x.mp4 -vf 'fps=1/10,scale=540:-1' frames/f_%02d.jpg` → `tesseract f.jpg stdout -l chi_sim+eng --psm 6`（证据 L2995–L3047；本例有字幕未走此路，但管线在同一会话内对 B站视频实际跑通，见 §3.5）。

### 2.6 图文笔记

同一 `__INITIAL_STATE__` 入口，图片 URL 在笔记数据的图片列表（本会话未演示，属推断；视频笔记字段已全部实测）。

---

## 3. B站解析路径（实测走通，台词靠本地 ASR）

### 3.1 短链展开（会触发风控，属预期）

```bash
curl -sS -L --max-time 30 -A "$CHROME_UA" -D /tmp/b23_headers.txt \
  'https://b23.tv/<code>' -o /tmp/bili_page.html
```

- 证据 L3342：302 → `www.bilibili.com/video/BV1NvPmzzE75?...`，随后视频页返回 **HTTP 412**（风控页）。**数据中心 IP 直抓 www 视频页不可靠，必须走 API 路线**。412 响应头里会 `set-cookie: X-BILI-SEC-TOKEN=…`，留着有用（见 3.3）。

### 3.2 元数据 API（免登录，稳定）

```bash
curl -sS --max-time 20 -A "$IPHONE_UA" \
  -H 'Referer: https://www.bilibili.com/video/BV1NvPmzzE75' \
  'https://api.bilibili.com/x/web-interface/view?bvid=BV1NvPmzzE75'
```

- 证据 L3376/3377：`code:0`，一次拿全 title / desc / owner(name,mid) / stat(view/danmaku/reply/like…) / `pages[].cid`（本例 cid=36566338129）/ duration=954s / aid。

### 3.3 字幕判定（多数情况拿不到 → 直接规划 ASR）

- `x/player/v2?bvid=&cid=`：`subtitle.subtitles=[]`（证据 L3419）
- `x/player/wbi/v2?bvid=&cid=`：同空，且 `need_login_subtitle: true`（证据 L3438）
- 结论：**无登录 cookie 时 CC/AI 字幕接口必空**（yt-dlp --list-subs 同样为空，L3529）。除非用户提供登录 cookie（SESSDATA），否则跳过字幕、走 3.4 起的音频 ASR。

### 3.4 取音频流（cookie jar 是关键）

```bash
# 先用 cookie jar 过一遍 m 站页面（复用 3.1 拿到的 X-BILI-SEC-TOKEN，或让 412 重新下发）
curl -sS -L --max-time 20 -A "$IPHONE_UA" \
  -H 'Referer: https://www.bilibili.com/' \
  -c /tmp/bili_ck.txt -b /tmp/bili_ck.txt \
  'https://m.bilibili.com/video/BV1NvPmzzE75' -o /tmp/bili_mobile.html   # 200，105KB

# 再取 DASH 流清单
curl -sS --max-time 20 -A "$IPHONE_UA" \
  -H 'Referer: https://m.bilibili.com/video/BV1NvPmzzE75' \
  -c /tmp/bili_ck.txt -b /tmp/bili_ck.txt \
  'https://api.bilibili.com/x/player/playurl?bvid=BV1NvPmzzE75&cid=36566338129&fnval=16&fnver=0&fourk=1' \
  -o /tmp/bili_playurl.json
```

- 证据 L3587/3588（m 站 200 含 `__INITIAL_STATE__`）、L3640/3641（playurl `code:0`，`dash.audio[]` 含 signed `upos-sz-*.bilivideo.com/…m4s` URL）。
- **注意**：`-c/-b` 同一个 jar 贯穿使用；playurl 的 URL 是按「当前 IP + UA + cookie」签发的，换机器不能复用。

### 3.5 下载音频并转写（台词的实际来源）

```bash
# 选最低码率音频（省流量，ASR 不需要高音质）
python3 - <<'PY'
import json
d = json.load(open('/tmp/bili_playurl.json'))['data']
a = min(d['dash']['audio'], key=lambda x: x.get('bandwidth') or 999999)
open('/tmp/bili_audio_url.txt','w').write(a['baseUrl'])
PY
curl -sS -L --max-time 120 -A 'Mozilla/5.0' \
  -H 'Referer: https://www.bilibili.com/video/BV1NvPmzzE75/' \
  "$(cat /tmp/bili_audio_url.txt)" -o /tmp/bili_audio.m4s

ffmpeg -loglevel error -y -i /tmp/bili_audio.m4s -ar 16000 -ac 1 /tmp/bili_audio.wav
```

- 证据 L3665/3666（m4s 下载成功，ffprobe 可读时长）。

ASR（分段、断点续跑、HF 镜像，证据 L4160；产出证据 L4736）：

```bash
# 120s 分段（长视频防单次运行被杀，可断点续跑）
ffmpeg -loglevel error -i /tmp/bili_audio.wav -f segment -segment_time 120 -c copy /tmp/bili_chunks/chunk_%03d.wav

cat > /tmp/run_whisper_chunks.py <<'PY'
import os, json, glob, time
from faster_whisper import WhisperModel
root='/tmp/bili_chunks'
model=WhisperModel('small', device='cpu', compute_type='int8')
for i, path in enumerate(sorted(glob.glob(root+'/chunk_*.wav'))):
    base=os.path.splitext(os.path.basename(path))[0]
    if os.path.exists(f'{root}/{base}.done'): continue
    segs,_=model.transcribe(path, language='zh', vad_filter=True, beam_size=1,
                            best_of=1, condition_on_previous_text=False,
                            initial_prompt='<视频主题领域词，如：量化策略 回测 调仓 涨停>')
    out=[{'start':round(i*120+s.start,1),'end':round(i*120+s.end,1),'text':s.text.strip()} for s in segs]
    json.dump(out, open(f'{root}/{base}.json','w'), ensure_ascii=False, indent=2)
    open(f'{root}/{base}.done','w').write('ok')
PY
HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 \
  setsid -f python3 /tmp/run_whisper_chunks.py > /tmp/bili_whisper.log 2>&1 &
```

- **HF_ENDPOINT=https://hf-mirror.com 必带**：本 VPS 直连 huggingface.co 失败（证据 L3726→L3749/L3773 由镜像解决）。
- `setsid -f` 让转写独立于会话存活（该 turn 后来被用户打断，转写仍持续产出）。
- `beam_size=1, best_of=1` 提速；`initial_prompt` 注入领域词汇显著改善专有名词。

### 3.6 可选增强：画面文字 OCR

下载最低码率 `dash.video[]`（同 3.5 头），`ffmpeg -vf 'fps=1/10,scale=720:-1'` 抽帧，`tesseract … -l chi_sim+eng --psm 6`（证据 L3958–L3996，产出 L4755）。适合 PPT 类视频补全屏幕文字。

---

## 4. 证据摘录（会话文件行号）

| 行号 | 事件 | 内容要点 |
|---|---|---|
| L2565 | user | 「https://xhslink.cn/o/AbuLbFw22PJ …把这个帖子内容给我扒下来」 |
| L2596 | tool/result | 302 → `xiaohongshu.com/discovery/item/6a7c28d1…?…xsec_token=…`；随后 200 |
| L2771 | tool/call | `undefined→null` 后 json.loads 成功 |
| L2811 | tool/result | noteData 全量：title「微盘股择时…」、desc、subtitles.source[0].url(zh srt)、stream.h264[].masterUrl |
| L2843 | tool/result | srt 下载成功，中文原文字幕 |
| L2880 | tool/result | SRT→1339 字纯文本 |
| L3311 | assistant | 小红书完整交付（标题/作者/互动数据表+转写全文+评论） |
| L3318 | user | 「https://b23.tv/cAgbtEB获取这视频的台词」 |
| L3342 | tool/result | 302→BV1NvPmzzE75，视频页 412 |
| L3377 | tool/result | view API code:0，title/stat/pages[].cid=36566338129 |
| L3438 | tool/result | wbi player：`need_login_subtitle: true`，subtitles 空 |
| L3588 | tool/result | m 站页面 200（cookie jar 生效） |
| L3641 | tool/result | playurl code:0，dash.audio[] signed URL |
| L3666 | tool/result | 最低码率音频 m4s 下载成功 |
| L4736 | tool/result | whisper 分段转写实际产出（含时间轴文本） |
| L4755 | tool/result | 视频帧 OCR 实际产出（屏幕文字） |

（文件：`session-791350d1…/session.jsonl`，行号=解压后 jsonl 行号；`tool/call` 在行号或行号+1，`tool/result` 在行号+1。）

## 5. 局限与适用条件

1. **小红书**：必须从 App 分享短链进入（xsec_token）；token 与 CDN URL 的 sign 参数均有时效；高频请求会触发风控（本机腾讯云 VPS IP 单次正常）。图文笔记字段路径未实测（推断同入口）。
2. **B站**：www 页面直抓遇 412 属常态，走 API 即可；**字幕（CC/AI）无登录 cookie 基本拿不到**，台词的可靠来源是「playurl 取音频 + 本地 whisper」；playurl URL 绑定出口 IP，不可跨机复用。
3. **ASR 成本**：small/int8/cpu 约 2–4× 实时时长（15 分钟视频约 30–60 分钟），长视频务必分段+断点标记+后台运行；模型首次下载需 hf-mirror。
4. **环境依赖**：curl、ffmpeg/ffprobe、tesseract-ocr(+chi_sim)、faster-whisper、zstd。
5. **时效性**：以上接口/字段为 2026-08-17 实测；小红书 `__INITIAL_STATE__` 结构与 B站 playurl 签名策略可能随版本变化，失效时优先核对 §2.2/§3.4 两处解析点。
