# /status - View Team Status Summary

Check the current status of all team members: who's doing what, their progress, and any blockers.

## Usage

/status

## Steps

1. Read `../shared/status.json` to get the latest team status data.
2. For each team member, summarize:
   - **Name & Role** - Which agent and their responsibility.
   - **Current Task** - What they are currently working on.
   - **Progress** - Percentage or stage of completion.
   - **Blockers** - Any issues preventing progress (or "None").
   - **Last Updated** - When their status was last refreshed.
3. Display a compact table or structured summary of all members.
4. Highlight any blockers or overdue items that need PM attention.
5. If `status.json` does not exist or is empty, report that no status data is available and suggest team members update their status.
