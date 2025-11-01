# Refined File Organization Algorithm Suggestion

## Basis and Incorporation from suggestion1_codex.md

The primary implementation will follow suggestion2_grok.md, which provides a solid hybrid agentic approach with evaluation of Algorithms 1-3, a recommended combined algorithm, essential tools, workflow, prompt, and code snippet. This is already optimum for real-world scenarios, balancing flexibility and simplicity.

From suggestion1_codex.md, we can incorporate the following without adding complexity:
- **Combined Algorithm Steps**: Adopt the structured 7-step flow (preprocess, heuristic matching, LLM mapping, conflict resolution, simulation, approval, execution) as it refines the workflow in suggestion2_grok.md into clearer phases, enhancing practicality while keeping the agentic loop adaptive.
- **Additional Tools**: Integrate a subset of read-only tools like `folder_similarity` (for LLM pre-matching) and `diff_trees` (for approval previews), plus gated mutating tools like `safe_merge` and `rollback` for safety. These fit naturally into the existing toolset without overcomplicating.
- **Prompt Templates**: Use the detailed subtree mapping and conflict-resolution prompts to ensure structured LLM outputs, directly enhancing the "ProposeMapping" and "ResolveConflict" tools.
- **Agent Planning Loop**: Refine the workflow with suggestion1_codex.md's loop outline (e.g., explicit step limits, caching, validation), making the agent more robust for edge cases like large directories.

These additions improve handling of conflicts and simulations without rigidifying the dynamic agentic planning.

## Refined Agentic Design and Implementation

### Agent Planning and Tool Calls

The agent reasons iteratively, using tools in any order based on context (e.g., start with preprocessing, then heuristic matching if obvious, fall back to LLM for ambiguity). Planning is guided by a system prompt encouraging read-only tools first, with memory for state (e.g., storing trees/actions). Tool calls can be parallel for batches (e.g., cohesion on multiple subtrees).

**Refined Tools (building on suggestion2_grok.md, incorporating from codex):**
- **ListTree(folder_path)**: Returns JSON tree (subfolders, files with metadata).
- **ComputeCohesion(folder_path)**: Returns score (0-1) based on file summaries similarity.
- **GetFileSummary(file_path)**: Returns ai_brief_summary and metadata.
- **ProposeMapping(current_item, planned_tree)**: LLM-based suggestion for action (move, merge, etc.).
- **DetectConflicts(proposed_actions)**: Scans for overlaps, returns conflicts list.
- **ResolveConflict(conflict_items)**: LLM suggestion for merges/renames.
- **FolderSimilarity(curr_path, planned_path, file_details?)**: LLM-based computation of similarity score (0-1) based on names, contents, types. Returns JSON with score and rationale. *Refined to LLM for accuracy; adds semantic pre-filtering.*
- **SimulatePlan(actions)**: Dry-run simulation with metrics. *New, from codex - enhances refinement.*
- **DiffTrees(before, after)**: Generates diff for approval. *New, from codex - aids HITL.*
- **SafeMove(src, dest)** / **SafeMerge(srcs, dest)** / **Rollback(map)**: Gated mutating tools for execution. *New, from codex - ensures safety.*

**Additional Suggested Tools (to enhance without complexity):**
- **FileMetadata(paths)**: Batch fetches types/sizes/hashes for duplicates/conflicts - useful for real-world dup handling.
- **EmbedLabels(paths)**: Assigns cluster labels via embeddings - optional for better cohesion if not pre-computed.

**Agent Workflow (refined Agno-style loop):**
- Step 1: ListTree + FileMetadata + GetFileSummary → store state.
- Step 2: For subtrees, call FolderSimilarity (LLM-based) and ComputeCohesion; if high score (>=0.8), auto-map; else ProposeMapping in parallel batches.
- Step 3: DetectConflicts → if any, ResolveConflict loop (max 3 iterations).
- Step 4: SimulatePlan + DiffTrees → if metrics low, refine; output JSON actions.
- Step 5: Await approval, then SafeMove/SafeMerge; log for Rollback.

High-level Implementation: Use Agno with tools as functions; agent runs with instructions to prioritize read-only, validate JSON, and gate mutations.

**System Prompt for Agent:**
You are a file organizer agent. Use read-only tools first to build/analyze trees. Generate action plan aligning current to planned structure, prioritizing whole-folder moves for high cohesion (>0.7). Call mutating tools only post-approval. Output strict JSON actions: [{"type": "move_folder", "source": "...", "dest": "...", "confidence": 0.9, "rationale": "..."}].

**Subtree Mapping Prompt (from codex):**
System: Map CURRENT subtree into PLANNED safely. Prefer whole-folder moves if ≥70% alignment. Output strict JSON actions.

**Conflict Resolution Prompt (from codex):**
System: Resolve conflicts with minimal changes. Output updated JSON actions.

**Code Snippet (Python for Agno Setup, refined):**
```python
from agno import Agent, Tool

# Define tools (implement as needed)
def list_tree(folder): ...  # DFS tree build
def folder_similarity(curr, planned, details=None): ...  # LLM-based score with prompt
# ... other tools

tools = [Tool(name="ListTree", func=list_tree), Tool(name="FolderSimilarity", func=folder_similarity), ...]

agent = Agent(model="your-model", tools=tools, instructions="Prioritize read-only; validate outputs; gate mutations.")
agent.run("Organize: current_root=/path, planned_json=...")
```

This refined design maintains simplicity while incorporating codex elements and LLM-based FolderSimilarity for improved accuracy in semantic matching, safety, and iteration.

**FolderSimilarity Prompt:**
System: Compute similarity between folders based on names, contents (summaries), types, and metadata. Prefer thematic overlaps. Output JSON: {'score': float (0-1), 'rationale': str}.
