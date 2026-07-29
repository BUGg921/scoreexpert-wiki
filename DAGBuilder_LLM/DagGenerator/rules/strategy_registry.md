# 策略注册表

本文件记录 config 中策略名与规则文档章节的对应关系。

## PP 策略

- `gpipe`：见 `pp_strategies.md` 中的 GPipe 章节。
- `1f1b`：见 `pp_strategies.md` 中的 1F1B 章节。

## DP 策略

- `naive_allreduce_after_backward`：见 `dp_strategies.md` 中的 naive allreduce 章节。

## 保留策略

以下策略当前只保留名称，生成器尚未完整实现：

- `dual_pipe`
- `vpp`
- `interleaved_1f1b`
- `zero_01`

如果要启用保留策略，需要同步更新规则文档、生成器实现和 RuleCheck。
