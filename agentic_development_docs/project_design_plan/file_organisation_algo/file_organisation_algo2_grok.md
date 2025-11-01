Suggested Algorithm for File and Folder Organization

** Based on the v1 design plan in your project documents, which emphasizes a human-in-the-loop approach with safe, reviewable operations, I'll outline a practical algorithm for transforming a current messy folder structure into a planned one. This algorithm draws from the Folder Move Decision Logic in your initial plan and the File operation Planning module in the v1 design, adapting them for real-world scenarios like inconsistent naming, duplicates, nested clutter, or partial overlaps between current and planned structures  . It avoids direct filesystem changes, focusing instead on generating a detailed action plan (e.g., move entire folders, merge folders, move individual files, or leave items untouched) that can be reviewed and executed later. The core idea is to use a depth-first search (DFS) traversal of the current structure, combined with targeted LLM calls to score and decide actions, ensuring it handles messiness by incorporating file content summaries, metadata, and cohesion scoring.
** This algorithm is designed to be iterative, scalable for large directories (e.g., up to 5k files as per v1 performance targets), and safe—it simulates changes in a "dry-run" mode without touching files . It assumes you already have:
** The current folder structure (e.g., as a tree representation from a scan).
** The planned folder structure (output from the Folder structure Planning Module, including proposed folders, cluster labels, and naming hints) .
** Per-file data: summaries (e.g., ai_brief_summary and ai_summary from extraction), metadata (e.g., type, date, size), and hashes for duplicates .

High-Level Algorithm Steps

1. Prepare Inputs (Preprocessing Phase):
** Traverse the current folder structure using DFS to build a comprehensive tree representation. Start from the root, recursively explore subfolders, and collect details for each node (folder or file): path, name, type (folder/file), metadata, content summary (if file), and any detected duplicates via hashing .
** Generate a flat list of all files and folders for quick lookups.
** Load the planned folder structure as a tree (e.g., with proposed root, subfolders, and suggested placements based on clusters).
** Compute initial "cohesion scores" for current folders: For each folder, score its internal consistency (e.g., topic variance from file summaries, naming patterns, metadata similarity) using a simple heuristic like averaging similarity metrics (e.g., via embeddings if available from Constella) or a quick LLM call for low-confidence cases. Threshold: High cohesion (>80%) suggests potential "move-as-a-unit"; low (<50%) flags for per-file breakdown .


2. Traverse and Match (Comparison Phase):
** Use DFS on the current tree, processing folders before their contents (post-order traversal to handle nested decisions).
** For each current folder or file:
Compare it against the planned tree: Check for name matches, path similarities, or semantic overlaps (e.g., if a current "Photos" folder aligns with a planned "Images" folder via keyword matching from summaries).
** If a direct match (e.g., identical name and high cohesion), mark as "remain" or "move-as-unit" to the planned equivalent.
** For non-matches or low-cohesion folders, queue for LLM decision: Collect context (current subtree, planned tree, file summaries) and call the LLM to propose actions.
** Handle messiness: During traversal, flag anomalies like empty folders, duplicates across trees, or conflicts (e.g., two folders with similar contents that could merge). Use duplicate detection to suggest "combine" if hashes match  .

3. Decide Actions via LLM (Planning Phase):
** For ambiguous or non-matching items, make an LLM call with a structured prompt (detailed below). This is the key step for practicality in messy systems—it leverages AI to reason over summaries and metadata without needing perfect rules upfront.
** Batch calls where possible: Group similar subtrees (e.g., all low-cohesion folders) into one LLM query to reduce API costs, but limit batches to ~50 items to avoid token limits.
** Output a per-item action plan: Categorize as "move folder intact," "merge folder with existing," "move file only," "leave in place," "rename," or "flag for review" (e.g., for conflicts or low confidence) .
** Incorporate user rules: If you have predefined prompts (e.g., "keep invoices under Finance"), inject them into the LLM context for guided decisions 


4. Simulate and Refine (Dry-Run Phase):
**  Build a simulated "after" tree by applying the proposed actions virtually (e.g., in memory, tracking source-to-destination mappings).
**  Detect conflicts in the simulation: E.g., filename collisions trigger rename suggestions; overlapping merges prompt for overrides.
** Compute an overall organization score for the simulated structure (e.g., based on cohesion, depth, and variance as in your initial plan) . If below a threshold (e.g., 70%), loop back to step 3 with refined LLM prompts highlighting issues.
** Generate a visual/textual diff: Show before/after trees, highlighted changes, and confidence levels (e.g., green for high-cohesion moves).


5. Output and Review (Finalization Phase):
** Produce a structured action list: For each file/folder, list the action, source/destination paths, rationale, and rollback info (e.g., original path for undo)  .
** Allow human review: Present in a UI or log, with options to approve, reject, or adjust (e.g., override a merge).
** For execution (out of scope here, but as per v1): Only proceed after approval, logging rollback metadata 


This algorithm is practical for messy systems because DFS handles arbitrary nesting, LLM calls provide flexible reasoning for inconsistencies, and the dry-run ensures safety. It aligns with your project's emphasis on confidence scoring and user control, scaling well by processing subtrees independently  . Estimated runtime: For 1k files, preprocessing ~10s, LLM calls ~1-2 min (batched), simulation ~5s on modern hardware.

Example LLM Call Design

To make decisions in step 3, use a single LLM prompt per batch/subtree. Pass it via your model's API (e.g., OpenAI-compatible endpoint as in v1) . Structure the prompt for clarity and enforce JSON output for easy parsing.

You are an AI file organizer assistant. Your task is to analyze the current folder structure, compare it to the planned structure, and propose safe actions for each file and folder to align them. Focus on: moving entire high-cohesion folders as units, merging similar folders, moving individual files, renaming for consistency, or leaving items if they already fit. Prioritize safety—no deletions. Use these user rules: [Insert user-provided rules/prompts here, e.g., "Group all .pdf invoices under Finance/Invoices"].

Current folder subtree (DFS order):
[Insert current subtree as a indented tree string, e.g.:
- messy_folder/
  - subfolder1/ (cohesion score: 75%, files: img1.jpg (summary: vacation photo, metadata: date=2023-05), doc1.txt (summary: notes on trip)]
  - file2.xlsx (summary: budget spreadsheet, metadata: type=spreadsheet)
]

Planned folder structure:
[Insert full planned tree as indented string, e.g.:
- organized_root/
  - Photos/ (for images)
  - Financial/ (for budgets)
  - Travel/ (for itineraries)
]

File details:
[For each file in subtree, list: filename, path, ai_brief_summary (2 lines), ai_summary (4 lines), metadata (type, date, size, hash for duplicates)]

For each folder and file in the current subtree, output a JSON array of actions. Each action object: 
{
  "item_path": "full/current/path",
  "action_type": "move_folder_intact" | "merge_folder" | "move_file" | "rename" | "leave" | "flag_review",
  "destination_path": "full/planned/path (or 'N/A' for leave/flag)",
  "rationale": "brief explanation (1-2 sentences)",
  "confidence": "high" | "medium" | "low" (based on cohesion/match strength)
}
If merging, specify the target folder to merge into. Flag low-confidence items for user review.

Expected Structured Output (JSON): The LLM returns a JSON array like:

[
  {
    "itemPath": "messy_folder/subfolder1/",
    "actionType": "move_folder_intact",
    "destinationPath": "organized_root/Photos/",
    "rationale": "Subfolder has high cohesion around images with travel themes, matches planned Photos folder.",
    "confidence": "high"
  },
  {
    "itemPath": "messy_folder/file2.xlsx",
    "actionType": "move_file",
    "destinationPath": "organized_root/Financial/",
    "rationale": "File summary indicates budget content, aligns with Financial cluster; no folder match so move individually.",
    "confidence": "medium"
  }
]

This prompt ensures structured, actionable outputs while incorporating your project's extraction outputs (e.g., summaries) and decision logic for whole-folder vs. per-file moves . Adjust token limits by shortening summaries if needed.
