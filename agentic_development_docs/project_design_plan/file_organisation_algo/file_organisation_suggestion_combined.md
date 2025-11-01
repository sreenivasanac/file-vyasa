# Combined Refined and Improved File Organization Algorithm Suggestion

## Basis, Incorporation, Overview, and Improvements
The primary implementation follows suggestion2_grok.md, providing a solid hybrid agentic approach with evaluation of Algorithms 1-3, a recommended combined algorithm, essential tools, workflow, prompt, and code snippet. This is optimum for real-world scenarios, balancing flexibility and simplicity.

- **Combined Algorithm Steps**: Adopt the structured 7-step flow (preprocess, heuristic matching, LLM mapping, conflict resolution, simulation, approval, execution) as it refines the workflow into clearer phases, enhancing practicality while keeping the agentic loop adaptive.
- **Additional Tools**: Integrate a subset of read-only tools like `folder_similarity` (for LLM pre-matching) and `diff_trees` (for approval previews), plus gated mutating tools like `safe_merge` and `rollback` for safety. These fit naturally into the existing toolset without overcomplicating.
- **Prompt Templates**: Use the detailed subtree mapping and conflict-resolution prompts to ensure structured LLM outputs, directly enhancing the "ProposeMapping" and "ResolveConflict" tools.
- **Agent Planning Loop**: Refine the workflow with suggestion1_codex.md's loop outline (e.g., explicit step limits, caching, validation), making the agent more robust for edge cases like large directories.

These additions improve handling of conflicts and simulations without rigidifying the dynamic agentic planning.

This design builds on suggestion3_refined.md to create a superior agentic algorithm. It enhances adaptability for real-world scenarios by adding dynamic batching (Algo1), post-order traversal (Algo2), and iterative refinement (Algo3), allowing the agent to handle complex nests, reduce calls, and resolve issues iteratively without added complexity.

## Agentic Approach Rationale
The dynamic agentic planning with tool calls is more optimum than fixed Algo1-3, enabling the agent to choose operations flexibly (e.g., batch only when efficient, iterate on ambiguities), improving robustness for messy structures.

## Refined Agentic Design and Implementation

### Agent Planning and Tool Calls
The agent reasons iteratively, using tools in any order based on context (e.g., start with preprocessing, then heuristic matching if obvious, fall back to LLM for ambiguity). Planning is guided by a system prompt encouraging read-only tools first, with memory for state (e.g., storing trees/actions). Tool calls can be parallel for batches (e.g., cohesion on multiple subtrees).

Agent uses state/memory to reason step-by-step, selecting tools dynamically (e.g., "For deep tree, use post-order; batch if >10 items"). New behaviors: Adaptive batching for efficiency, bottom-up processing for nests, looped refinement for low-confidence cases.

**Refined Tools (Integrated from Both Suggestions):**
- **ListTree(folder_path)**: Returns JSON tree (subfolders, files with metadata).
- **ComputeCohesion(folder_path)**: Returns score (0-1) based on file summaries similarity.
- **GetFileSummary(file_path)**: Returns ai_brief_summary and metadata.
- **ProposeMapping(current_item, planned_tree)**: LLM-based suggestion for action (move, merge, etc.).
- **DetectConflicts(proposed_actions)**: Scans for overlaps, returns conflicts list.
- **ResolveConflict(conflict_items)**: LLM suggestion for merges/renames.
- **FolderSimilarity(curr_path, planned_path, file_details?)**: LLM-based computation of similarity score (0-1) based on names, contents, types. Returns JSON with score and rationale.
- **SimulatePlan(actions)**: Dry-run simulation with metrics.
- **DiffTrees(before, after)**: Generates diff for approval.
- **SafeMove(src, dest)** / **SafeMerge(srcs, dest)** / **Rollback(map)**: Gated mutating tools for execution.
- **FileMetadata(paths)**: Batch fetches types/sizes/hashes for duplicates/conflicts - useful for real-world dup handling.
- **EmbedLabels(paths)**: Assigns cluster labels via embeddings - optional for better cohesion if not pre-computed.
- **PostOrderTraverse(tree)**: Bottom-up tree processing (from Algo2).
- **IterativeRefine(unresolved_items, planned_tree)**: Loops refinement (from Algo3, max 3 iterations).
 - **IncorporateUserRules(rules_text, current_state)**: Takes user-provided rules/prompts (e.g., "keep invoices under Finance") and the agent's current state (e.g., proposed actions/tree). Uses an LLM call to refine mappings by injecting rules into decisions; outputs updated JSON actions with a "rule_applied" flag and brief rationale. Use after ProposeMapping and before DetectConflicts when rules exist.

**Agent Workflow (Integrated Refined Agno-style Loop):**
- Step 1: ListTree + FileMetadata + GetFileSummary → store state.
- Step 2: PostOrderTraverse; for subtrees/nodes, call FolderSimilarity (LLM-based) and ComputeCohesion; if high score (>=0.8), auto-map; ProposeMapping in parallel batches.
- Step 2.5: If user rules exist, call IncorporateUserRules to inject them into proposed actions; set rule_applied on affected items with concise rationale; then proceed to Step 3.
- Step 3: DetectConflicts → if any, ResolveConflict loop (max 3 iterations) or IterativeRefine if needed.
- Step 4: SimulatePlan + DiffTrees → if metrics low, refine; output JSON actions.
- Step 5: Await approval, then SafeMove/SafeMerge; log for Rollback.

High-level Implementation: Use Agno with tools as functions; agent runs with instructions to prioritize read-only, validate JSON, and gate mutations.

**System Prompt for Agent (Integrated):**
You are a file organizer agent. Use read-only tools first to build/analyze trees. Dynamically choose tools (e.g., batch for efficiency, iterate refinements). Generate action plan aligning current to planned structure, prioritizing whole-folder moves for high cohesion (>0.7). Call mutating tools only post-approval. Output strict JSON actions: [{"type": "move_folder", "source": "...", "dest": "...", "confidence": 0.9, "rationale": "..."}].
 Honor user-provided organization rules; apply them after ProposeMapping and mark rule_applied=true when a rule changes an action.

**Subtree Mapping Prompt (from codex):**
System: Map CURRENT subtree into PLANNED safely. Prefer whole-folder moves if ≥70% alignment. Output strict JSON actions.

**Conflict Resolution Prompt (from codex):**
System: Resolve conflicts with minimal changes. Output updated JSON actions.

**FolderSimilarity Prompt:**
System: Compute similarity between folders based on names, contents (summaries), types, and metadata. Prefer thematic overlaps. Output JSON: {'score': float (0-1), 'rationale': str}.

**IncorporateUserRules Prompt:**
System: Refine these actions [{actions}] using user rules: {rules_text}. Prioritize rules over heuristics; update or override actions as needed. Output strict JSON actions with fields: type, source, dest, confidence, rationale, rule_applied (boolean).

**Code Snippet (Python for Agno Setup, Integrated and Refined):**
```python
from agno import Agent, Tool

# Define tools (implement as needed)
def list_tree(folder): ...  # DFS tree build
def folder_similarity(curr, planned, details=None): ...  # LLM-based score with prompt
def post_order_traverse(tree): ...  # Bottom-up
def iterative_refine(items, planned): ...  # Loop
def incorporate_user_rules(rules_text, current_state): ...  # Inject rules; return updated actions with rule_applied flags
# ... other tools

tools = [Tool(name="ListTree", func=list_tree), Tool(name="FolderSimilarity", func=folder_similarity), Tool(name="PostOrderTraverse", func=post_order_traverse), Tool(name="IterativeRefine", func=iterative_refine), Tool(name="IncorporateUserRules", func=incorporate_user_rules), ...]

agent = Agent(model="your-model", tools=tools, instructions="Prioritize read-only; validate outputs; gate mutations. Adaptively plan: batch, traverse post-order, refine iteratively.")
agent.run("Organize: current_root=/path, planned_json=...")
```

This combined design maintains simplicity while incorporating codex elements, LLM-based FolderSimilarity for improved accuracy in semantic matching, safety, and iteration, and empowers the agent with new adaptive capabilities for real-world scenarios.
