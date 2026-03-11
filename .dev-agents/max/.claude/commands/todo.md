# /todo - Manage Team Todos

View, add, or complete team-level todo items tracked in the shared task list.

## Usage

/todo                     - List all open todos
/todo add <description>   - Add a new todo item
/todo done <number>       - Mark a todo as completed
/todo remove <number>     - Remove a todo item

## Steps

1. Read `../shared/tasks/todos.md` to load the current todo list. Create the file if it does not exist.
2. Based on the subcommand:

   **List (default):**
   - Display all open todos with their index numbers, owners, and priorities.
   - Show completed items separately at the bottom if any exist.

   **Add:**
   - Append a new line in this format: `- [ ] <description> — Owner: <name>, Added: YYYY-MM-DD`
   - If the user specifies an owner or priority, include them. Otherwise default owner to "unassigned".

   **Done:**
   - Change the matching item from `- [ ]` to `- [x]` and append `Completed: YYYY-MM-DD`.

   **Remove:**
   - Delete the matching line from the file.

3. Write the updated content back to `../shared/tasks/todos.md`.
4. Confirm the action taken and show the updated list.
