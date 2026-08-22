# task-0444 清理旧轮换 SSH 密码明文 — 过程笔记

## 侦察（2026-08-22）

- 目标文件与大小：
  - /root/.openclaw/workspace/scripts/sync_timing_matrix.sh（1114 B）
  - /root/.openclaw/workspace/shared/results/work/rdagent-fix-conda.sh（2859 B）
  - /root/.openclaw/evolving-claw-repo/research/work/rdagent-fix-conda.sh（2859 B）
- 两个 rdagent-fix-conda.sh `cmp` 结果：IDENTICAL（完全相同）
- `sshpass -p '...'` 出现次数：sync_timing_matrix.sh=2（第 10/12 行附近，一处 ssh、一处 scp）；每个 rdagent 文件=1（第 4 行用法注释内）
- secrets.env：存在，权限 -rw------- root:root；`grep -c '^QUANT_SSH_PASSWORD='` = 1 ✔
- sync_timing_matrix.sh 已有 `set -e`；变量区（HP/SRC/DST1/DST2）之后是两处 sshpass 调用

## 修改方案

1. sync_timing_matrix.sh：
   - 在变量区后插入密码提取块：从 /root/.openclaw/secrets.env 提取 QUANT_SSH_PASSWORD 一次（grep -m1 + cut -d= -f2-，剥离可选首尾引号），为空则报错退出（不回显值）
   - 两处 `sshpass -p '<旧明文>'` → `sshpass -p "$QUANT_SSH_PASSWORD"`
2. 两个 rdagent-fix-conda.sh 第 4 行注释：`sshpass -p '<旧明文>'` → `sshpass -p "$QUANT_SSH_PASSWORD"`（仅注释示例，不改脚本逻辑）
3. 编辑使用通用正则替换 `sshpass -p '[^']*'`，命令与输出中不出现任何密码字面值

## 执行记录

- [ ] secrets.env 值格式确认（仅长度/引号风格）
- [ ] 三文件替换
- [ ] 验证（grep 0 命中 / bash -n / 提取测试）
- [ ] 全仓附加侦察
