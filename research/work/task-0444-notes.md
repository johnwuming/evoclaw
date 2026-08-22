# task-0444 清理旧轮换 SSH 密码明文 — 过程笔记

## 侦察（2026-08-22）

- 目标文件与大小：
  - /root/.openclaw/workspace/scripts/sync_timing_matrix.sh（1114 B）
  - /root/.openclaw/workspace/shared/results/work/rdagent-fix-conda.sh（2859 B）
  - /root/.openclaw/evolving-claw-repo/research/work/rdagent-fix-conda.sh（2859 B）
- 两个 rdagent-fix-conda.sh `cmp` 结果：IDENTICAL（完全相同）
- `sshpass -p '...'` 出现次数：sync_timing_matrix.sh=2（一 ssh、一 scp）；每个 rdagent 文件=1（第 4 行用法注释内）
- secrets.env：存在，权限 -rw------- root:root；`grep -c '^QUANT_SSH_PASSWORD='` = 1 ✔
- secrets.env 值格式：裸值（无引号包裹），长度 16（仅记录长度，未读值）
- sync_timing_matrix.sh 已有 `set -e`；变量区（HP/SRC/DST1/DST2）之后是两处 sshpass 调用

## 修改内容

1. sync_timing_matrix.sh：
   - 在 DST2 变量行后插入 6 行密码提取块：`grep -m1 '^QUANT_SSH_PASSWORD=' /root/.openclaw/secrets.env | cut -d= -f2-` + 剥离可选首尾引号 + 空值守卫（缺失则 stderr 报错 exit 1，不回显值）
   - 两处 `sshpass -p '<旧明文>'` → `sshpass -p "$QUANT_SSH_PASSWORD"`
2. 两个 rdagent-fix-conda.sh 第 4 行注释：`sshpass -p '<旧明文>'` → `sshpass -p "$QUANT_SSH_PASSWORD"`（仅注释示例，脚本逻辑零改动）
- 编辑方式：python 通用正则 `sshpass -p '[^']*'` 替换（/tmp/task0444_fix.py），命令与输出全程未出现任何密码字面值
- 无关文件：未修改（改动仅 3 目标文件 + 本笔记 + /tmp 两个临时脚本，/tmp 脚本不含秘密）

## 验证结果

- 验收 grep（任务书指定模式，3 文件）：0 命中（exit=1）✔
- `bash -n`：三文件全部语法通过 ✔
- `grep -c '^QUANT_SSH_PASSWORD=' /root/.openclaw/secrets.env` = 1（≥1）✔
- 提取块功能测试（env -i 干净环境模拟 cron）：真实 secrets.env → extract-ok len=16（与裸值原长一致，引号剥离无副作用）；文件缺失 → 守卫触发（实际脚本中报错 exit 1）✔
- 修改后掩码复查：sync_timing_matrix.sh 提取块位置正确、两处调用已变量化；rdagent 两副本第 4 行均已是 `$QUANT_SSH_PASSWORD` 引用写法 ✔

## 附加侦察（只报告不修复）

任务书指定模式全仓扫描（workspace + evolving-claw-repo），除 3 个目标文件外另有 6 处命中旧明文：
1. /root/.openclaw/workspace/scripts/task-0288-t1-timing-matrix.md
2. /root/.openclaw/workspace/scripts/task-0287-c1-graycards.md
3. /root/.openclaw/workspace/scripts/task-0285-a1-factor-expansion.md
4. /root/.openclaw/workspace/scripts/task-0286-b-e2e-chart.md
5. /root/.openclaw/workspace/memory/heartbeat-archive-20260816.md
6. /root/.openclaw/workspace/tools/agent-dashboard/tasks.db（二进制数据库）

均为历史任务文档/归档/DB 记录，非可执行脚本路径；按任务书要求未改动，建议后续单独任务处理（md 可直接替换为变量引用写法；tasks.db 需评估是否含该明文后再清洗）。

## 结论

任务完成：3 文件明文清零，脚本 cron 可用性经干净环境测试保持，全部验收标准通过。
