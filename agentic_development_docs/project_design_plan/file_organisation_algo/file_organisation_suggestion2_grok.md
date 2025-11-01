# File Organization Algorithm Suggestion

## Evaluation of the Three Algorithms

All three algorithms share core similarities: they use Depth-First Search (DFS) for traversing the current folder structure, incorporate preprocessing to gather file metadata and summaries, compute cohesion scores heuristically, and leverage LLM calls with structured prompts to generate action plans (e.g., move_folder, move_file, merge_folders). This makes them practical for handling messy, real-world folder structures by prioritizing whole-folder operations for high-cohesion groups and falling back to per-file moves.

- **Algorithm 1 (Grok)**: Strong in batching subtree decisions to reduce LLM calls, emphasizing DFS with cohesion thresholds for whole-folder moves. Pros: Efficient for large directories, scalable. Cons: Relies heavily on pre-computed cohesion, which may miss nuanced cases without more LLM involvement.
- **Algorithm 2 (Grok)**: Focuses on post-order DFS and detailed LLM prompts for actions, including simulation for dry-runs. Pros: Robust conflict detection and user rules integration. Cons: Potentially more LLM calls if not batched carefully, adding complexity.
- **Algorithm 3 (ChatGPT)**: Incorporates heuristic matching before LLM, with confidence-based validation and iterative refinement. Pros: Reduces unnecessary LLM queries via heuristics; good for human-in-the-loop reviews. Cons: The second pass for merges could increase runtime for very large structures.

None is clearly "best" as they overlap significantly, but Algorithm 3 edges out due to its heuristic pre-filtering and confidence scoring, making it less LLM-dependent and more explainable. However, combining elements yields an optimum: Use Algo1's batching + Algo2's simulation/dry-run + Algo3's heuristics/confidence for a balanced, not overly complex approach.

## Algorithm 4: Agentic Approach Evaluation

An agentic approach (using a framework like Agno) is more optimum than the fixed algorithms above for real-world messiness, as it allows adaptive, iterative planning. Instead of a rigid DFS flow, the agent can dynamically query, reason, and adjust (e.g., recompute cohesion on subsets or handle unexpected duplicates). This flexibility handles edge cases better without predefined thresholds, though it may increase LLM token usage if not managed.

From Agno docs (via web search): Agno supports building agents with tools, memory, and workflows for deterministic steps. It's ideal here—use workflows for high-level orchestration (e.g., preprocess → plan → refine) and agents for tool-calling reasoning.

### Agent Planning and Tool Calls

The agent starts with the current and planned trees, then reasons step-by-step:
1. Preprocess: Call tools to build trees and compute initial cohesions.
2. Plan per subtree: Use tools to analyze subsets, propose actions via reasoning.
3. Refine: If conflicts, call resolution tools iteratively.
4. Output: Generate structured action list.

**Required Tools (to implement as Agno functions):**
- **ListTree(folder_path)**: Returns JSON tree of folder (subfolders, files with metadata).
- **ComputeCohesion(folder_path)**: Returns score (0-1) based on file summaries similarity (use embeddings or quick LLM).
- **GetFileSummary(file_path)**: Returns ai_brief_summary and metadata.
- **ProposeMapping(current_item, planned_tree)**: LLM-based tool to suggest action (move, merge, etc.) for an item.
- **DetectConflicts(proposed_actions)**: Scans actions for overlaps, returns conflicts list.
- **ResolveConflict(conflict_items)**: LLM tool to suggest merges/renames for conflicts.

**Agent Workflow (using Agno workflows):**
- Step 1: Call ListTree on current root → store as state.
- Step 2: Traverse (agent reasons over subtrees, calling ComputeCohesion and ProposeMapping in parallel for batches).
- Step 3: Call DetectConflicts → if any, loop to ResolveConflict.
- Step 4: Simulate dry-run in memory, output JSON actions with confidence/rationale.

This is more adaptive than the fixed algos, integrating seamlessly with your v1 human-in-the-loop via Agno's control plane.

## Recommended Algorithm (Combined + Agentic)

Use a hybrid: Agentic wrapper around combined Algo1-3 elements for flexibility. Implement as Agno agent with the tools above.

**Prompt for Agent (System Prompt):**
You are a file organizer agent. Given current/parsed trees, use tools to generate an action plan aligning to planned structure. Prioritize whole-folder moves for high cohesion (>0.7). Output JSON actions: [{"type": "move_folder", "source": "...", "dest": "...", "confidence": 0.9, "rationale": "..."}].

**Important Code Snippet (Python for Agno Agent Setup):**
```python
from agno import Agent, Tool

# Define tools as functions
def list_tree(folder): ...  # Implement DFS tree build
tools = [Tool(name="ListTree", func=list_tree), ...]  # Add all tools

agent = Agent(model="your-model", tools=tools)
agent.run("Organize folders: current_root=/path, planned_json=...")
```
This keeps complexity low while being powerful.
