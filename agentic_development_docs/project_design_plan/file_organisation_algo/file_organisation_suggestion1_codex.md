# FileVyasa — Agentic File‑Organisation Algorithm (Codex Suggestion 1)

## Executive summary
- Goal: transform a messy current tree into a planned tree using a practical, safe, and not‑too‑complex agentic approach that works across real‑world scenarios.
- Verdict on Algorithms 1–3:
  - Algo1 (DFS + LLM batching): scalable traversal, preserves whole‑folder moves; needs explicit conflict handling and thresholds.
  - Algo2 (heuristic matching first): cheap and effective for obvious matches; needs tie‑break/semantic fallback.
  - Algo3 (strict JSON + dry‑run + HITL): reliable outputs, reviewable plan, enables rollback; needs a conflict/merge pass.
- Best path: combine them. Add an agentic planning loop (Algorithm 4) that uses deterministic tools first, LLM only where ambiguous, simulates the plan, then executes only after approval.

---

## Combined algorithm A* (simple, robust)

Inputs
- current_tree: scanned directory tree with files/folders
- planned_tree: LLM‑proposed target structure (from Folder Structure Planning Module)
- file_details: {path, type, size, mtime, summaries, cluster_label, hash}
- user_rules: optional policy hints (e.g., “Invoices under Finance/Invoices”)

Step 1 — Preprocess (read‑only)
- list_tree(root) → tree; file_metadata(paths) → types/sizes/mtimes/hashes.
- summarize_files(paths) → brief, summary (token‑bounded). Optionally reuse cached summaries.
- cohesion_score(folder) → [0..1] from distribution of cluster labels/types.

Step 2 — Heuristic candidate matching (non‑LLM)
- For each current folder c and planned folder p compute:
  - score(c,p) = w1·name_sim + w2·content_sim + w3·type_overlap + w4·path_prior
  - name_sim: normalized edit/jaro similarity; content_sim: label/embedding overlap; type_overlap: Jaccard of file type sets.
- If max score ≥ τ1 (default 0.80) and cohesion ≥ 0.70 → candidate move‑as‑unit; else mark ambiguous.

Step 3 — LLM subtree mapping (batched)
- Batch ambiguous subtrees (≤50 items each). Provide: subtree JSON, planned_tree, file_details (abridged), heuristic_candidates, user_rules.
- Model returns strict JSON actions per item: move_folder | merge_folders | move_file | rename_file | rename_folder | create_subfolder | leave_in_place with confidence [0..100] and a short rationale.
- Prefer whole‑folder moves if ≥70% files align to one planned folder; otherwise break apart.

Step 4 — Consolidate + resolve conflicts
- Merge all actions; detect collisions (same dest/name), duplicate files by hash, parallel moves to same target.
- Run a focused LLM conflict prompt with only conflicting items to suggest merges/renames/nesting with minimal change.

Step 5 — Simulate (dry‑run) and score
- simulate_plan(actions) → after_tree, conflicts, metrics {cohesion, collisions, depth/width balance}.
- If metrics below τ2 (default 0.70) or conflicts remain → refine: re‑prompt only the problematic subtrees.

Step 6 — Human approval (HITL)
- Show before/after diff, actions, confidences. Allow edits/overrides.

Step 7 — Gated execution and verification
- Execute only approved actions; log rollback map; verify filesystem reflects plan; surface any residual stragglers.

Real‑world cases handled
- Mixed‑topic folders (scatter files), near‑duplicate names (Photos/Images), duplicates by content hash, deep nesting, partial overlaps, date/type‑driven groupings.

---

## Prompt templates (JSON‑only)

Subtree mapping prompt
```
System: You are an expert file organizer. Map CURRENT subtree into PLANNED structure safely.
Rules:
- Prefer whole‑folder moves when ≥70% of files align to one planned folder.
- Break low‑cohesion folders; suggest merges where themes overlap; no deletions.
- Only output strict JSON matching the schema; no prose.

User JSON:
{
  "current_subtree": <JSON subtree with cohesion and up to 50 items>,
  "planned_tree": <JSON planned tree>,
  "file_details": [{path, brief, summary, type, size, created, cluster_label}],
  "heuristic_candidates": [{current_path, suggested_planned_path, score}],
  "user_rules": ["..."]
}

Response schema:
{
  "actions": [
    {"type": "move_folder|merge_folders|move_file|rename_file|rename_folder|create_subfolder|leave_in_place",
     "source": "<path or [paths]>", "dest": "<path>", "new_name": "<optional>",
     "confidence": <0-100>, "rationale": "<≤2 sentences>"}
  ],
  "unresolved_items": ["<paths>"]
}
```

Conflict‑resolution prompt
```
System: Resolve destination conflicts and filename collisions with minimal changes.
User JSON:
{
  "conflicting_actions": [...],
  "file_clues": [{path, brief, type, cluster_label}],
  "user_rules": ["..."]
}
Return updated actions in the same schema, replacing conflicted ones.
```

---

## Agent tool catalog (IO schemas)

Read‑only tools
- list_tree(root: str, depth?: int=6) → {tree}
- file_metadata(paths: [str]) → [{path, size, mtime, type, hash}]
- summarize_files(paths: [str], budget_tokens?: int=256) → [{path, brief, summary}]
- embed_labels(paths: [str]) → [{path, cluster_label, embedding_id?}]
- cohesion_score(path: str) → {path, score: float, sample: int}
- folder_similarity(curr_path: str, planned_path: str) → {name_sim: float, content_sim: float, type_overlap: float, score: float}
- simulate_plan(actions: [Action]) → {after_tree, conflicts: [...], metrics: {cohesion, collisions, balance}}
- diff_trees(before_tree, after_tree) → {added, moved, renamed, unchanged}
- detect_conflicts(actions) → {collisions: [...], duplicates: [...], filename_clashes: [...]}

Mutating (gated) tools
- safe_move(src: str, dest: str) → {ok: bool, reason?}
- safe_merge(srcs: [str], dest: str) → {ok: bool, details?}
- make_dir(path: str) → {ok: bool}
- rollback(map: [{from, to}]) → {ok: bool}

Notes
- Keep tools idempotent; return machine‑parseable JSON only.
- Strictly separate read‑only from mutating; execution gated by an `approved_plan` flag.

---

## Agent planning loop (Agno‑style design)

Policies
- step_limit: 40; read_only_tool_limit: 30; mutating_tool_limit: gated by approval.
- Cache scans/summaries/embeddings; checksum inputs to avoid recompute.
- Validate all LLM outputs against the JSON schema; refuse execution on invalid data.

Loop outline
1) list_tree + file_metadata + summarize_files + cohesion_score.
2) folder_similarity to produce heuristic candidates.
3) For ambiguous subtrees, call Subtree Mapping Prompt; collect actions.
4) detect_conflicts; if any, use Conflict‑resolution Prompt.
5) simulate_plan; if metrics < τ2 or conflicts remain, refine problematic batches.
6) Present diff for HITL; await `approved_plan=true`.
7) Execute safe_move/safe_merge/make_dir; record rollback map.

---

## Minimal code outline (Python/Agno)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

# ---- Tool stubs (implement with your local FS and caches) ----
@tool
def list_tree(root: str, depth: int = 6):
    """Return directory tree JSON (read-only)."""
    ...

@tool
def file_metadata(paths: list[str]):
    ...

@tool
def summarize_files(paths: list[str], budget_tokens: int = 256):
    ...

@tool
def cohesion_score(path: str):
    ...

@tool
def folder_similarity(curr_path: str, planned_path: str):
    ...

@tool
def detect_conflicts(actions: list[dict]):
    ...

@tool
def simulate_plan(actions: list[dict]):
    ...

@tool
def safe_move(src: str, dest: str):
    ...

@tool
def safe_merge(srcs: list[str], dest: str):
    ...

# ---- Agent ----
organizer = Agent(
    id="file-organizer",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        list_tree, file_metadata, summarize_files, cohesion_score,
        folder_similarity, detect_conflicts, simulate_plan,
        safe_move, safe_merge,
    ],
    instructions=(
        "Plan using read-only tools first; output strict JSON per schemas. "
        "Only call mutating tools if dependencies.approved_plan is true."
    ),
    markdown=True,
)

# Pseudocode run:
# 1) gather context → 2) heuristics → 3) LLM mapping → 4) conflicts → 5) simulate → 6) approve → 7) execute.
```

---

## Why agentic (Algorithm 4) is superior here
- Deterministic tools keep costs low and results reproducible; LLM only for ambiguity.
- Batching + strict schemas yield reliable, auditable actions.
- Simulation + HITL ensure safety before any file operation.
- Simple thresholds (τ1≈0.80, τ2≈0.70) and batch size (≤50) keep the method effective yet not complex.

