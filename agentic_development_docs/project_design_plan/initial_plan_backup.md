I want to create a Local File Organizer: AI File Management software.


Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - with an option to do Local LLM. This AI intuitively scans, restructures, and organizes files for quick, seamless access and easy retrieval. It automatically renames and organizes your files. Are you overflowing with unorganized files? Do you spend too much time searching for documents, photos, or important files lost in the chaos? It's time to take control with FileVyasa--the revolutionary app that organizes your files effortlessly using AI-powered natural language processing.

How It Works 💡

Before:
/home/user/messy_documents/
├── IMG_20230515_140322.jpg
├── IMG_20230516_083045.jpg
├── IMG_20230517_192130.jpg
├── budget_2023.xlsx
├── meeting_notes_05152023.txt
├── project_proposal_draft.docx
├── random_thoughts.txt
├── recipe_chocolate_cake.pdf
├── scan0001.pdf
├── vacation_itinerary.docx
└── work_presentation.pptx

0 directories, 11 files

After:

/home/user/organized_documents/
├── Financial
│   └── 2023_Budget_Spreadsheet.xlsx
├── Food_and_Recipes
│   └── Chocolate_Cake_Recipe.pdf
├── Meetings_and_Notes
│   └── Team_Meeting_Notes_May_15_2023.txt
├── Personal
│   └── Random_Thoughts_and_Ideas.txt
├── Photos
│   ├── IMG_20230515_140322.jpg
│   ├── IMG_20230516_083045.jpg
│   └── IMG_20230517_192130.jpg
├── Travel
│   └── Summer_Vacation_Itinerary_2023.docx
└── Work
    ├── Project_X_Proposal_Draft.docx
    ├── Quarterly_Sales_Report.pdf
    └── Marketing_Strategy_Presentation.pptx

7 directories, 11 files
Sample product image from competitor product (for idea / inspiration):
@agentic_development_docs/project_design_plan/sample_product_images/Screenshot 2025-10-30 at 6.36.51 PM.png


Your desktop is a mess? You cannot find anything in your downloads and documents? Sorting and renaming all these files by hand is too tedious? Time to automate it once and benefit from it forever.

it uses LLMS (remote or Local) to help organize messy folders like Downloads or Desktop. Not sort files into folders solely based on extension or filename patterns, but based on what each file actually is supposed to do or does. Basically: what would normally take me a great deal of time for dragging and sorting can now be done in a few.


This AI software totally understands all the files in your local file system. The high-level overview then it plans for a good hierarchy of how the folder structure and organization structure have to be, and then it moves all the files, reads and understands the file contents. 
In the initial step of folder planning mode, you can send a directory (or few directories) to FileVyasa, and it will plan a suggested file structure to organize your files. You can give your inputs as well to update this file structure, and the agent will try to inculcate these inputs.


It is very agentic and interactive experience. the agent takes permission from the user before performing operations. The agent takes in input from the user for rules and prompts for classification, organisation, file moves.



Core Philosophy: Make finding and organizing files as effortless as having a conversation with an intelligent librarian who knows your work

It creates a Clustering map of all the files using Constella library, to have a high-level view of the different files, and which kinds of files have to be together in folders. 
[INSTRUCTION] Go through constella library present in local file system - /Users/sreenivasanac/SoftwareProjects/constella/@agentic_development_docs/project_design_plan/initial_plan.md  
- /Users/sreenivasanac/SoftwareProjects/constella/README.md
And update here how constella library can be used by this project as an input to auto create file structure out of the files. it can be used for getting clusters of files as an input to classify the files, for creating a folder structure plan.
[/INSTRUCTION]

[INSTRUCTION] Many folders have to be moved together, instead of individual files. The folder themselves are reasonably organised, and should not be moved. The whole folder has to be moved to a better more organised place in the file system planned by the agent. Think what implementation decisions of creating the agent will enable this. For example, the agent looks at folder tree structure, and individual file content summaries / descriptors, along with file names, and plans / decides if individual files have to be moved, or the folder is reasonably organised, and the folder as a whole needs to be moved. [/INSTRUCTION]

Copilot Mode: chat with AI to tell AI how you want to sort the file (ie. read and rename all the PDFs)
Change models to use
Have both remote model providers like OpenAI, Claude, Grok, as well as local models running in Ollama server.
Understand images, Sorting and tagging pictures into various folder structures based on image description (through LLM call of Image to text), and its EXIF data
video file support - through EXIF data (maybe Video descriptors as video to text in later stages)
Categorization via text extracted from PDF, DOCX, images (and other formats) , as well as file metadata (like date of creation, file size), and clustering.

Checks file duplication
Sample product image from competitor product:
@agentic_development_docs/project_design_plan/sample_product_images/Screenshot 2025-10-30 at 6.33.25 PM.png

4-level confidence system
🎯 85% confidence threshold - Only acts when genuinely certain
🤔 Interactive questioning - Asks clarifying questions until confident
📊 Visual confidence indicators - Color-coded trust levels (🟢🟡🔴)

Learning from corrections - Remembers your inputs, preferences, rules and prompts and improves over time.


Sorting and renaming PDF invoices based on file content
Safe moving, renaming, copying of files and folders with conflict resolution options.
Very agentic experience. [INSTRUCTION] agentic experience similar to code generation tools like Codex and Claude code. Think of how the experience could be, and update here. [/INSTRUCTION]
Agentic experience - the software updates on how it is thinking, what step it is doing, how it is planning. The plan can be paused in the middle, and user can give instructions, or redirect the plan.
Sample product image from competitor's product (for inspiration / idea): @agentic_development_docs/project_design_plan/sample_product_images/c8f5a808-35f7-4dd9-a1f8-2098caa0bfcc.avif

The AI makes plan, takes decisions - but the user is in control, and has the final say. Review every action - approve, reject or give further inputs, rules, prompts to direct the agent, or select only the changes that you want.
Sample image from competitor site: @agentic_development_docs/project_design_plan/sample_product_images/658c9ee7-1925-43e1-b57c-6b058951789b.avif

Ability to take rules and prompts from the user and execute as well. The rules are not static, but as prompts preferably.
Some sample prompts as rules can also be surfaced to the user
@agentic_development_docs/project_design_plan/sample_product_images/57049b68-f829-4e24-a88d-93b4afd508c5.avif

Has strong guardrails against deleting files. Only file moves for now - no file deletions. There are features like moving incomplete downloads from their ~/Downloads to Archive folder, they are not deleted for now.

[INSTRUCTION]For these [/INSTRUCTION]

The agent has tools like File operations (file read, file move), Image read (get image descriptor and metadata), call constella library for clustering of files information, folder structure planning [INSTRUCTION] Add few other tool calls that will be required for this agentic file organiser [/INSTRUCTION]

[INSTRUCTION] Go through Agno AI - agentic framework documentation using Context7 MCP server. Think of ways in which this project can be made agentic using features and capabilities Agno AI. Basic features add in the main requirements. Non-basic features add in the "later version" (or similar) section. For example, human in the loop.
For example, if a PDF has encrypted password, the agent can ask for password for the file to the user. Or the user can decline giving the password, and give what the file is about in text to the agent, which the agent can use.
Sample product image from competitor product (for inspiration / idea):
@agentic_development_docs/project_design_plan/sample_product_images/image.png
 [/INSTRUCTION]

[INSTRUCTION]
Look at competitor product images of Sortio, in this folder - for ideas and inspiration @agentic_development_docs/project_design_plan/sample_product_images/sortio
[/INSTRUCTION]

File support for major file types like
Images: .png, .jpg, .jpeg, .gif, .bmp
Text Files: .txt, .docx, .md
Spreadsheets: .xlsx, .csv, .xls
Presentations: .ppt, .pptx
PDFs: .pdf
Video: major formats like .mp4
[INSTRUCTION] Add few other similar file formats which need to be supported[/INSTRUCTION]

Compatible with Mac mainly and primarily, but preferably should be able to run in Linux and Windows as well.


[INSTRUCTION] Go through the images in @agentic_development_docs/project_design_plan/sample_product_images folder. These are images of competitor products. This AI app FileVyasa need NOT be verbatim similar to the UI or functionality. Take only the relavant features by seeing these sample product images, which are close to the initial plan idea and requirements I have given, taking inspiration from these sample product images. This AI app FileVyasa need NOT be verbatim similar to the UI or functionality. [/INSTRUCTION]


FileVyasa is well configurable. In the UI, there is settings, in which users can provide their own BYOK remote AI keys, or their Ollama server related information. Many of the decisions, choices are configurable through the App UI.


Features in V3:
File preview for which operation is planned, in the app
Select list of files to rename, the agent goes through file contents, current file name, metadata (date of creation, file type), EXIF data - and then gives brief suitable name to the files. It shows the suggested name in the Interface, and user can select a subset or all of them, and click "Apply", or click "Cancel".
Sample product images from competitor product:
@agentic_development_docs/project_design_plan/sample_product_images/57f935b8-7c46-4146-b733-e53c3bb460d2.avif
@agentic_development_docs/project_design_plan/sample_product_images/f86a78a9-004a-4539-a528-aafb4fd0b1bd.avif
@agentic_development_docs/project_design_plan/sample_product_images/9df5f947-2fd4-434e-a106-66ca4b5c00ad.avif



Features for Later versions v4 (not in v1, v2 or v3):
Semantic search
"Find client payment terms" vs folder navigation
Quickly find files by their actual meaning, powered by advanced vector search.


Read non-text PDF (through OCR)
Sample product image from competitor product (for inspiration / idea):
@agentic_development_docs/project_design_plan/sample_product_images/image.png

Option to rollback file moves - Never fear AI file operations again. One-click undo for any operation that went wrong.
sample product image from competitor site (just as inspiration or idea):
@agentic_development_docs/project_design_plan/sample_product_images/image copy 2.png

# See what the AI did recently
python easy_rollback_system.py --list

# Undo a specific operation
python easy_rollback_system.py --undo 123

# Emergency: Undo ALL today's operations
python easy_rollback_system.py --undo-today

Google Drive integration


Parallel processing
Batch processing



Logs: See what FileVyasa did, when it happened, and where it went

Auto-group / Smart folder
Turn any folder into a Smart Folder.
Instantly, FileVyasa will add new sub-folders to your Smart Folder based on the types of files you typically keep in that folder. It’ll then organize your files into those sub-folders. Configure folders to automatically sort upon receiving a new file


Never organize again
Let FileVyasa handle organizing your computer so you can find files instantly in your smart, self-organizing folder system.


