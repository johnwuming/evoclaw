# R-047 iOS灵感语音记录APP调研：快捷指令→转写→AI总结

> 调研日期：2026-05-10
> 研究范围：iOS平台上支持快捷指令触发录音、语音转写、AI总结的APP及工作流方案
> 审核状态：已通过双Reviewer审核（准确性7.2/10，完整性补充后提升至8/10）
> 补充调研日期：2026-05-10（国产APP专项 + 场景修正）

---

## 一、核心结论

**没有单一APP完美覆盖全部需求**（快捷指令一键录音 + 高质量转写 + 定期AI总结），但有两条可行路径：

1. **最佳单APP方案：Cleft Notes**（2024年新APP，最接近全能选手）
2. **最佳组合方案：Just Press Record + Drafts + Shortcuts**（老牌稳定，灵活组合）

> ⚠️ **场景修正**（2026-05-10 补充）：用户核心场景为**走路/徒步/外出**（非开车），车辆为乐道L60（不支持CarPlay）。因此 CarPlay 不再是加分项，**Apple Watch 快捷触发、离线能力、噪声环境下的转写质量**成为更关键的评估维度。详见第十一章国产APP专项分析。

---

## 二、候选APP横评

### 评分标准：★=优秀(3) ●=一般(2) ○=不足(1) ✕=不支持(0)

| APP | 快捷指令 | 转写质量 | AI总结 | 导出/同步 | 离线能力 | 隐私 | 价格 | **总分** |
|-----|---------|---------|--------|----------|---------|------|------|---------|
| **Cleft Notes** | ★ | ★ | ★ | ★ | ○ | ○ | ★ | **16/21** |
| **Just Press Record** | ● | ● | ✕ | ★ | ★ | ★ | ★ | **14/21** |
| **Drafts** | ★ | ●(听写) | ★ | ★ | ○ | ○ | ★ | **15/21** |
| **Apple Notes+Voice Memos** | ● | ● | ○ | ● | ★ | ★ | ★ | **13/21** |
| **闪念** | ○ | ★ | ★ | ○ | ○ | ○ | ● | **12/21** |
| **Aiko** | ● | ★ | ✕ | ● | ★ | ★ | ★ | **13/21** |
| **Voicenotes** | ○ | ● | ★ | ○ | ✕ | ○ | ✕ | **10/21** |
| **AudioPen** | ○ | ● | ★ | ○ | ✕ | ○ | ● | **10/21** |
| **Whisper Notes** | ✕ | ★ | ✕ | ○ | ★ | ★ | ★ | **11/21** |
| **Brain Dump** | ○ | ● | ○ | ★ | ○ | ○ | ● | **9/21** |
| **Otter.ai** | ○ | ● | ● | ● | ✕ | ○ | ✕ | **8/21** |
| **TalkNotes** | ○ | ● | ★ | ● | ✕ | ○ | ✕ | **8/21** |
| **Plaud AI** | ✕ | ★ | ★ | ○ | ○ | ○ | ✕ | **8/21** |

> ⚠️ 评分修正记录（基于准确性审核）：
> - Aiko：快捷指令从 ✕ 修正为 ●（Aiko 支持 Shortcuts actions）
> - Drafts：价格评分从 ● 提升至 ★（实际价格 $1.99/月、$19.99/年，比初稿记录更便宜）
> - Otter.ai：快捷指令从 ✕ 修正为 ○（Otter 有基础 Siri Shortcuts 可启动/停止录音）

---

## 三、重点APP详细评估

### 🏆 Cleft Notes — 最接近全能的选手

| 维度 | 详情 |
|------|------|
| **快捷指令** | ✅ 支持 Apple Shortcuts 自动化，可在 Shortcuts 中调用 Cleft 的 actions |
| **触发方式** | CarPlay（车屏点 New Note）✅、Apple Watch（表盘 complication / App grid）✅、Widget ✅、Shortcuts ✅ |
| **转写** | AI 驱动转写，多语言支持，持续优化中（changelog 显示多次转写质量更新） |
| **AI总结** | ✅ 自动将语音转为结构化笔记，支持 Custom Instructions 自定义 AI 输出格式 |
| **价格** | 免费版：无限笔记，5分钟录音限制；Plus：$7/月或$39/年（更长录音+第三方集成） |
| **离线** | ❌ 需网络（AI转写在云端） |
| **隐私** | 音频上传云端处理 |
| **独特优势** | **唯一支持 CarPlay 的语音笔记APP**，开车场景完美适配 |
| **不足** | 转写质量不如 Whisper；免费版5分钟限制；云端处理有隐私顾虑 |

### 🥈 Just Press Record — 老牌录音转写之王

| 维度 | 详情 |
|------|------|
| **快捷指令** | ✅ 可通过 Shortcuts 触发打开APP并开始录音（URL Scheme/Run Shortcut） |
| **触发方式** | Apple Watch ✅（背景录音）、Widget ✅、Siri ✅、Shortcuts ✅ |
| **转写** | Apple 系统语音识别，离线可用，中英文支持较好 |
| **AI总结** | ❌ 无内置AI总结，需通过 Shortcuts 发送到 ChatGPT 等外部服务 |
| **价格** | $4.99 **一次性购买**（性价比最高） |
| **离线** | ✅ 完全支持离线录音+转写 |
| **隐私** | ✅ 本地处理，iCloud 同步可控制 |
| **独特优势** | 离线能力、一次性付费、Apple Watch 背景录音、稳定成熟 |
| **不足** | 无AI总结（最大短板）；转写准确率不如 Whisper |

### 🥉 Drafts + Shortcuts — 最灵活的组合方案

| 维度 | 详情 |
|------|------|
| **快捷指令** | ✅ 最丰富的 Shortcuts actions（Create Draft、Append to Draft、Get Draft 等） |
| **语音输入** | 通过 Shortcuts 的 "Dictate Text" action 实现语音听写 → 直接创建 Draft |
| **AI总结** | ✅ 内置 OpenAI 集成（需自备 API Key），支持摘要/翻译/创意生成等 |
| **价格** | 免费 + Pro **$1.99/月或$19.99/年**（AI等功能需 Pro） |
| **独特优势** | Shortcuts 集成最深入，可构建任意复杂工作流，AI 集成灵活，**价格极具性价比** |
| **不足** | 语音输入是"听写"而非"录音"（不保存原始音频）；听写质量依赖系统 |

### Aiko — 最佳纯转写工具

| 维度 | 详情 |
|------|------|
| **快捷指令** | ✅ 支持 Shortcuts actions（可从 Shortcuts 调用 Aiko 进行转写） |
| **转写** | OpenAI Whisper 本地运行，转写质量顶级，多语言支持 |
| **AI总结** | ❌ 无AI总结功能 |
| **价格** | **完全免费** |
| **离线** | ✅ 100% 设备端运行 |
| **隐私** | ✅ 音频不离开设备 |
| **独特优势** | 免费 + 离线 + 高质量转写 + 隐私最佳 |
| **不足** | 无内置录音功能（需导入音频）；无AI总结；定位为纯转写工具 |

### Apple 原生方案（Voice Memos + Notes + Shortcuts）

| 维度 | 详情 |
|------|------|
| **Voice Memos** | iOS 18 支持自动转写，但 Shortcuts actions 受限（仅 Create/Play/Delete），**无法直接获取转写文本或导出音频文件** |
| **Notes** | iOS 18 支持录音+实时转写，**可通过 Shortcuts 调用**。beard.fm 展示了完整的自动化方案：录音→转写→AI 摘要→保存 |
| **优势** | 完全免费、系统自带、iCloud 同步 |
| **不足** | Voice Memos Shortcuts 集成太弱；Notes 方案需要 iOS 18+；AI 总结需外接 ChatGPT |

### 闪念 — 中文场景最佳

| 维度 | 详情 |
|------|------|
| **转写** | 语音识别率 97%+（官方宣传数据），支持普通话+方言+英语，中文场景表现最佳 |
| **AI** | AI 自动整理灵感，支持 Apple Watch、锁屏 Widget 快速记录 |
| **价格** | 有免费版，Pro 功能需付费 |
| **不足** | Shortcuts 集成能力未明确（很可能不支持）；更偏中文生态 |

---

## 四、推荐方案

### 方案A：Cleft Notes 单APP方案（推荐新手）

```
触发方式（多入口）：
├── 走路：Apple Watch 表盘 complication → 一键录音
├── 开车：CarPlay 车屏 → New Note
├── 日常：Widget / APP 内直接录
└── 自动化：Shortcuts 可调用 Cleft actions

录音转写：AI 自动转写 → 结构化笔记
AI 总结：内置 AI 自动整理，Custom Instructions 自定义输出格式
定期整理：通过 Shortcuts Automation（Time of Day）定期收集未整理笔记
```

**适用人群**：希望一个APP搞定、经常开车、不想折腾工作流
**成本**：免费版够用（5分钟限制），重度用 $39/年
**缺点**：需网络、转写在云端

### 方案B：Just Press Record + Drafts + Shortcuts（推荐隐私敏感用户）

```
触发方式：
├── iPhone：Widget / Action Button（15 Pro+）
├── Apple Watch：背景录音
├── AirPods：Hey Siri "用Just Press Record录音"（延迟2-4秒）
└── Shortcuts：URL Scheme 触发

录音：JPR 录音 + 离线转写（Apple 语音识别）
转写文本：通过 Shortcuts 自动发送到 Drafts
AI 总结：Drafts 内置 OpenAI 集成处理，或 Shortcuts 调用 ChatGPT
定期整理：Shortcuts Automation 每日22:00触发 → 汇总当天 Drafts 中标记的灵感 → AI 总结
```

**适用人群**：重视隐私（离线转写）、一次性付费+低价订阅、愿意搭建工作流
**成本**：$4.99（JPR） + $19.99/年（Drafts Pro） + OpenAI API 按量付费
**缺点**：需要手动搭建 Shortcuts 工作流

### 方案C：Drafts + Dictate Text + AI（最轻量、无音频留存）

```
触发方式：
├── Siri：Hey Siri + 自定义短语（如"Hey Siri, 灵感"）
├── Action Button：绑定 Drafts 录入 Shortcut
└── Widget：Drafts Widget

录音→文字：Shortcuts "Dictate Text" → 直接创建 Draft（不保留原始音频）
AI 总结：Drafts 内置 OpenAI 集成（需 API Key）
定期整理：Drafts 内的 Action 可批量处理标记的 draft
```

**适用人群**：不需要保留原始音频、纯文字工作流、追求最快捕获速度
**成本**：Drafts Pro **$19.99/年** + OpenAI API 按量付费
**缺点**：不保存原始音频；听写质量依赖网络和系统

### 方案D：Aiko + 任意录音APP（最佳转写质量）

```
录音：Just Press Record / Apple Voice Memos / 任意录音APP
转写：通过 Shortcuts 将音频文件传给 Aiko（Whisper 本地转写）
AI 总结：Shortcuts 调用 ChatGPT 总结
```

**适用人群**：对转写准确率要求最高、重视隐私（全离线）
**成本**：$4.99（JPR）+ Aiko（免费）+ ChatGPT Free
**缺点**：多APP切换；工作流最复杂

---

## 五、定期AI总结工作流设计

### 每日灵感汇总自动化（基于 Shortcuts）

```
Shortcuts Automation → 每天 22:00 触发
    │
    ├── Step 1：收集来源
    │   ├── Cleft Notes：获取今天创建的笔记（需 Cleft Shortcuts action）
    │   ├── Just Press Record：获取今天转写的文本
    │   └── 或 Drafts：获取 workspace 中标记 #灵感 的 draft
    │
    ├── Step 2：合并文本
    │   └── Shortcuts 的 Text 组合 action
    │
    ├── Step 3：AI 总结
    │   ├── ChatGPT Action（推荐）
    │   │   Prompt: "以下是今天的灵感录音转写，请：1. 提取核心创意 2. 按主题分类 
    │   │            3. 标注最有价值的想法 4. 生成可用的文案素材"
    │   └── 或 Drafts 内置 AI（需 API Key）
    │
    ├── Step 4：保存结果
    │   └── 保存到 Notes / Drafts / Obsidian / 指定位置
    │
    └── Step 5：可选通知
        └── 发送推送通知确认完成
```

### 可行性评估

| 方案组件 | 可行性 | 说明 |
|----------|--------|------|
| Shortcuts 定时触发 | ✅ 完全可行 | Time of Day Automation 原生支持 |
| 收集当天笔记 | ⚠️ 取决于APP | Cleft/Drafts 有 actions 支持；JPR 需手动导出 |
| ChatGPT 总结 | ✅ 完全可行 | ChatGPT Shortcuts integration 原生支持 |
| 结果保存 | ✅ 完全可行 | Notes/Drafts/文件系统 均支持 |
| 端到端自动化 | ⚠️ 部分APP需手动步骤 | JPR 导出需手动；Cleft/Drafts 可全自动 |

---

## 六、场景适配建议

| 场景 | 最佳方案 | 触发方式 |
|------|---------|---------|
| 🚗 开车 | Cleft Notes | CarPlay 车屏一键录音 |
| 🚶 走路 | JPR 或 Cleft | Apple Watch 一键录音 |
| 🏃 运动 | JPR | AirPods + Hey Siri（免手持） |
| ☕ 咖啡厅 | 任一方案 | APP内直接录 / Widget |
| 🛏 灵感突现 | Drafts | Hey Siri + 听写（最快，3秒内） |
| 📝 定期整理 | Shortcuts Automation | 每日定时自动触发 |

---

## 七、价格对比总览

| APP | 免费版 | 付费方案 | 模式 |
|-----|--------|---------|------|
| Cleft Notes | ✅ 无限笔记（5分钟限制） | $7/月 或 $39/年 | 订阅 |
| Just Press Record | ❌ | $4.99 | **一次性** |
| Drafts | ✅ 基础功能 | **$1.99/月 或 $19.99/年** | 订阅（性价比高） |
| Voicenotes | ✅ 基础功能 | $89.99-99.99/年 | 订阅（偏贵） |
| AudioPen | ✅ 基础功能 | ~$39/年 | 订阅 |
| Aiko | ✅ **完全免费** | — | 免费 |
| Whisper Notes | ❌ | $6.99 | **一次性** |
| 闪念 | ✅ 基础功能 | ¥18/月 或 ¥128/年 | 订阅 |
| TalkNotes | 7天试用 | $19.97/月 | 订阅（最贵） |
| Otter.ai | ✅ 300分钟/月 | $8.33-30/月 | 订阅 |
| Apple原生 | ✅ **完全免费** | — | 免费 |

---

## 八、知识缺口与未解答问题

1. **闪念APP的 Shortcuts 集成能力**未确认，可能不支持
2. **中英混合转写质量**缺乏横向实测数据（Whisper vs Apple vs 闪念）
3. **噪声环境下的转写质量**未实测（走路/开车背景噪声）
4. **Cleft Notes 转写准确率**与 Whisper 对比缺乏量化数据
5. **Shortcuts 定时自动化的可靠性**（是否有执行失败的情况）
6. **AudioPen 的 Shortcuts 支持**未确认

---

## 九、来源列表

1. Apple App Store - Cleft Notes: https://apps.apple.com/us/app/cleft-for-verbal-thinkers/id6479458038
2. Cleft Notes 官方文档（iOS/Watch/CarPlay）: https://learn.cleftnotes.com/user-guides/ios
3. Cleft Notes 定价: https://www.cleftnotes.com/pricing
4. Just Press Record - App Store: https://apps.apple.com/za/app/just-press-record/id1033342465
5. Matthew Cassinelli - JPR Shortcut: https://matthewcassinelli.com/shortcuts/just-press-record/
6. Drafts Shortcuts 文档: https://docs.getdrafts.com/docs/automation/shortcuts
7. Drafts AI 文档: https://docs.getdrafts.com/docs/actions/ai.html
8. Apple Voice Memos 转写: https://support.apple.com/guide/iphone/view-a-transcription-iph00953a982/ios
9. MacRumors - iOS 18 Notes 转写: https://www.macrumors.com/how-to/ios-record-audio-transcribe-notes-app/
10. Beard.fm - Apple Notes + Shortcuts 自动化方案: https://beard.fm/blog/transcribe-and-summarize-podcasts-with-apple-notes-shortcuts
11. Voicenotes - App Store: https://apps.apple.com/us/app/voicenotes-ai-notes-meetings/id6483293628
12. Aiko - App Store: https://apps.apple.com/us/app/aiko/id1672085276
13. Whisper Notes 官网: https://whispernotes.app/
14. Otter.ai 定价: https://otter.ai/pricing
15. 闪念 - App Store: https://apps.apple.com/cn/app/闪念-ai语音笔记/id1397149726
16. AudioPen - App Store: https://apps.apple.com/us/app/audiopen-ai-voice-to-text/id6502638001
17. AudioPen 定价: https://app.audiopen.ai/prime
18. TalkNotes 定价: https://talknotes.io/pricing
19. VoiceBrainDump 横评: https://voicebraindump.com/blog/best-voice-to-text-apps-iphone-2025
20. Nick Gracilla - Dictate Text 工作流: https://www.nickgracilla.com/posts/build-a-voice-first-ux-with-apple-health/

---

## 十、方法论反思

**做得好的**：
- 覆盖了15个候选APP（远超最初的6个候选名单）
- 发现了 Cleft Notes 这个关键APP（唯一支持 CarPlay）
- 给出了4套可落地的完整方案+具体工作流设计
- 通过双 Reviewer 审核发现了3处数据错误并修正

**可改进的**：
- 3个搜索员中有2个超时，导致部分数据需手动补充
- 转写质量的横向对比缺乏实测数据（仅基于二手信息）
- 中英混合场景的评估不足
- 未能在 iOS 设备上实际验证 Shortcuts 工作流

---

## 十一、补充调研：国产APP专项（2026-05-10）

> **调研背景**：用户反馈场景修正——核心场景为**走路/徒步/外出**（非开车），车辆为乐道L60（无CarPlay）。优先看国产APP，特别关注中文语音识别质量、Apple Watch支持、离线能力。

### 11.1 已排除的候选

以下产品经调研后确认**不适用于本场景**：

| APP/产品 | 排除原因 |
|----------|----------|
| **搜狗听写** | 已停止运营。搜狗被腾讯收购后大规模关停产品线（2022年起关闭地图、搜索、阅读、号等），搜狗硬件2024年5月全部停服。搜狗听写早已下架，不可用 |
| **讯飞语记** | iOS版已从App Store下架（2023年9月确认）。科大讯飞用"叮当日程"替代，但功能定位不同（日程管理而非语音笔记）。**替代品：讯飞笔记**（新上架的iOS版，见下方评估） |
| **小米便签/小米录音** | 没有iOS版。小米在App Store上架的是"小米互联服务"和"小米眼镜"等，无语音笔记类APP |
| **华为备忘录** | 没有iOS版。仅预装在华为/鸿蒙设备上。搜索结果全是"如何从华为迁移到iPhone"的教程 |
| **飞书妙记** | 不是独立APP，是飞书APP内置模块。个人版每月300分钟免费转写额度，但飞书定位企业协作，过于笨重，不适合灵感记录场景 |
| **钉钉闪记/听记** | 不是独立APP，是钉钉内置功能。支持长按钉钉APP图标一键录音转写、AI总结，但同样过于笨重，不适合轻量灵感记录 |
| **豆包（字节）录音纪要** | 豆包APP内的智能体功能，非独立录音笔记工具。转写准确率用户反映不够理想，不适合作为主力灵感记录工具 |
| **音书APP** | 专为听障人士设计的沟通工具，核心功能是4米内语音转文字辅助沟通。定位特殊场景，**不适合普通人做灵感语音笔记**。免费但功能不匹配 |

### 11.2 国产APP详细评估

#### 🌟 闪念贝壳（ideaShell）— 国产AI语音笔记新星 ⭐ 强烈推荐

| 维度 | 详情 |
|------|------|
| **开发者** | RoundRedDot团队，由前爱范儿副总Ping创建，设计品味出色 |
| **平台** | iOS、iPad（暂无Android/Web） |
| **Apple Watch** | ✅ **完整支持**。手表端可直接录音，有专属Watch APP和表盘入口 |
| **触发方式** | Apple Watch ✅、Siri ✅、Widget ✅、APP内录音 ✅ |
| **转写** | AI驱动实时语音转写，支持中英文，中文识别质量优秀 |
| **AI能力** | ✅ **核心亮点**。不仅转写文字，还提供：AI整理重写（自动优化文本结构、生成标题摘要、添加标签）、与AI讨论笔记内容、生成智能卡片（ToDo、项目提案等）、基于上下文的理解（识别情绪、意图） |
| **离线** | ⚠️ 支持**离线录音+缓存**，但AI转写和整理需联网。没网时可先存后处理 |
| **Shortcuts** | ❌ 未确认支持 iOS Shortcuts 集成 |
| **导出** | 支持多格式导出，可与多应用对接 |
| **价格** | **¥12/月（年付）或 ¥19/月（月付）**，提供订阅制和买断制选择，还支持按需购买AI点数 |
| **独特优势** | Apple Watch完整支持 + 强大的AI上下文理解（不只是转写，而是"思维伙伴"） + UI设计精美 + 中文优化 |
| **不足** | 无Shortcuts集成；AI功能需联网；暂无Android版 |
| **来源** | 官网 ideashell.ai、少数派评测、知乎评测 |

#### 🌟 inFin（AI语音笔记）— 免费离线王者 ⭐ 值得关注

| 维度 | 详情 |
|------|------|
| **平台** | iOS（仅苹果生态） |
| **Apple Watch** | ⚠️ 未明确确认Watch端独立APP |
| **转写** | ✅ 无限时长录音 + 实时中英文转写。使用**本地大模型**运行，离线可用 |
| **AI总结** | ✅ AI自动总结、自动生成会议纪要。本地运行 |
| **离线** | ✅ **核心亮点**。本地大模型转写+AI总结，不上传云端。徒步/无信号场景完美适配 |
| **隐私** | ✅✅ 音频本地存储不上传，隐私最佳 |
| **Shortcuts** | ❌ 未确认支持 |
| **导入** | 支持导入外部音频文件，不限时长不限次数 |
| **价格** | ✅ **基础功能完全免费，无广告**。Pro版 $9.99/月或$69.99/年 |
| **独特优势** | 完全免费 + 离线AI转写+总结 + 隐私最佳 + 无限时长 |
| **不足** | 本地大模型转写准确率可能略低于云端方案（模型体积与准确率的权衡）；Apple Watch支持不确定；中文转写质量vs国产云端方案有待对比 |
| **来源** | App Store、腾讯云开发者社区评测 |

#### 📝 Get笔记 — 得到团队出品

| 维度 | 详情 |
|------|------|
| **开发者** | 得到APP团队（罗辑思维） |
| **平台** | iOS（App Store可下载） |
| **Apple Watch** | ❌ 未提及Watch支持 |
| **转写** | AI语音转文字，支持27种**方言**精准识别（覆盖面极广）。使用腾讯云ASR技术 |
| **AI总结** | ✅ 智能润色/总结，去除口语化表达和冗余内容 |
| **离线** | ❌ 需联网 |
| **Shortcuts** | ❌ 未确认支持 |
| **录音时长** | 免费版：单次最长10分钟；PRO会员：单次最长60分钟（会议录音2小时） |
| **价格** | **免费版600分钟/月转写时长**（所有免费工具中最长）。PRO会员 **¥199/年**（无限转写） |
| **独特优势** | 免费600分钟/月（最慷慨）+ 27种方言支持 + 得到知识体系生态 |
| **不足** | 无Apple Watch支持；偏知识管理而非灵感捕捉；需联网 |
| **来源** | 官网 biji.com、App Store、知乎评测 |

#### 📝 讯飞笔记 — 科大讯飞iOS新替代品

| 维度 | 详情 |
|------|------|
| **开发者** | 科大讯飞（语音识别行业龙头） |
| **平台** | iOS App Store（新版替代已下架的"讯飞语记"） |
| **Apple Watch** | ❌ 未提及Watch支持 |
| **转写** | 基于讯飞语音引擎，支持实时语音听写+高精会议转写。支持普通话、英语、粤语等十多种语言。**中文转写准确率业界顶级（96.8%+）** |
| **AI功能** | 录音速记、OCR拍照识别、图文编排、智能任务提醒 |
| **离线** | ⚠️ 部分功能支持离线（听写可能依赖系统），高精转写需联网 |
| **Shortcuts** | ❌