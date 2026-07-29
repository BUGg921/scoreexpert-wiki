# DP Strategy Rules

## naive_allreduce_after_backward

- Each PP stage triggers one stage-level DP AllReduce after all backward tasks for that stage complete.
- The DP AllReduce node is placed on the shared `DP Comm` row.
- The AllReduce node must be reachable from every backward node in the same PP stage across all DP ranks.

## reduce_scatter_allgather_after_backward

- Each PP stage triggers one stage-level DP ReduceScatter after all backward tasks for that stage complete.
- A matching DP AllGather node must follow the ReduceScatter node for the same PP stage.
- Both nodes are placed on the shared `DP Comm` row.
- The ReduceScatter node must be reachable from every backward node in the same PP stage across all DP ranks.
- The AllGather node must be reachable from the matching ReduceScatter node.

## zero_01

Reserved for future optimizer-state and parameter-sharding flows.
