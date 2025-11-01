# Improved Agentic File Organization Algorithm

## Overview and Improvements
This design builds on suggestion3_refined.md, incorporating elements from Algorithms 1-3 to create a superior agentic algorithm. It enhances adaptability for real-world scenarios by adding dynamic batching (Algo1), post-order traversal (Algo2), and iterative refinement (Algo3), allowing the agent to handle complex nests, reduce calls, and resolve issues iteratively without added complexity.

## Agentic Approach Rationale
The dynamic agentic planning with tool calls is more optimum than fixed Algo1-3, enabling the agent to choose operations flexibly (e.g., batch only when efficient, iterate on ambiguities), improving robustness for messy structures.

## Agentic Design and Implementation

### Agent Planning and Tool Calls
Agent uses state/memory to reason step-by-step, selecting tools dynamically (e.g., "For deep tree, use post-order; batch if >10 items"). New behaviors: Adaptive batching for efficiency, bottom-up processing for nests, looped refinement for low-confidence cases.

**Tools:**
- **ListTree(folder_path)**: JSON tree.
- **ComputeCohesion(folder_path)**: Cohesion score.
- **GetFileSummary(file_path)**: Summary/metadata.
- **ProposeMapping(current_item, planned_tree)**: LLM action suggestion.
- **DetectConflicts(proposed_actions)**: Conflict list.
- **ResolveConflict(conflict_items)**: LLM merges/renames.
- **FolderSimilarity(curr_path, planned_path, file_details?)**: LLM similarity score.
- **SimulatePlan(actions)**: Dry-run with metrics.
- **DiffTrees(before, after)**: Diff for approval.
- **SafeMove(src, dest)** / **SafeMerge(srcs, dest)** / **Rollback(map)**: Gated execution.
- **FileMetadata(paths)**: Batch metadata.
- **EmbedLabels(paths)**: Cluster labels.
- **BatchSubtrees(subtrees, planned_tree)**: Batches subtrees for LLM mapping (from Algo1).
- **PostOrderTraverse(tree)**: Bottom-up tree processing (from Algo2).
- **IterativeRefine(unresolved_items, planned_tree)**: Loops refinement (from Algo3, max 3 iterations).

**Agent Workflow:**
- Step 1: ListTree + FileMetadata + GetFileSummary → state.
- Step 2: PostOrderTraverse; for nodes, FolderSimilarity/ComputeCohesion → auto-map if high; else BatchSubtrees + ProposeMapping.
- Step 3: DetectConflicts → ResolveConflict or IterativeRefine if needed.
- Step 4: SimulatePlan + DiffTrees → refine if metrics low.
- Step 5: Approve, then SafeMove/SafeMerge; log Rollback.

**System Prompt:**
You are a file organizer agent. Dynamically choose tools (e.g., batch for efficiency, iterate refinements). Prioritize whole-folder moves for high cohesion. Output JSON actions.

**Code Snippet (Agno Setup):**
```python
from agno import Agent, Tool

# Define tools
def batch_subtrees(subtrees, planned): ...  # Batch LLM call
def post_order_traverse(tree): ...  # Bottom-up
def iterative_refine(items, planned): ...  # Loop

tools = [Tool(name="BatchSubtrees", func=batch_subtrees), ...]  # All tools

agent = Agent(model="your-model", tools=tools, instructions="Adaptively plan: batch, traverse post-order, refine iteratively.")
agent.run("Organize: current_root=/path, planned_json=...")
```
This empowers the agent with new adaptive capabilities while keeping it simple.
