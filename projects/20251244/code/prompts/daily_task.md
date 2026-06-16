# Daily Task Prompt

Run the Daily Korea Morning Briefing workflow for Korean readers.

## Time

07:00 KST

## Workflow

1. Agent B collects at least 15 news candidates.
2. Agent B records title, source, link, importance, and trace information.
3. Agent A verifies freshness, duplicates, source diversity, and user relevance.
4. Agent A selects the final 10 items.
5. Agent A writes a Discord-ready briefing.
6. Save local backup logs.
7. Save Notion structured logs if available.
8. If Notion fails, continue Discord delivery and record the error locally.

## Final output requirements

- 10 final news items
- Korean-language summaries
- Source links
- Clear section formatting for Discord
- Execution summary
- Logging status
