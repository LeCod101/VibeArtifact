# /meeting - Record Meetings

Parse meeting information and append a structured record to the shared meetings log.

## Usage

/meeting <topic> [attendees] [notes]

If arguments are omitted, prompt interactively for meeting details.

## Steps

1. Collect meeting details from the user:
   - **Date/Time** - Default to current timestamp if not provided.
   - **Topic** - The main subject of the meeting.
   - **Attendees** - List of participants (agent names or roles).
   - **Key Decisions** - Decisions made during the meeting.
   - **Action Items** - Tasks assigned, with owners and deadlines.
   - **Notes** - Any additional discussion points.
2. Format the record using this structure:

```markdown
## Meeting: <Topic>
- **Date:** YYYY-MM-DD HH:MM
- **Attendees:** ...
### Decisions
- ...
### Action Items
- [ ] <task> — Owner: <name>, Due: <date>
### Notes
- ...
---
```

3. Append the formatted record to `../shared/tasks/meetings.md`. Create the file if it does not exist.
4. If action items were recorded, remind the PM to follow up or assign them via `/todo`.
