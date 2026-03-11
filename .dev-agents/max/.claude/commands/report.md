# /report - Generate Project Report

Compile a daily or weekly project report from team status, tasks, and review data.

## Usage

/report [daily|weekly]

Defaults to `daily` if no argument is provided.

## Steps

1. Read the following shared data sources:
   - `../shared/status.json` - Current team member statuses.
   - `../shared/tasks/todos.md` - Open and completed team todos.
   - `../shared/tasks/meetings.md` - Recent meeting records.
   - `../shared/reviews/` - Any pending or completed review items.
2. Compile the report with these sections:
   - **Report Type & Date** - Daily or weekly, with date range.
   - **Summary** - One-paragraph overview of project health.
   - **Progress** - What was accomplished since the last report.
   - **In Progress** - What is currently being worked on, by whom.
   - **Blockers & Risks** - Issues that need attention.
   - **Upcoming** - Next priorities and planned work.
   - **Metrics** - Tasks completed, tasks added, blockers resolved (if data available).
3. Save the report to `../shared/docs/report-YYYY-MM-DD.md`.
4. Display the full report to the user for review.
