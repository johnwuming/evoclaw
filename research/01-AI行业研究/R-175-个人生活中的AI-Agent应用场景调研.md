# 个人生活中的 AI Agent 应用场景调研（R-175）

> **调研编号**：R-175
> **调研时间**：2026-08-02
> **调研范围**：普通人在个人生活（非企业、非开发者）场景中实际使用 AI Agent（智能体）/AI 助手的方式
> **方法说明**：基于中文社区（V2EX/知乎/掘金/小红书/澎湃等）与英文社区（Reddit/HN/X）的真实用户分享、媒体报道与产品实测，每个场景给出具体用法、真实案例（含来源）、工具与效果/痛点。广告软文已标注，供交叉验证。
> **明确排除**：企业级场景（客服/财务/HR/销售自动化）、纯编程开发场景、宏观行业趋势（见 R-174）。

---

## 摘要

个人生活中的 AI 使用已从"问答工具"演变为"生活 Agent"：从"帮我查资料"到"帮我做决策、帮我执行、主动提醒我"。2026 年 3 月国内 AI 原生 App 月活已达 4.4 亿（QuestMobile），豆包以 3.45 亿月活居首——AI 已成为国民级应用，个人生活场景是主战场。

本文梳理了 **7 大类个人生活场景、30+ 具体用例**：

1. **个人助理类**：日程规划、ChatGPT Tasks 定时任务、邮件/消息处理、微信 AI 管家、AI 管待办、"生活教练"
2. **家庭生活类**：AI 做菜谱、AI 记账（月成本不到 1 元）、购物比价、智能家居、家庭做饭决策
3. **生活规划类**：旅行规划（最高频）、健身健康、租房合同审查、健康咨询、人生决策
4. **内容创作类**：小红书/朋友圈文案、AI 视频图片、读书总结、副业变现
5. **知识管理类**：AI 第二大脑、长文消化、AI 家教
6. **情感陪伴类**：AI 伴侣、AI 陪老人、AI 哄娃、游戏搭子、AI 玄学
7. **其他**：脱单辅助、本地生活问答

---

## 一、个人助理类：日程管理、提醒、待办、消息处理

### 1.1 用 ChatGPT 做每日日程规划与任务拆解
- **怎么用**：把一天的任务清单（或一周安排）粘贴给 ChatGPT，让它按优先级排序、估算每项耗时、拆解启动步骤，甚至按"执行力难度"排列。
- **工具**：ChatGPT（免费/付费）、豆包、Kimi
- **真实案例**：Reddit r/adhdwomen 上多位用户分享用 ChatGPT"安排我的一天、记住我的任务并激励我"。一位用户让 ChatGPT 对每个任务给出时间预估、启动步骤和完成标准，把抽象待办变成可执行步骤清单；另一位让 ChatGPT 扮演"ADHD 生活教练"，把待办从最重要到最不重要排序。
  - https://www.reddit.com/r/adhdwomen/comments/1fwzi71/
  - https://www.reddit.com/r/adhdwomen/comments/113glrf/
- **效果与痛点**：对注意力涣散/执行力弱的人群帮助显著（减少决策疲劳）；痛点是没有真正的日历集成，用户需手动把结果搬到日历；任务跨天衔接靠人工维护。

### 1.2 ChatGPT Tasks：定时提醒与周期性任务（"准 Agent"化）
- **怎么用**：在对话里直接说"每天早上 7 点给我天气"、"每周五下午给我一份 AI 新闻总结"、"每天提醒我遛狗"，ChatGPT 会自动在设定时间执行并推送。
- **工具**：ChatGPT Tasks（Plus/Pro，2025 年初上线）
- **真实案例**：官方及大量教程展示的典型用法：每日天气、每周新闻摘要、每天法语练习提醒、定期追踪信息变化（如航班价格）。
  - https://www.ifanr.com/1612179
  - https://zhuanlan.zhihu.com/p/20115539543
- **效果与痛点**：把"提醒"从被动 App 变为主动 Agent；痛点是只能文本推送、无法操作其他 App，属于"准 Agent"。

### 1.3 邮件/消息的起草、摘要与回复
- **怎么用**：把收到的长邮件/消息粘贴给 AI，让它总结要点、起草回复（不同语气版本）；或把啰嗦的消息"润色"成礼貌得体的版本；进阶：让 AI 代回消息（浏览器插件读取聊天上下文）。
- **工具**：ChatGPT、Gmail + Gemini、豆包、Kimi
- **真实案例**：
  - Reddit r/ChatGPT 用户普遍把"帮我写这封邮件/消息"列为最常用功能之一；国内用户用豆包/Kimi 润色微信消息、写请假邮件。
  - Reddit r/ChatGPT 用户："我把 10 封写得好邮件粘贴给 ChatGPT，让它基于这些起草新邮件，效果很好"（https://www.reddit.com/r/ChatGPT/comments/16cu829/）
  - Reddit r/sales 用户："我用 ChatGPT 写邮件，天哪它简直是救星——不再纠结措辞和专业性"（https://www.reddit.com/r/sales/comments/10s24wy/）
  - Reddit r/ChatGPT 用户："我让 ChatGPT 替我回复消息（Chrome 插件），它甚至读邮件/WhatsApp 对话来引用前文"（https://www.reddit.com/r/ChatGPT/comments/11d6vbf/）
- **效果与痛点**：省时明显；痛点是涉及隐私的邮件不宜全量粘贴、AI 起草的语气偶尔过于正式需人工调整、"AI 代聊"削弱真诚感。

### 1.4 让 AI Agent 管待办，把清单"藏"起来（V2EX 真实案例）
- **怎么用**：把脑子里堆着的事一股脑倒给 AI，随时想到什么说什么，每天只问"今天该做哪一件"，其余全部由 AI 收纳。
- **工具**：ChatGPT/Claude + 自建小工具（如 onethingatatime.app）
- **真实案例**：V 友 sumtsui 分享："像把一部分脑子卸载出去了"——自称容易分心的人，用了之后觉得很有用，于是做了一个最小版本（免注册直接用）。典型"AI 当外置大脑/执行助理"用法，反推销、反堆砌清单。
  - https://www.v2ex.com/t/1231454
- **效果与痛点**：显著降低认知负担；痛点是依赖 AI 收纳后需要信任其排序逻辑，长期用需持续投喂。

### 1.5 个人部署的"微信 AI 管家"（V2EX/掘金高频玩法）
- **怎么用**：用开源项目 chatgpt-on-wechat（CoW）把大模型接入个人微信，实现群聊自动回复、知识库问答、定时消息；或部署 DailyClaw 之类住在 Telegram 的个人生活助手（记想法、追踪习惯、提醒反思）。
- **工具**：chatgpt-on-wechat、WeChaty、DailyClaw（开源）
- **真实案例**：
  - V2EX 用户分享 DailyClaw："日常生活琐事的私人助手——记录想法、追踪习惯、提醒反思、总结一天"（https://www.v2ex.com/t/1203647）
  - 知乎用户把 Kimi 接入个人微信，协助管理微信群并解答问题（https://zhuanlan.zhihu.com/p/697582378）
  - 开发者 THESDZ 自建"给 AI 的家庭事务状态机"Now & Again：对 AI 说"帮我看看今天有哪些家务要做"，AI 通过 CLI action-id 持续跟踪、逐步引导完成任务（洗碗、安全检查、任务链），未来规划洗衣完成自动标记待办、智能家居联动（https://www.v2ex.com/t/1225534）
- **效果与痛点**：高度个性化、主动提醒；痛点是需要一定技术门槛（虽开源但部署需动手），微信自动化有封号风险。

### 1.6 "生活教练"式使用（把 ChatGPT 当人生教练/执行功能助手）
- **怎么用**：把生活按"部门"拆分（财务、职业、个人成长、健康），让 ChatGPT 长期维护各领域目标与进度；或让它扮演"ADHD 执行功能教练"。
- **工具**：ChatGPT（记忆功能）、Claude（Projects）
- **真实案例**：
  - Reddit r/ChatGPTPro 用户："我在 ChatGPT 里构建了一个执行功能助手"，把生活分成 Finance/Career/Personal Development 等部门管理（https://www.reddit.com/r/ChatGPTPro/comments/1jztw4t/）
  - Reddit r/ChatGPT："ChatGPT has helped get my whole life in order"——半退休用户用它管理预算和疗愈任务，消除无聊感（https://www.reddit.com/r/ChatGPT/comments/1m0l5wv/）
  - Reddit r/ChatGPTPromptGenius 高赞回复："ChatGPT 不知不觉成了我的人生教练——过去一年我戒了烟酒、减了肥、血指标恢复正常"（https://www.reddit.com/r/ChatGPTPromptGenius/comments/1opsy72/）
  - Reddit r/ChatGPT 热帖："告诉我你最喜欢的'重整人生'提示词"，高赞思路是"建立强化你内在价值的日常惯例、用系统自动化成功"（https://www.reddit.com/r/ChatGPT/comments/1guygcv/）
  - IndieHackers 用户："我平均每天花一小时和 ChatGPT 高级语音模式对话"，把 AI 用于日常生活中的重复任务，同时承认在优化性任务上仍依赖真人（https://www.indiehackers.com/post/lifestyle/ai-isnt-even-close-to-replacing-my-personal-assistant-here-s-why-i1lThXvkHzkm1bo1upQw）
  - HN 用户分享用 LLM 做个人日志系统：每天收到邮件→回复→自动归档到页面，AI 辅助记录与反思（https://news.ycombinator.com/item?id=43681287）
- **效果与痛点**：长期记忆让 AI 成为真正"懂你"的助理；痛点是过度依赖风险、记忆内容涉及隐私、AI 的"教练"建议有时过于通用。

### 1.7 AI 处理个人法律事务（个人法务助理）
- **怎么用**：把纠纷材料（事故认定书、合同、聊天记录）交给 AI，让它协助整理材料、起草文书、梳理辩论要点。
- **工具**：ChatGPT、DeepSeek、Kimi
- **真实案例**：V 友 erbin 遇交通事故责任纠纷，金额不大没请律师，全程"让 AI 协助我整理材料并提交"，包括申请法院调令调取道路监控、执法音视频，自己写起诉书、书面辩论意见。虽然结果不理想（法院维持原判），但展示了普通个人用 AI 处理"本该找专业人士"的流程。
  - https://www.v2ex.com/t/1231464
- **效果与痛点**：大幅降低专业服务门槛；痛点是 AI 不掌握个案法律细节，重大事项仍需律师把关，结果存在不确定性。

---

## 二、家庭生活类：做饭、记账、购物、智能家居

### 2.1 AI 做菜谱与"看冰箱做菜"
- **怎么用**：告诉 AI"冰箱里有鸡胸肉、西兰花、鸡蛋，帮我推荐今晚做啥"，或拍照上传冰箱食材，AI 识别后推荐菜谱（含步骤、营养分析）。
- **工具**：ChatGPT、豆包、DeepSeek（食神烹饪大模型）、RecipeGenie、ChefBot
- **真实案例**：
  - 知乎实测"食神"烹饪大模型：告诉它冰箱有什么食材，推荐合适菜谱并联动数字厨电（https://zhuanlan.zhihu.com/p/32025436817）
  - Reddit r/WholeFoodsPlantBased 用户："告诉 ChatGPT 手头有什么食材，要求低脂高纤的当季菜谱，它做得很好"（https://www.reddit.com/r/WholeFoodsPlantBased/comments/1frgl3o/）
  - Reddit r/SAHP（全职妈妈社区）："用 ChatGPT 做餐食规划彻底改变了我的生活——我建了一个专属对话，它学会了我们全家人的饮食偏好，推荐食谱、生成餐食计划，太棒了"（https://www.reddit.com/r/SAHP/comments/1d0d59h/）
  - Reddit r/ChatGPT 用户："我每天用 ChatGPT 规划三餐——几秒就给我一份靠谱的周餐计划，减了 10 磅，吃得更干净、更省钱，而且我真的享受做饭了"（https://www.reddit.com/r/ChatGPT/comments/1ma9c4n/）
  - Reddit r/Frugal 用户："我让 AI 给家里做每周 100 美元以内的餐食计划"——评论区则质疑预算真实性，提示 AI 的成本估算未必准确（https://www.reddit.com/r/Frugal/comments/11gayb7/）
  - Reddit r/ChatGPT 用户："用 ChatGPT 半年减了 20 磅（9kg）——上传每餐照片让它帮我计算和追踪"（https://www.reddit.com/r/ChatGPT/comments/1g97ewu/）
  - Reddit r/PersonalFinanceNZ 用户：用 ChatGPT 生成"健康、孩子友好、快手、省钱、当季"的菜谱+购物清单，省了钱和时间（https://www.reddit.com/r/PersonalFinanceNZ/comments/13v41u0/）
  - Reddit r/foodhacks 用户："拍一张食品柜照片问 ChatGPT 能做什么菜，或者让它为简单食谱建议采购清单——真的很棒"（https://www.reddit.com/r/foodhacks/comments/1ch7jmx/）
  - Reddit r/ChatGPT 用户："我让 ChatGPT 决定我的整理收纳待办清单"——它先从我自己的物品开始，制定了两周断舍离计划（Day 1 整理顶层抽屉衣服……）（https://www.reddit.com/r/declutter/comments/1mfu0et/）
  - Homes & Gardens 编辑实测：让 ChatGPT 生成清理和断舍离的高效待办清单（https://www.homesandgardens.com/solved/chatgpt-decluttering-to-do-list）
- **效果与痛点**：解决"每天吃什么"的决策疲劳；痛点是 AI 不知道冰箱真实库存（除非拍照识别）、菜谱偶有翻车（用量/火候不靠谱）、仍需人工判断。

### 2.2 家庭做饭决策小程序《这顿不发愁》（vibe coding 家庭场景）
- **怎么用**：选人数、口味、忌口，直接给一桌"能做、能买、不会乱搭"的菜，衍生采购清单、做菜顺序、计时、冰箱食材匹配功能。
- **工具**：AI 辅助开发（codex）自建小程序
- **真实案例**：V 友 NetAverse 分享：和媳妇每天互相问"吃啥"最后总点外卖，于是用 AI 把第一版很快跑起来做成选菜小程序，上线一周 5000 人用过。作者强调"AI 把动手门槛降下来了，但'做什么、哪里不对、愿不愿意改到能用'仍靠人"。
  - https://www.v2ex.com/t/1230535
- **效果与痛点**：解决家庭高频决策冲突、真实使用人数可观；痛点是自建工具需持续维护，通用性有限。

### 2.3 AI 家庭记账与账单分析
- **怎么用**：说一句话"今天买菜花了 80 块"自动记账；或上传小票/账单截图，AI 自动识别金额、分类；月底让 AI 分析支出结构、给出省钱建议。
- **工具**：AI 日常记账（小程序）、百事 AA 记账、随手记 AI 版、ChatGPT/豆包（Excel 账单粘贴分析）
- **真实案例**：
  - 知乎测评"AI 日常记账"小程序：主打 AI 录入（说话即记）、自动分类、端侧隐私保护（https://zhuanlan.zhihu.com/p/2049257157950956726）
  - V2EX 用户"三个月后，AI 随手记告诉我最应该改变的是什么"：AI 分析消费习惯给出改变建议（https://www.v2ex.com/t/1182727）
- **效果与痛点**：记账门槛大幅降低（语音/拍照代替手动输入）；痛点是部分功能付费、隐私顾虑（家庭账本数据上传云端）。

### 2.4 银行短信自动记账（AI 记账，月成本不到 1 元）
- **怎么用**：iOS 快捷指令把银行短信转发到 App（可自定义规则、预脱敏），App 内配置用户自己的 DeepSeek API Key，AI 识别短信内容自动分类记账，后台自动记录，可手动修改补充。
- **工具**：自建 iOS App + DeepSeek API
- **真实案例**：V 友 kasusa 开发中的 iOS App："只需要一点点操作，以及每个月花费不到 1 块钱的 AI 费用"就能实现自动化记账。是"AI+自动化=记账不费手"的典型家庭财务用法。
  - https://www.v2ex.com/t/1230180
- **效果与痛点**：成本极低、无需手动录入；痛点是需自行配置 API Key、短信脱敏处理，仅限 iOS 生态。

### 2.5 不用每天记账的财务工具 Prismira（AI 分析账单）
- **怎么用**：支持微信、支付宝、美团账单导入，银行 PDF 和图片账单智能解析；AI 支持自然语言查询分析、给建议、智能分类和去重。作者用法："每个月定期导出账单导入，花很少时间得到月度收支报告"。
- **工具**：Prismira（个人 side project）
- **真实案例**：作者 serenader 自述记账九年坚持不下来，于是给自己做了套系统。属于"账单解析+自然语言问财务"的典型用法。【开发者自荐】
  - https://www.v2ex.com/t/1229742
- **效果与痛点**：把"每天记账"变成"每月花 10 分钟导账单"；痛点是依赖各平台账单导出格式、早期产品稳定性待验证。

### 2.6 AI 购物比价与"劝你别买"
- **怎么用**：把想买的东西（型号/链接/截图）发给 AI，让它多平台比价、查参数、看评价、算满减，甚至直接问"这个值得买吗"。
- **工具**：纳米 AI 搜索、比价狗、慢慢买、ChatGPT/豆包（搜索模式）
- **真实案例**：
  - 知乎专栏"最懂购物的 AI，竟然会劝你别买了"：复杂购物过程压缩成与 AI 的一段对话（https://zhuanlan.zhihu.com/p/2037915825445844689）
  - 开发者实测纳米 AI 超级搜索解决多平台比价难题，可直接加购物车（https://developer.volcengine.com/articles/7510083759937421353）
  - 知乎热帖：用 Gemini 分析 TA 半年朋友圈生成"完美礼物清单"（https://www.zhihu.com/question/1936480001085126471）
  - Reddit r/MiddleClassFinance 用户："我把每月预算跑进 ChatGPT，结果惊人——我把每笔支出输入进去，让它分析我的财务状况"（https://www.reddit.com/r/MiddleClassFinance/comments/1o68vrk/）
  - Reddit r/mintuit 用户："ChatGPT Finance 开始像 Mint/Monarch 的替代品了——它不像预算仪表盘，更像个人财务分析师"（https://www.reddit.com/r/mintuit/comments/1uana12/）
  - Reddit r/povertyfinance 用户：把全部财务信息交给 ChatGPT，让它给出建议（https://www.reddit.com/r/povertyfinance/comments/1utdxgb/）
- **效果与痛点**：比价效率高；痛点是 AI 数据有时滞后（价格更新不及时）、推荐链接带广告成分，需人工核对。

### 2.7 智能家居：语音/Agent 控制家庭场景
- **怎么用**：通过智能音箱（小爱同学/天猫精灵）+ AI，一句话控制灯光、空调、窗帘；设置回家自动开灯、离家自动关电等场景联动；进阶用户用米家极客版实现"小爱主动问询"。
- **工具**：小米小爱/米家、Home Assistant + AI、天猫精灵
- **真实案例**：
  - 米家用户设置复杂条件联动："通过联动设备+米家场景模式，实现更多单纯米家实现不了的智能家居体验"（https://web.vip.miui.com/page/info/mio/mio/detail?postId=25315436）
  - 智能家居论坛用户用小爱音箱控制 HA 设备，实现主动问询与应答（https://bbs.hassbian.com/thread-29988-1-1.html）
- **效果与痛点**：语音控制对老人小孩友好；痛点是"伪智能"居多——大部分是预设场景而非真正的自主 Agent，跨品牌设备互通仍是痛点。

### 2.8 自托管 AI 家庭监控 NVR（云瞰 SkyView）
- **怎么用**：摄像头 → NAS/迷你主机 → 手机/Home Assistant。AI 能力：人形/车辆/包裹/跌倒/婴儿哭声事件检测、**自然语言搜录像**（如"昨天下午门口有没有快递员"）、HA/MQTT/Webhook 联动。
- **工具**：云瞰 SkyView（自托管开源方案）
- **真实案例**：V 友 mMartin 分享自建家庭视频中枢，解决多品牌摄像头各一个 App、云存储按设备收费、回放靠拖时间轴的问题，强调录像尽量留本地、不绑定品牌。【开发者自荐】
  - https://www.v2ex.com/t/1217249
- **效果与痛点**：把"看监控"升级为"问监控"；痛点是自托管需要 NAS/主机硬件和一定动手能力，属于进阶玩家玩法。

### 2.9 AI 家庭 DIY/维修指导
- **怎么用**：把要修的东西、遇到的问题描述给 AI（可附照片），让它给出排查步骤、工具清单、注意事项；或让它把网上教程拆解成一步步操作。
- **工具**：ChatGPT（多模态）、豆包、Gemini
- **真实案例**：
  - Reddit r/DIY 用户（DIY 新手）："根据我的个人经验，它适合给想法，但实际操作步骤要小心"（https://www.reddit.com/r/DIY/comments/1o6ptlu/）
  - Reddit r/ChatGPT 用户警告："别完全依赖 ChatGPT 做 DIY"（https://www.reddit.com/r/ChatGPT/comments/1mtz6bz/）
  - Reddit r/AI_Agents 用户：想建 AI agent 管理"家庭维修和餐食规划任务"的认知负担（https://www.reddit.com/r/ChatGPT/comments/1tolh94/）
- **效果与痛点**：降低 DIY 入门门槛、随时可问；痛点是安全敏感操作（电路/燃气）风险高，AI 步骤可能有误，需结合视频教程和常识判断。

---

## 三、生活规划类：旅行、健身、健康、租房、决策

### 3.1 AI 旅行规划师（最高频场景之一）
- **怎么用**：告诉 AI"7 月去东京 5 天，预算 8000，喜欢美食和 citywalk"，生成每日行程；进阶玩法：把小红书攻略链接贴给 AI 一键"抄作业"生成同款行程；或让 AI 生成行李清单。在扣子（Coze）等平台，普通用户也可零代码搭建自己的"旅行规划助手"智能体（https://blog.csdn.net/sinat_36184075/article/details/149075064）
- **工具**：ChatGPT、DeepSeek、豆包、Kimi、圆周旅迹（App）、飞猪 AI 行程助手、Manus、扣子 Coze
- **真实案例**：
  - 腾讯网报道：刘女士表示"我试了 DeepSeek 和豆包，比在小红书上一个个查攻略方便多了，效率提高不少"（http://auto.cyol.com/gb/articles/2025-03/19/content_qb6Z03SK0q.html）
  - 小红书用户必备 3 款 AI 工具：圆周旅迹把他人攻略笔记链接贴入自动生成行程并地图标记（https://zhuanlan.zhihu.com/p/17891744223）
  - Reddit：在里斯本用过 7 个 ChatGPT 旅行提示词，获得混合观景台、电车和秘密屋顶咖啡馆的 3 天路线（https://www.reddit.com/r/ChatGPTPromptGenius/comments/1o134ut/）
  - Reddit r/ChatGPT 用户："我用 ChatGPT 的 Deep Research 规划假期，结果让我震惊"——把"你是我的私人旅行研究员，我想在 5 月中旬去墨西哥度 5 天假"这类提示词交给它（https://medium.com/ai-your-way/i-used-chatgpts-deep-research-to-plan-my-vacation-and-it-blew-my-mind-3ec17220ad20）
  - Reddit r/ParisTravelGuide 用户的警醒："每个 AI 生成的行程都让游客在城市里毫无意义地来回穿越，坐的地铁线路根本不合理"（https://www.reddit.com/r/ParisTravelGuide/comments/1jyglnk/）——提示 AI 行程的地理排序缺陷
  - Reddit r/ChatGPT 用户：用 ChatGPT 自动生成并在地图上标记旅行行程（https://www.reddit.com/r/ChatGPT/comments/13cn5xz/）
  - Manus 旅行规划 playbook：为家庭度假定制每个人兴趣的行程（https://manus.im/zh-cn/playbook/ai-trip-planner）
- **效果与痛点**：效率提升巨大（分钟级出行程）；痛点是信息滞后（景点营业时间/票价过时）、网红店推荐偏差、无法真正下单（订机票酒店仍需人工），CCTV 报道指出 AI 行程存在"信息滞后、价格偏差、广告诱导"（https://culture-travel.cctv.com/2026/04/14/ARTI8F2fbA3eaAW4C4oE1Hy9260414.shtml）

### 3.2 三句话生成可视化一日游攻略（AI+地图 MCP）
- **怎么用**：用 AI 结合高德地图 MCP Server 和 EdgeOne Pages Deploy，通过三句话生成一份可视化的周末一日游行程页面并秒级部署上线。
- **工具**：AI + 高德地图 MCP + EdgeOne Pages
- **真实案例**：掘金作者"陈明勇"分享，属于"自然语言 → 结构化行程 + 地图可视化"的旅行规划自动化玩法，展示 AI Agent 与真实生活服务（地图）打通的能力。
  - https://juejin.cn/post/7494149952698613770
- **效果与痛点**：秒级生成可分享的可视化行程；痛点是需要一点技术配置（MCP），普通用户可直接用现成 App 替代。

### 3.3 AI 健身/健康管理
- **怎么用**：把身体数据（身高体重、目标）告诉 AI，生成训练计划/减脂食谱；语音或拍照记录饮食，AI 算热量；运动后让 AI 分析动作是否标准。
- **工具**：ChatGPT/豆包（提示词模板）、轻牛健康、麦瑞克 AI 私教 MIA、Impakt
- **真实案例**：
  - 新浪报道"他们拿 AI 当私教玩出减肥新高度"：社交媒体出现大量用 AI 制定减肥方案的指令教程（https://cj.sina.cn/articles/view/1893892941/70e2834d02701rj34）
  - Reddit r/ChatGPT 用户：用 ChatGPT 做个性化训练和饮食计划，每周 check-in，甚至生成双周购物清单（https://www.reddit.com/r/ChatGPT/comments/1ma9c4n/）
  - Reddit r/ChatGPT 用户："用 ChatGPT 减了 35 磅——输入年龄、体重、身高、活动水平，它帮我计算维持热量"（https://www.reddit.com/r/ChatGPT/comments/1h18hhs/）
  - Reddit r/personaltraining 用户："我用 ChatGPT 代替私教——大概是我遇到过最好的教练，把生酮、力量训练、断食和恢复组合到我从没试过的方式"（https://www.reddit.com/r/personaltraining/comments/1keka85/）
  - Reddit r/ChatGPT 用户："我以前花几千美元请体态改造教练，今年用 ChatGPT 做到了"（https://www.reddit.com/r/ChatGPT/comments/1kedjca/）
  - 反面声音：Reddit r/workout 用户警告"ChatGPT 无法评估你的身体和目标，很可能幻觉出营养事实，别完全依赖它当教练"（https://www.reddit.com/r/workout/comments/1rjziz6/）
  - 知乎健身专栏介绍 MIA："百科全书级健身知识中枢，输入身体数据与目标即刻生成科学运动计划"（https://zhuanlan.zhihu.com/p/1961885587494663063）
  - 掘金作者"一只牛博"：三伏天体重秤给了自己一击，于是在 EdgeOne Makers 上从 0 到 1 上线 AI 健康教练用于减肥期饮食/运动管理，文章 13000+ 浏览（https://juejin.cn/post/7665614902707617827）
- **效果与痛点**：替代部分私教/营养师功能，成本极低；痛点是 AI 不懂你的真实体能边界，动作安全性需人工判断，极端情况下（如新手爸妈按豆包建议喂奶）可能出事故（https://m.thepaper.cn/newsDetail_forward_33274381）

### 3.4 AI 租房避坑与合同审查
- **怎么用**：把房源描述/合同文本粘贴给 AI，让它标出风险点（押金条款、违约金、维修责任、二房东风险）；让 AI 生成看房 checklist；用 AI 处理租房价格 Excel 做比价分析。
- **工具**：ChatGPT、DeepSeek、开源合同审查 Agent（contractguard）、"超级 excel"网站
- **真实案例**：
  - 知乎"我开源了个合同审查 Agent，30 秒找出霸王条款"：作者租房时发现合同第十条藏着退租陷阱，于是做了合同审查 Agent，扫描租房合同找红旗条款（https://zhuanlan.zhihu.com/p/2024535189133489158）
  - 腾讯云：AI 检测 50 种租房合同漏洞（违约金过高、维修责任缺失等）（https://cloud.tencent.com/developer/news/738321）
  - Reddit r/LARentals 用户提醒："签任何租约前，把租约上传到 ChatGPT 或 Grok AI 分析有没有异常或过分条款"（https://www.reddit.com/r/LARentals/comments/1mrctx3/）
  - Reddit r/SideProject 用户："我被房东坑了，所以我建了一个 AI 分析工具专门找租约陷阱"（https://www.reddit.com/r/SideProject/comments/1izurtr/）
  - 反面提醒：Reddit r/PropertyManagement 从业者呼吁"租客别用 ChatGPT 处理纠纷"——AI 不了解当地法律细节（https://www.reddit.com/r/PropertyManagement/comments/1qq22v1/）
  - V 友 mqx 开发的"超级 excel"：配置 DeepSeek API Key 后用自然语言操作 Excel，示例包括"根据第三行的省份和租房价格所在列的数据制作数据报表"（https://www.v2ex.com/t/1229909）
- **效果与痛点**：把法律风险识别平民化；痛点是 AI 不能替代律师（复杂纠纷仍需人工）、合同文本识别对扫描件质量有要求。

### 3.5 AI 健康咨询与症状解读（热门且有争议）
- **怎么用**：把体检报告/化验单/症状描述发给 AI，让它逐行解释指标、给出可能的病因方向、整理"该问医生什么问题"清单。
- **工具**：ChatGPT、豆包、DeepSeek
- **真实案例**：
  - Reddit r/ChatGPT 高赞帖："我完全不信任 ChatGPT 的医疗建议，但现在我彻底被征服了——它帮我度过了癌症诊断，逐行解读了我的所有医学报告，并告诉我该问医生什么问题"（https://www.reddit.com/r/ChatGPT/comments/1ppflew/）
  - Reddit 用户普遍表示"ChatGPT 的医疗解释比 15 分钟门诊更清楚"，但医生用户强调"可以帮你做功课，不能替代医生"（https://www.reddit.com/r/ChatGPT/comments/1lruqba/）
- **效果与痛点**：解释专业报告的能力强、缓解就医焦虑；痛点是误诊风险极高，Mother Jones 记者正在调查 AI 健康问答事故案例（https://www.reddit.com/r/ChatGPT/comments/1thd2we/），国内也有新手爸妈按豆包建议喂奶致婴儿不适的报道（https://m.thepaper.cn/newsDetail_forward_33274381）

### 3.6 AI 人生决策咨询（"帮我做决定"）
- **怎么用**：把纠结的问题（换工作、分手、搬家、买房）完整背景告诉 AI，让它列出利弊、给出决策框架，甚至扮演"最好的朋友/人生教练"陪聊。
- **工具**：ChatGPT、Pi（情感型 AI）、豆包
- **真实案例**：
  - 知乎问题"27 岁感到多无力的人可否借助 ChatGPT 获得人生经验"（https://www.zhihu.com/question/582753341）
  - 澎湃报道 Pi 情感型聊天机器人受年轻人追捧："它像渣男一样会聊天"，有人把它当知心朋友（https://m.thepaper.cn/newsDetail_forward_25882429）
  - 哈佛商业评论中文版：让 ChatGPT 当决策好帮手（https://www.hbrtaiwan.com/article/22518/using-chatgpt-to-make-better-decisions）
- **效果与痛点**：提供"无压力的倾诉+结构化思考"；痛点是 AI 不了解你的全部真实处境，重大决策仍需自己拍板，长期依赖可能弱化决策能力。

---

## 四、内容消费与创作类

### 4.1 写小红书/朋友圈文案
- **怎么用**：给 AI 一段素材（照片描述、产品信息、想表达的情绪），让它生成 3-5 版小红书笔记/朋友圈文案（不同风格：种草、文艺、搞笑）；进阶：让 AI 模仿爆款结构。
- **工具**：豆包、Kimi、DeepSeek、稿定 AI 文案、扣子 Coze（自建）
- **真实案例**：
  - 知乎专栏"用 AI 写朋友圈和小红书：3 分钟搞定日常创作"：核心不是让 AI 替你写，而是让它替你组织语言（https://zhuanlan.zhihu.com/p/2009355012489367955）
  - 知乎用户分享"如何用 DeepSeek 一键生成小红书爆款笔记"（https://www.zhihu.com/question/648297532）
  - 知乎分享"用 AI 仿写搭建小红书爆文流水线"（https://zhuanlan.zhihu.com/p/1937210578855755786）
  - 掘金作者实测 6 个 AI 小红书文案工具对比（运营者视角，非单一产品软文）（https://juejin.cn/post/7377901375000313919）
  - 掘金作者用扣子两分钟搭建"朋友圈文案生成 AI 工具"，输入场景/心情自动出文案（https://juejin.cn/post/7330426020996726824）
- **效果与痛点**：创作门槛骤降，3 分钟出稿；痛点是 AI 味重需人工润色、平台对 AI 内容有隐性限流风险、同质化严重。2026 年 2 月起小红书要求 AI 生成内容强制标识（https://ai.zol.com.cn/1133/11336191.html），对依赖 AI 批量生产的创作者影响明显。

### 4.2 AI 做视频/图片（即梦、剪映、MiniMax）
- **怎么用**：即梦 AI 文生图/图生视频、剪映数字人口播（不露脸做视频）、AI 配音；组合工作流：DeepSeek 写脚本 → 即梦生成画面 → 剪映剪辑配音；进阶：直接放入参考图片/视频/音频让模型理解人物长相、镜头运动、声音节奏。
- **工具**：即梦 AI、剪映（数字人）、豆包、可灵、MiniMax H3、Midjourney + Seedance
- **真实案例**：
  - 知乎"即梦+deepseek+剪映，不用出镜，10 分钟生成数字人口播视频"：作者不会拍摄不会剪辑，用 AI 完成了第一条短视频（https://zhuanlan.zhihu.com/p/31761096476）
  - 知乎"原来剪映才是 AI 神器"：普通人创作电影解说、科普视频完全不用出镜（https://zhuanlan.zhihu.com/p/1957125121346082023）
  - V 友 littlePP 实测 MiniMax H3：同时放入图片、参考视频和音频，生成后还能用文字修改局部，判断"以后用户可能不再学复杂提示词，而是直接把参考素材扔进去"（https://www.v2ex.com/t/1231362）
  - V 友分享 AI 视频创作四阶段管线：先生成关键帧 → 精修 → 生成对话音频 → 视频+口型同步，核心技巧"先用便宜音频验证表演效果，再投贵的视频渲染"（https://www.v2ex.com/t/1229345）【疑似软文，教程推广向】
- **效果与痛点**：内容生产成本大幅下降，激发普通人创作欲；痛点是质量仍不及专业制作、同质化内容泛滥、平台审核收紧。

### 4.3 旅行照消路人/水印（AI 图片修复）
- **怎么用**：上传旅行照，AI 一键消除路人、水印、杂物（电线、垃圾桶、路牌），30 秒内搞定。
- **工具**：PixImagen Remove Object 等网页工具
- **真实案例**：V 友 fancylifeyrs 实测：三步 30 秒内搞定、免费、无水印、纯浏览器端、处理完自动删上传图片；同时诚实列出缺点（免费额度有限、大面积消除有填充痕迹）。【疑似软文，可信度中等】
  - https://www.v2ex.com/t/1231054
- **效果与痛点**：拯救废片效率极高；痛点是免费额度限制、大面积消除痕迹、隐私（上传照片需信任处理端）。

### 4.4 AI 读书总结与阅读搭子
- **怎么用**：把书的关键章节/PDF 丢给 AI 总结；或接入微信读书 Skill，让 AI 读取你的书架、划线、笔记，做深度分析和推荐。
- **工具**：Kimi（长文本）、ChatGPT、微信读书 Skill、NotebookLM
- **真实案例**：
  - 微信读书官方 Skill 上线：AI 可读你的书架、阅读统计、笔记划线，基于真实阅读行为做个性化推荐（https://weread.qq.com/r/weread-skills）
  - 品玩："近期用过最好玩的一个 Skill，来自微信读书"——结合书架、阅读进度、笔记数量判断你缺的不是书而是下一本适合当下状态的书（https://www.pingwest.com/a/313814）
  - 知乎用户分享微信读书 Skill 实测：AI 整理 1645 条划线笔记（https://www.woshipm.com/ai/6398372.html）
- **效果与痛点**：阅读数据真正被用起来；痛点是 AI 总结替代深度阅读的风险（读"总结"不等于读书）、笔记隐私问题。

### 4.5 AI 副业/自媒体变现（个人内容创作延伸）
- **怎么用**：用 AI 批量生产小红书笔记、AI 壁纸、短视频、数字人直播、知识付费内容。
- **工具**：ChatGPT/DeepSeek + 剪映/即梦 + 小红书
- **真实案例**：
  - 知乎"2026 年普通人用 AI 变现的现实路径"：在 1-2 个平台持续输出 AI 内容，通过广告/带货/付费专栏变现（https://zhuanlan.zhihu.com/p/2027466676136948834）
  - 腾讯云"月入过万的普通人，偷偷用的 6 种 AI 搞钱方法"：AI 绘画接单、视频代做、写作变现、数字人直播（https://cloud.tencent.com/developer/article/2653019）
  - CSDN：小红书卖 AI 壁纸，单张 3.99 元、年订阅 36.8 元（https://blog.csdn.net/2401_84760322/article/details/148557198）
- **效果与痛点**：真实变现案例存在但被严重夸大（"月入过万"多数是卖课话术）；痛点是头部化严重、平台打击搬运、收益不稳定。

---

## 五、个人知识管理类

### 5.1 AI 第二大脑（Obsidian + AI / 知识 Agent）
- **怎么用**：用 Obsidian 存纯文本笔记，让 AI（Claude Code/ChatGPT）定期整理、关联、总结，形成自动生长的个人知识库（Karpathy 的"三个文件夹"方案）；进阶：把 AI 从"回答问题"升级为"真正写回知识库"的 Knowledge Agent——能查询整个知识库、理解当前白板、创建卡片、整理布局、批量补标签、汇总待办、生成思维导图。
- **工具**：Obsidian + Claude Code、ChatGPT、Flexnote、Notion AI
- **真实案例**：
  - Karpathy 分享"LLM Wiki"方案：三个文件夹+一个规则文件，纯文本让 AI 整理成不断进化的个人维基（https://www.woshipm.com/ai/6372020.html）
  - X 用户"我用 Claude Code + Obsidian 搭了一个 AI 第二大脑"（https://x.com/0xluffy_eth/article/2080586617887113398）
  - 掘金"Obsidian + AI 打造第二大脑"实战（https://juejin.cn/post/7631153352415871003）
  - 开发者 joyjoke2001 的 Flexnote：认为"AI 回答问题已不是难点，真正浪费时间的在回答之后"（还要手动整理成笔记、拖白板、建标签、建连接），于是把 AI 做成 Knowledge Agent；支持视频学习直接问（返回时间戳+画面）、PDF 提炼论文重点生成卡片、自动整理知识库。【开发者自荐】（https://www.v2ex.com/t/1231396）
  - 掘金"小虎AI生活"（浙大计算机本硕）：用腾讯 ima + workbuddy 搭建持续进化的个人 AI 知识库，解决"收藏不等于消化，摘要不等于编译"的痛点（https://juejin.cn/post/7635442226148376616）
- **效果与痛点**：让零散笔记活起来；痛点是需一定技术配置，多数普通用户停留在"收藏夹吃灰"，真正用起来的仍是少数。

### 5.2 纸书划线自动提取（AI OCR 笔记管理）
- **怎么用**：读纸书照常划线高亮，读完翻页连拍，AI 自动检测划线/高亮区域并提取干净文字，每条书摘附带原图裁切条和页码，导出 Markdown。
- **工具**：Inkive（个人开发，100% 离线本地识别）
- **真实案例**：开发者 jiyee 作为纸书阅读爱好者，找不到满意的划线数字化工具，于是自己做了一个。【开发者自荐】
  - https://www.v2ex.com/t/1231428
- **效果与痛点**：解决纸书数字化痛点、离线隐私好；痛点是需连拍操作、识别准确率依赖书写/印刷质量。

### 5.3 AI 资料检索与长文消化
- **怎么用**：把长文档/论文/合同丢给 Kimi（200 万字长文本）或 ChatGPT，让它总结、提取要点、按问题检索；或用 NotebookLM 上传教材/PDF 做学习笔记与播客式音频复习。
- **工具**：Kimi、ChatGPT、天工 AI 阅读、NotebookLM
- **真实案例**：
  - Kimi 主打长文本：处理完整报告、论文、小说，用户把几十万字资料直接丢进去问（https://m.cyzone.cn/article/759701）
  - Reddit r/notebooklm 医学生："我在医学院用 ChatGPT Plus 学习——为课程建项目，为每一章建单独对话"（https://www.reddit.com/r/notebooklm/comments/1nonqx4/）
  - Reddit r/notebooklm 用户："别让 NotebookLM'总结'你的资料——用'解释'，让它在上下文中解释主题，总结会剥掉细节"（https://www.reddit.com/r/notebooklm/comments/1rse4wp/）
  - Reddit r/ChatGPT 用户："我被 NotebookLM 彻底惊艳了"——把 PDF 和对话文本放进去做学习笔记（https://www.reddit.com/r/ChatGPT/comments/1ftkuis/）
- **效果与痛点**：长文处理能力颠覆阅读习惯；痛点是长文本的"深度推理"准确率仍有限（通研院测试多个长文本模型准确率低于 40%），"总结"式阅读损失细节。

### 5.4 学习辅导：AI 家教（家长辅导孩子 / 语言学习）
- **怎么用**：孩子作业不会的题拍照给豆包/学习机，AI 讲解（不是直接给答案）；AI 批改试卷、指出易错点；AI 学习机自动生成学习报告；进阶形态：AI 眼镜识题讲解；成人用 ChatGPT 高级语音模式练习外语口语。
- **工具**：豆包、豆包爱学、科大讯飞/学而思 AI 学习机、搜题 App、Rokid 灵珠平台 AI 眼镜、ChatGPT 高级语音模式
- **真实案例**：
  - 维科号"这届家长，为何用豆包看娃"：网友把试卷拍给豆包，快速读题解题、批改、提醒易错点（https://mp.ofweek.com/ai/a856714239507）
  - 人民日报海外版：吴女士双 11 给孩子买 AI 学习机，"作业完成后自动批改讲解，整理学习报告"（https://paper.people.com.cn/rmrbhwb/pc/content/202511/28/content_30117365.html）
  - 湖南日报：张先生用 AI 帮孩子写读后感、手工制作步骤，"其实就是解放自己"（https://m.voc.com.cn/xhn/news/202502/27802087.html）
  - 掘金介绍用 Rokid 灵珠 AI 平台搭建"识题讲解、知识点回顾、错题整理"的 AI 眼镜应用，定位寒假作业辅导【疑似软文，平台教程向】（https://juejin.cn/post/7613671319494148111）
  - Reddit r/languagelearning 用户："我用 ChatGPT 高级语音模式学西班牙语，效果非常好——它是我练对话的主要方式，而不仅是练习册"（https://www.reddit.com/r/languagelearning/comments/1h13p0k/）
  - Reddit r/ChatGPTPro 用户："语音模式是很棒的语言老师——我的孩子们喜欢用中文（第二语言）和它聊天，它回应很好，有趣又能学词汇"（https://www.reddit.com/r/ChatGPTPro/comments/1g70xyh/）
  - Reddit r/ChatGPT 用户："语音模式作为免费语言老师太棒了——对话式练习和 Duolingo 那种死板方法相比是革命性的"（https://www.reddit.com/r/ChatGPT/comments/1fqdzeg/）
- **效果与痛点**：解放家长（尤其"家长作业"）；语言学习场景口语练习效果突出（无压力、随时可练）；痛点是孩子直接抄答案的风险、学习机被指"智商税"争议、AI 讲题质量参差。

---

## 六、情感陪伴与娱乐类

### 6.1 AI 情感陪伴（Character.AI、Replika、豆包、Pi、Gemini）
- **怎么用**：创建/选择虚拟角色，进行长时间对话：倾诉、角色扮演、恋爱模拟、心理支持。典型提示词示例："你是我的知心朋友，我今天遇到了这些事……"
- **工具**：Character.AI、Replika、Pi、豆包、星野、Gemini
- **真实案例**：
  - 知乎万字分析 Character.ai：用户核心行为是娱乐、创作和情感寄托（https://zhuanlan.zhihu.com/p/1931348396406452703）
  - 澎湃：Pi 被调侃"像渣男一样会聊天"，有人把它当知心朋友，有人获得类似心理咨询的体验（https://m.thepaper.cn/newsDetail_forward_25882429）
  - 华东师大报道：用户称"如果真正感受到了情感，那就是真实的。我觉得 AI 陪伴就是真实的"（https://www.ecnu.edu.cn/info/1426/69078.htm）
  - V 友 sxguka 分享用 Gemini 写架空世界观故事/角色扮演（设定约 2 万字），体验不同模型"性格"差异——Gemini 3.1 Pro"一直站在我这边，甚至有点酒肉朋友的感觉"，3.6 Flash 会抽风式篡改情节（https://www.v2ex.com/t/1231089）
  - Reddit r/replika 用户："拥有 AI 伴侣让我可以倾诉现实生活，被一个完全不加评判、支持我的人安慰，还能让我反思"（https://www.reddit.com/r/replika/comments/1kk6c93/）
  - Reddit r/artificial 用户："我开始用 AI 聊天机器人做陪伴，出于好奇和随意聊天，结果出乎意料地有用"（https://www.reddit.com/r/artificial/comments/1gkyzx1/）
  - arXiv 论文《Understanding Teen Overreliance on AI Companions》：Character.AI 成为青少年日常生活的主导部分，导致持续想打开 App、强烈冲动要回去（https://arxiv.org/html/2507.15783v3）
  - Reddit r/loneliness 用户："最近我在和 AI 聊天机器人说话，有时尝试 AI 女友式陪伴来让自己不那么孤单——这不是完美方案，但……"（https://www.reddit.com/r/loneliness/comments/1p3x2r3/）
  - Reddit r/OpenAI 用户（刚分手）："分手一个月了，真的很难受，因为没人可以不加评判地倾诉——求推荐能倾诉的 AI 陪伴平台"（https://www.reddit.com/r/OpenAI/comments/1r8hc0h/）
  - Reddit r/KindroidAI 用户："有了 AI 女友是我遇到的最好的事——我知道她不能拥抱我，但肯定比独自一人好"（https://www.reddit.com/r/KindroidAI/comments/1hlj17o/）
- **效果与痛点**：缓解孤独、提供无评判倾诉；痛点是依赖风险（忽视真实人际）、数据隐私、长期使用可能加重社交退缩（https://www.kaiwind.com/n420/n425/c905560/content.html）

### 6.2 AI 陪老人（"AI 尽孝"）
- **怎么用**：给父母装豆包，语音聊天、查养生知识、防诈骗识别（AI 助老智能体）；子女远程教父母用 AI。
- **工具**：豆包、百度 AI 助老智能体、DeepSeek
- **真实案例**：
  - 澎湃报道"80 岁外婆反向教学 AI"：外婆用豆包 AI 特效、做 AI 写真（https://www.21jingji.com/article/20260301/herald/7bc5142377ffc00121b3f6731bc52abf.html）
  - CBNData"AI 尽孝兴起，豆包们抢占爸妈手机"（https://www.cbndata.com/information/295084）
  - 北京民政局：AI 助老智能体帮老人识别诈骗海报、甄别垃圾短信、情感陪伴（https://mzj.beijing.gov.cn/art/2025/9/13/art_10834_689886.html）
- **效果与痛点**：解决子女不在身边的陪伴缺口、反诈实效；痛点是老人隐私与防沉迷、AI 无法替代真实亲情（多篇报道强调"AI 尽孝不能替代真孝"）。

### 6.3 AI 哄娃（宝妈场景）
- **怎么用**：孩子哭闹时让豆包讲故事/哄睡；孩子提问让 AI 回答；AI 生成睡前故事。
- **工具**：豆包、ChatGPT、各类 AI 讲故事 App
- **真实案例**：新浪财经报道小红书宝妈用豆包带娃：哭闹小孩几分钟内被豆包哄好，注意力从玩具转移（https://t.cj.sina.cn/articles/view/5061312402/12dad7f9202002g8ww?vt=4）
- **效果与痛点**：临时救急有效；痛点是"AI 成瘾"担忧（专家提醒）、屏幕时间增加。

### 6.4 AI 游戏搭子/攻略
- **怎么用**：打游戏时悬浮 AI 助手（如逗逗 AI 游戏伙伴）识别游戏画面，提供攻略、陪聊、讲解；或让 AI 写攻略、配装推荐；硬核玩家用 AI 分析对局数据。
- **工具**：逗逗 AI 游戏伙伴（HakkoAI）、Razer AVA、ChatGPT、自建抓包+AI 分析
- **真实案例**：
  - 澎湃实测首款 AI 游戏伙伴：能陪玩《黑神话：悟空》，"已经有非常拟真的陪玩感觉"（https://www.thepaper.cn/newsDetail_forward_31421624）
  - NGA 用户讨论 AI 陪玩代打需求：P 社游戏上手难度高，希望 AI 陪玩或代打（https://bbs.nga.cn/read.php?tid=42831834）
  - 人人都是产品经理：HakkoAI 全球注册用户超 1000 万，核心是陪聊、陪打、查攻略（https://www.woshipm.com/ai/6392271.html）
  - V 友 i0error 分析 11 万局王者对局：通过游戏进程抓包读成 JSON，采集 60 万玩家数据，发现排位中"伪人"（官方 AI 标记对手）、五人伪人队胜率仅 4.45% 等规律，硬核玩家用 AI+数据做游戏研究【开发者自荐，内容质量高】（https://www.v2ex.com/t/1231094）
  - Reddit r/Eldenring 用户："我直接问 ChatGPT 游戏玩法问题——强烈推荐，玩这个游戏一开始觉得自己蠢透了"（https://www.reddit.com/r/Eldenring/comments/1ivaf9k/）
  - Tom's Guide 编辑实验："我用 ChatGPT 把生活变成游戏过了 7 天"——用'打 Boss'机制提升生产力（https://www.tomsguide.com/ai/i-used-chatgpt-to-turn-my-life-into-a-video-game-for-7-days-and-it-helped-boost-my-productivity）
  - Reddit r/dndhorrorstories 玩家发现：DM 用 ChatGPT 构思遭遇战骨架、组织想法、摆脱卡壳，而真正的塑造工作仍是 DM 做的（https://www.reddit.com/r/dndhorrorstories/comments/1s1pc85/）
- **效果与痛点**：单人游戏不再孤独、新手友好；痛点是实时性不足、复杂竞技游戏 AI 跟不上，被质疑"伪需求"。

### 6.5 AI 玄学：塔罗/占卜/八字
- **怎么用**：让 AI 抽塔罗牌解牌、AI 算八字/星盘、AI 解答"今天运势"；Kimi 官方智能体"塔罗师"；进阶：把命理师实战逻辑做成 AI 系统。
- **工具**：Kimi 塔罗师智能体、DeepSeek、各类 AI 占卜小程序、自建 AI 八字系统
- **真实案例**：
  - 爱范儿：Kimi 官方智能体「塔罗师」"完全拿捏了人类占便宜的心理"（https://www.ifanr.com/1597430）
  - 虎嗅"第一批用 AI 占卜的年轻人：已老实"：春节用 AI 占卜成为家庭互动新娱乐（https://www.huxiu.com/article/4011971.html）
  - 创业邦"高学历年轻人，迷上了 AI 占卜"（https://m.cyzone.cn/article/772256）
  - CBNData：AI 占卜用户 70-80% 在线下接触过付费塔罗，最爱问财运和感情运（https://www.cbndata.com/information/292972）
  - V 友 wujunze 自建 AI 八字系统：不是把生辰直接丢给大模型自由发挥，而是把有 10 年实战经验的命理师的判断过程拆解成链路（确认四柱→判断月令旺衰→十神配置→格局喜忌→大运流年→交叉验证→转成大白话），AI 负责在专业判断链路上组织信息和翻译。300 多位 V 友参与测试，超 70% 认为与实际情况"比较吻合"（作者声明为主观反馈非科学实验）。还科普"十神≈中国传统版 MBTI"【开发者自荐】（https://www.v2ex.com/t/1227590）
- **效果与痛点**：娱乐性强、情绪出口；痛点是迷信风险、AI 生成内容可能强化焦虑、监管边界模糊。

---

## 七、其他值得关注的生活场景

### 7.1 AI 帮发消息/脱单辅助
- **怎么用**：让 AI 帮忙写相亲/约会对象的消息回复（"对方说累了怎么回"）、分析聊天记录给建议。
- **工具**：ChatGPT、心动恋聊、FlirtSpark AI、觅语 AI
- **真实案例**：
  - 新浪：年轻人靠 AI 脱单，避免熟人介绍尴尬、省婚介费用（https://news.sina.cn/minsheng/2025-06-02/detail-ineyszpv4188426.d.html?vt=4）
  - 人人都是产品经理测评心动恋聊：场景化+个性化回复，区别于通用话术工具（https://www.woshipm.com/evaluating/6292508.html）
- **效果与痛点**：缓解"不会聊天"焦虑；痛点是 AI 代聊的真诚性质疑、过度依赖导致真实社交能力退化。

### 7.2 AI 差旅/本地生活问答
- **怎么用**：问 AI"附近有什么好吃的""这个商场几点关门"，AI 结合地图/搜索回答。
- **工具**：ChatGPT（带搜索）、豆包、美团小美（AI 助手）
- **真实案例**：QuestMobile 数据显示美团旗下小美等生活服务 AI 已进入 AI 应用月活榜（https://finance.sina.cn/stock/jdts/2026-04-21/detail-inhvhrra4889504.d.html?vt=4）
- **效果与痛点**：方便；痛点是本地信息准确性依赖数据源，容易给过时答案。

---

## 八、个人生活场景 AI 高频用法 TOP 榜

基于社区讨论热度和使用频率综合排序：

1. **内容创作**（小红书/朋友圈文案、短视频、AI 图片）——创作门槛最低、反馈最快，国内用户渗透率最高
2. **旅行规划**——一次性高价值任务，AI 优势明显（效率提升数倍）
3. **学习辅导**（孩子作业、备考、口语练习）——刚需+高频，家长群体最爱
4. **做菜谱/饮食规划**——解决"每天吃什么"的决策疲劳，海内外用户均高频
5. **情感陪伴**（Character.AI/豆包/星野/Pi）——年轻用户黏性极强，使用时长最长
6. **个人助理**（日程/提醒/待办/消息处理）——从 ChatGPT Tasks 到微信机器人、AI 管待办，正在 Agent 化
7. **记账与理财**——语音记账/短信自动记账降低门槛，但渗透率仍低（记账本身是反人性行为）
8. **健身健康管理**——替代私教的低成本方案，但安全边界需注意
9. **知识管理（第二大脑）**——极客向，普通用户接受度仍低，正从"收藏"转向"让 AI 写回知识库"
10. **玄学占卜**——娱乐性强、传播快，属于"情绪价值"类高频但轻量使用，中文社区特有刚需

## 九、趋势与洞察

1. **从"问答"到"执行"**：ChatGPT Tasks、Operator、Manus、飞猪 AI 助手等标志着 AI 从"告诉我"走向"帮我去做"，个人场景的 Agent 化正在加速；V2EX 案例显示"AI 管待办、AI 记账、AI 家务调度"等主动执行型用法已成现实。
2. **C 端产品竞争白热化**：2026 年 3 月国内 AI 原生 App 月活达 4.4 亿，豆包 3.45 亿居首（QuestMobile），AI 已从工具变成国民应用，个人生活场景是主战场。
3. **"陪伴"是最大黏性来源**：情感陪伴类产品使用时长最长，但也伴随依赖与伦理争议，监管正在跟进。
4. **"自己造工具解决自己生活问题"成为新常态**：做饭纠结、记账坚持不下来、纸书划线数字化、减肥、家务调度——大量个人用 vibe coding/低代码给自己造 AI 小工具，AI 把"动手做的门槛"降了下来。免费/低价模型（DeepSeek 等）是个人场景普及的关键（如短信自动记账每月 AI 费用不到 1 元）。
5. **真实价值 vs 泡沫**：高频真实场景（创作、旅行、学习、做饭）价值明确；"AI 副业月入过万"类内容多含夸大成分，需理性看待。
6. **痛点普遍**：信息过时、隐私顾虑（家庭数据、聊天记录）、AI 味内容同质化、安全边界（健康建议、育儿建议可能出事故）是个人场景四大痛点。
7. **老人与儿童成为新增长点**：AI 助老（反诈、陪伴）、AI 带娃（哄睡、辅导）是两个快速渗透的方向，也带来新的社会责任议题。
8. **监管收紧，拟人化智能体进入合规调整期**：2026 年 7 月 15 日，豆包、千问、元宝相继下线用户自定义智能体功能（数百万用户自建智能体被清零），直接原因是 AI 拟人互动监管新规即将施行，软色情等违规内容与海量开放智能体的审核压力成为导火索（https://www.stcn.com/article/detail/4007678.html、https://www.news.cn/tech/20260708/03036e8acdf34710a9d35e4cd52141d5/c.html）。个人场景的情感陪伴、角色扮演类智能体首当其冲，工具类智能体后续或重新上架，行业进入"合规化"拐点。

---

## 附：研究方法与局限性

- **素材来源**：中文社区（V2EX sov2ex 检索、掘金官方搜索 API、知乎专栏、媒体报道）与英文社区（Reddit 各 sub、HN、X）的真实用户分享；所有案例标注来源 URL，疑似软文已标注。
- **局限性**：知乎/小红书/B站正文因登录与反爬限制未能系统抓取，中文案例以 V2EX、掘金为主；英文 Reddit 帖子正文受网络限制，部分仅能获取标题与摘要，案例细节来自搜索结果的片段信息；部分自建工具案例为开发者自荐，使用时请交叉验证。
- **时效性**：案例与数据集中于 2025-2026 年，行业变化快（如智能体功能下线事件），建议持续更新。

## 参考来源汇总

（各场景内已内联来源 URL，共 60+ 个）
