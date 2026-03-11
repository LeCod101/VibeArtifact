# /suggest - Provide Product Suggestions

Analyze the current project state and offer product direction suggestions to guide next steps.

## Usage

/suggest [area]

Optional `area` can be: `features`, `architecture`, `priorities`, `risks`, or omitted for a general analysis.

## Steps

1. Gather context by reading:
   - `../shared/status.json` - Team progress and current work.
   - `../shared/tasks/todos.md` - Outstanding tasks.
   - `doc_internal/devlog/PROGRESS.md` - Overall project progress (if accessible).
   - `doc_internal/PRD.md` - Product requirements (if accessible).
   - `doc_internal/开发计划_最终版.md` - Development plan (if accessible).
2. Analyze the current state:
   - What has been completed vs. what remains.
   - Where the team is spending the most effort.
   - Any gaps between the plan and actual progress.
   - Potential risks or bottlenecks.
3. Generate suggestions organized by the requested area (or all areas if none specified):
   - **Feature Priorities** - Which features to focus on next and why.
   - **Architecture Concerns** - Any structural issues to address early.
   - **Process Improvements** - Ways to improve team velocity or coordination.
   - **Risk Mitigation** - Identified risks and recommended actions.
4. Present suggestions as a numbered list with brief rationale for each.
5. Flag any suggestions that conflict with existing decisions in the project docs.
