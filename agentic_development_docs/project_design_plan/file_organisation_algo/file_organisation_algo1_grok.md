Algorithm Design for Aligning Current Folder Structure to Planned Structure
To bridge the gap between the current messy folder structure and the LLM-proposed planned folder structure (generated from the Folder Structure Planning Module), we need a practical, iterative algorithm that minimizes filesystem disruptions, respects whole-folder cohesion where possible, and leverages LLM for nuanced decisions while keeping operations safe and reviewable. The goal is to generate a detailed action plan (e.g., moves, renames, merges) that can be previewed and approved by the user before execution.
This algorithm should handle real-world messiness like inconsistent naming, nested subfolders with mixed content, duplicates across paths, and partial overlaps between current and planned structures. It prioritizes:

Whole-folder operations first (e.g., moving intact folders) to preserve existing organization.
Per-file adjustments only when necessary (e.g., scattering files from a low-cohesion folder).
Conflict detection (e.g., merging folders with similar names/themes).
Safety: All decisions are simulated in a dry-run, with no actual changes until user approval.

The algorithm uses a hybrid tree-traversal approach combining Depth-First Search (DFS) for exploring the current structure with LLM-guided decision-making at key nodes. DFS is chosen because it naturally handles nested folders by processing subtrees recursively, allowing decisions on entire subfolders before individual files. This reduces LLM calls (batching decisions per subtree) and scales to large directories (e.g., 5k+ files) by limiting context size per call.
High-Level Algorithm Steps

Preparation Phase:

Represent the current folder structure as a tree (e.g., a nested dictionary or JSON-like object with paths, subfolders, and files including their names, summaries, and metadata like type, size, creation date).
Obtain the planned folder structure from the prior LLM call (as a similar tree representation, e.g., proposed root with subfolders and suggested file groupings based on clusters).
For each file in the current tree, attach pre-extracted data: filename, ai_brief_summary (2 lines), ai_summary (4 lines), metadata, and cluster label (from Constella).
Compute a quick heuristic "cohesion score" for each current subfolder (non-LLM): e.g., average similarity of file cluster labels within the folder (using simple Jaccard on tags or pre-computed embeddings). Threshold: >0.7 suggests treating as a "unit" initially.


Traversal and Decision Phase (DFS with LLM Batching):

Start DFS from the root of the current tree.
At each folder node (including root):

If the folder has high cohesion (>threshold), propose it as a candidate for whole-folder move/merge.
Batch the subtree's details (subfolders + files) and pass to LLM for decisions.
LLM outputs a structured plan for that subtree, mapping current items to planned paths.


Recurse into subfolders only if the LLM decides to break them apart (e.g., low cohesion or no direct match).
For leaf nodes (files), defer to subtree batch unless isolated.
Limit batch size: If a subtree exceeds ~50 items, split into child batches and aggregate decisions bottom-up.
After full traversal, consolidate all subtree plans into a global action list, resolving conflicts (e.g., duplicate destinations via renaming suggestions).


Conflict Resolution Phase:

Scan the consolidated plan for overlaps (e.g., two folders mapping to the same planned path).
If conflicts, make a targeted LLM call with just the conflicting items to suggest resolutions (e.g., merge, rename, or nest one inside the other).


Output and Integration:

Generate a flat list of actions: e.g., [{"type": "move_folder", "source": "/current/path", "dest": "/planned/path"}, {"type": "move_file", "source": "/file.txt", "dest": "/planned/subfolder/file.txt"}, {"type": "rename_file", "source": "/oldname.txt", "new_name": "newname.txt"}, {"type": "merge_folders", "sources": ["/folderA", "/folderB"], "dest": "/combined"}].
Each action includes a confidence score (from LLM) and rationale snippet.
Feed this into the Approval State Manager for user review, with previews (e.g., before/after tree diffs).



This approach is practical for messy systems because:

DFS minimizes redundant traversals and handles nesting intuitively.
Batching reduces LLM calls (e.g., 5-10 per large dir vs. one per file).
LLM handles ambiguity (e.g., thematic merges) where heuristics fail.
Scales: For very large dirs, add parallelism by processing independent subtrees concurrently.

LLM Call Design for Subtree Decisions
For each batched subtree during DFS, make one LLM call with a structured prompt. Use a model like Grok or OpenAI (via BYOK) that supports JSON-structured outputs for reliability.


Prompt Template:
You are an expert file organizer. Given the current subtree of a messy folder structure, the target planned folder structure, and details about files (names, summaries, metadata), generate a precise action plan to align the current to the planned structure.

Key rules:
- Prioritize moving entire folders if they match a planned subfolder thematically (based on file summaries/cluster labels).
- For low-cohesion folders (score <0.7), suggest breaking into per-file moves.
- Suggest merging if multiple current folders/files align to the same planned path (e.g., similar themes).
- Suggest renames only if needed for consistency or conflicts.
- Apply user rules: [INSERT USER-PROVIDED RULES/PROMPTS HERE, e.g., "Keep invoices under Finance"].
- No deletions; only move, rename, or merge.
- Output actions with confidence (0-100%) and brief rationale.
- If no good match, suggest leaving in place or creating a new subfolder under planned root.

Current Subtree:
[INSERT JSON-LIKE REPRESENTATION OF SUBTREE, e.g.,
{
  "path": "/messy_documents/subfolderX",
  "cohesion_score": 0.8,
  "subfolders": [
    {"path": "/subfolderX/childY", "files": [...], ...}
  ],
  "files": [
    {"name": "budget_2023.xlsx", "ai_brief_summary": "2023 annual budget spreadsheet with expenses.", "ai_summary": "Details income, outflows for Q1-Q4; authored by user.", "metadata": {"type": "xlsx", "created": "2023-05-15"}, "cluster_label": "financial"}
    // ... up to ~50 items
  ]
}
]

Planned Folder Structure:
[INSERT FULL PLANNED TREE AS JSON, e.g.,
{
  "root": "/organized_documents",
  "subfolders": [
    {"name": "Financial", "suggested_contents": "Budgets, invoices (cluster: financial)"},
    {"name": "Photos", "suggested_contents": "Images from 2023 (cluster: media)"},
    // ... all proposed folders with brief descriptors from clustering
  ]
}
]

Output exactly in this JSON format (no extra text):
{
  "actions": [
    {
      "type": "move_folder" | "move_file" | "rename_file" | "rename_folder" | "merge_folders" | "leave_in_place" | "create_subfolder",
      "source": "<full source path or array of paths for merge>",
      "dest": "<full destination path>",
      "new_name": "<optional new name for rename>",
      "confidence": <integer 0-100>,
      "rationale": "<1-2 sentence explanation>"
    },
    // ... one per item in subtree
  ],
  "unresolved_items": [<list of paths that need further review, if any>]
}

Expected Output Handling:

Parse the JSON actions and integrate into the traversal state.
If "unresolved_items" is non-empty (e.g., due to ambiguity), flag for user input or a follow-up LLM call with more context.
Aggregate confidences: If average <60%, escalate the whole subtree to user review.

LLM Call for Conflict Resolution
If conflicts arise post-traversal (e.g., two actions targeting the same dest), batch them into a separate call.
Prompt Template:

Resolve conflicts in the following proposed actions that overlap on destinations. Suggest adjustments like renames, nesting, or merges. Prioritize thematic alignment based on summaries.

Conflicting Actions:
[INSERT LIST OF CONFLICTING ACTIONS AS JSON ARRAY, e.g.,
[
  {"type": "move_folder", "source": "/folderA", "dest": "/Financial"},
  {"type": "move_folder", "source": "/folderB", "dest": "/Financial"}
]
]

File Details for Conflicts:
[INSERT RELEVANT FILE SUMMARIES/METADATA FOR INVOLVED ITEMS]

User Rules: [INSERT USER RULES]

Output adjusted actions in the same JSON format as before, replacing the originals.

This design ensures the algorithm is robust, explainable, and integrates seamlessly with V1's human-in-the-loop ethos, while handling real-world complexities like partial matches or overgrown nests.