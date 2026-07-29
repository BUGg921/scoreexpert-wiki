# PP 策略规则

本文档描述当前 DagGenerator 支持的流水并行调度规则。

## gpipe

- 所有 microbatch 先完成 forward 流水。
- forward 完成后再进入 backward 流水。
- 相邻 stage 之间通过 PP 通信节点连接。
- 同一 stage 的计算任务按 stream 顺序串行化。

## 1f1b

- 每个 stage 在满足依赖后优先执行 backward，否则执行可用的 forward。
- forward 依赖前一 stage 的 forward 完成。
- backward 依赖后一 stage 的 backward 完成。
- 最后一 stage 的 backward 只依赖本 stage 对应 forward 完成。

## 保留策略

- `dual_pipe`
- `vpp`
- `interleaved_1f1b`

这些策略尚未在生成器中完整实现，不能静默近似。
