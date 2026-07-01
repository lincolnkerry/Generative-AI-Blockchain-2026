
tools:
  - name: log
    description: Audits your intent before executing any other tool. Mandatory first step.
  - name: cron
    description: Schedules, updates, or deletes automated delivery jobs.
  - name: web_search
    description: Performs a web search to gather factual data for "DÉCOUVERTE" tracks.
  - name: YOUTUBE_SCRAPPER_MCP
    description: Searches YouTube for exactly one educational video related to the current lesson topic.
  - name: PDF_READER_MCP
    description: Extracts text from user-provided PDF files inside the Revision_ref/ directory. Must support page targeting.
  - name: TRACK_MANAGER_MCP
    description: Manage the TUTOR_MEMORY by adding, increment and delete track
  - name: LESSON_SENDER_MCP
    description: Create a formatted message for Discord User