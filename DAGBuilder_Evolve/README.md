# DAGBuilder_Evolve

该项目在不复制核心实现的前提下，复用同级 `DAGBuilder_LLM` 的 DAG 生成、规则检查与
`ValueSim/simulator_v2`，用真实性能仿真驱动并行策略 program 演化。旧 SearchRunner
及旧 ValueSim 入口不会被调用或修改。

## 搜索对象

默认场景是 7B、32 卡，搜索 `PP、TP、DP、micro_batch_num、GPipe/1F1B、
AllReduce/RS+AG`。EP、CP、VPP 和 Rank 放置固定。默认结构空间含 873 个去重策略；
显存估计不通过的策略会保留在目录中并标为不可提名。

Rank 按 PP-major 放置：

```text
global_rank = ((pp_stage × DP) + dp_rank) × TP + tp_rank
```

TP Rank 连续且优先位于同一 Server，只使用前 `active_gpus` 张物理卡。

## 运行

在本目录执行：

```powershell
$env:PYTHONPATH = $PWD
python -m dagbuilder_evolve `
  --scenario configs\scenario_7b_32g.py `
  --run-name 7b_mock_2round `
  --rounds 2 --mock
```

正式 10 轮使用 DeepSeek。验收配置使用响应更快的 `deepseek-v4-flash`：

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
python -m dagbuilder_evolve `
  --scenario configs\scenario_7b_32g_flash.py `
  --run-name 7b_deepseek_flash_10round
```

`scenario_7b_32g.py` 保留 `deepseek-v4-pro` 配置，适合允许更长模型响应时间的运行。
没有密钥时正式模式会立即停止。密钥不会进入配置、checkpoint 或报告。使用
`--resume outputs\<run>\checkpoint_latest.json` 可按保存的随机状态继续。

## 评估和保留规则

每个 program 对全部显存可行策略给启发式分，但不能访问文件、网络或仿真器。每个
island 每轮最多提交 8 个尚未仿真的候选；候选经过 DAG 生成、RuleCheck 和纯数值
simulator_v2 后，按最长路径时延排名。缓存保证相同场景与策略只仿真一次。

四个 island 分别关注显存安全、拓扑亲和、流水线效率和综合平衡。每岛最多保留 20
个 program；MAP-Elites 使用 AST 复杂度和 Top-8 提名差异分格。第 5、10 轮进行环形
迁移。当前最优仅表示“已实际仿真候选中的最小时延”，报告会同时给出空间覆盖率。

## 输出

每轮目录包含 program、island 排名、MAP-Elites 网格、迁移和 checkpoint。最终输出
`final_report.json`、`convergence.json`、`program_database.json`、最佳 DAG/weighted
DAG/关键路径，以及：

- `best_score_program.py`：实际提名或关联最终最优策略的完整打分公式；
- `score_program_evidence.json`：公式的 program、island、代数、候选 score 和完整排名；
- `deployment_experience.json/md`：最优部署策略，以及分别来自打分公式和数值仿真的推理；
- `scenario_analysis.md`：按 Wiki `raw/articles` 风格自动生成“实验场景、最优解、打分策略代码、经验总结”四段主体；经验总结内分离并行策略、原因和结论边界，主体后固定追加“未仿真的场景”和“下一步仿真建议”。覆盖差集从正式 Wiki 的目标总览及其 raw 场景链接读取，并与本轮结果合并；不采用用户口头清单，也不把仅存在的配置文件算作已仿真。

最终策略按数值仿真的最长路径选择，score 只负责解释候选为何进入仿真。部署经验中的
策略、公式归因和数值证据均由确定性模板生成，语言模型不得修改这些结构化事实。

直接运行 Evolve 时保留上述结构化产物；通过 `scoreexpert-scenario-analysis` 流水线运行时，
流水线会先用完整产物完成一致性校验，再删除支持文件，最终每个成功运行目录只保留
自包含的 `scenario_analysis.md`。只有调试时显式使用 `--keep-candidates` 才保留完整产物。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试覆盖 873 个候选、Rank/通信域、program 沙箱、缓存、单策略纯数值评估，以及两轮
Mock 演化和 checkpoint 输出。
