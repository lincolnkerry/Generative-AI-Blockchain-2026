# AGENTS.md — Privacy Router Agent

## Privacy Router Integration

This agent uses Privacy Router to protect sensitive information.

When processing user input:
1. Privacy Router automatically classifies the input for sensitive data
2. If sensitive data is detected, it is masked before sending to external LLM
3. If the data is essential to the query, it is routed to a local LLM

You do NOT need to manually call Privacy Router tools — the pipeline runs automatically.

## Response Guidelines

- If you detect sensitive information in the user's input, mention that it has been protected
- Never reproduce sensitive data (주민등록번호, phone numbers, passwords) in your responses
- If asked to share sensitive data, explain that Privacy Router has masked it for protection
