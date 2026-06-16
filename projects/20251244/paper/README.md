Daily Korea Morning Briefing Agent

Course: Generative AI and Blockchain
Project title: Daily Korea Morning Briefing Agent  
Team / Member: Youngu Lee
Primary project type: Smartened OpenClaw/Agent System  
Secondary type: Cost-Efficient AI Stack / Privacy-Preserving AI Service  
Status: Final submission draft

1. Project overview

Daily Korea Morning Briefing Agent is a collaborative multi-agent workflow that automatically creates a reliable morning news briefing for Korean user. The system runs at 07:00 KST, collects a larger candidate pool, verifies and filters sources, selects the final 10 news items, summarizes them, delivers the result to Discord, and records the workflow in local logs and Notion.

This project is not a single summarization bot. It separates the workflow into two agent roles:

- Agent A: Orchestrator / Verifier**
  - Checks freshness, duplicates, source diversity, and user relevance.
  - Selects the final 10 items.
  - Produces the final Discord-ready briefing.
  - Records execution evidence and errors.
- Agent B: Collector / Reviewer**
  - Collects at least 15 candidate news items.
  - Records title, source, link, importance, and trace information.

2. Problem statement and target user

Problem

Manually checking Korean news every morning is time-consuming. A single-agent summarizer can be fast, but it may hallucinate, miss important items, overuse one source, or provide weak traceability.

Target user

The target user is a Korean reader, student, researcher, or worker who wants a concise and trustworthy daily morning briefing without manually checking multiple news sources.

3. Practical value

The system provides practical value by:

   1. Reducing repetitive morning news-checking time.
   2. Producing a consistent Discord-ready daily briefing.
   3. Using a larger candidate pool before final selection.
   4. Keeping evidence logs so the output can be reviewed later.
   5. Maintaining a local backup log even when Notion logging fails.
   6. Supporting user-specific personalization, such as preferred news categories, topics, keywords, or media sources, so the daily briefing can be tailored to the user’s interests instead of providing a generic news summary.

4. Installation and execution instructions

Prerequisites
- OpenClaw installed and configured
- Hermes runtime configured
- Discord integration configured
- Web search / web open tools available
- Notion integration configured, optional but recommended
- Python 3.10+ for optional local log hashing

Basic execution flow
   1. Configure OpenClaw Cron to trigger the workflow at 07:00 KST.
   2. Run Hermes with Agent A and Agent B prompts.
   3. Agent B collects at least 15 candidates.
   4. Agent A verifies candidates and selects the final 10.
   5. The final briefing is posted to Discord.
   6. Local logs are saved under `usage-log/`.
   7. Notion logs are created when available.
   8. Optional: run the hash manifest script to make the logs tamper-evident.

```bash
python code/scripts/hash_manifest.py usage-log/ hash_manifest.jsonl
```

5. Differentiation versus big-tech assistants/platforms

This project differs from general big-tech assistants in the following ways:

   1. Workflow-level traceability  
      The system logs the candidate pool, selection rationale, verification results, tool usage, and errors, instead of only showing the final answer.

   2. Role-separated multi-agent verification  
      Candidate collection and final verification are separated into different agent roles to reduce single-agent failure.

   3. Local-first evidence backup  
      Even if Notion fails, local filesystem logs remain mandatory, so the output does not disappear with one external service failure.

   4. Domain-specific morning briefing workflow  
      The system is optimized for Korean daily news delivery at 07:00 KST, rather than being a generic chatbot.

   5. Cost-efficient agent decomposition
      The workflow can be further divided into smaller agent roles, such as source collection, duplicate filtering, relevance scoring, verification, and final summarization. This allows lightweight or cheaper models to handle simpler steps while stronger models are used only for high-value reasoning tasks, which can reduce overall operating cost.

   6. Extensible recurring-task framework 
      Although the current implementation focuses on daily news briefings, the same agent workflow can be reused for other scheduled knowledge tasks, such as summarizing one research paper per day, monitoring a specific technology field, tracking policy changes, or preparing a daily study briefing.

   7. Tamper-evident extension path  
      The project includes a future blockchain-based verification direction where hashes of briefings, links, logs, and traces can be stored to detect post-edit changes.

6. 7-day usage log summary

The 7-day usage log is stored in:

- [`usage-log/usage-log.md`](usage-log/usage-log.md)

Summary fields to maintain:

- Date and execution time
- Whether the scheduled run succeeded
- Number of candidate items collected
- Number of final items delivered
- Discord delivery status
- Notion logging status
- Local backup logging status
- Main errors and fixes
- Evidence link or screenshot reference

> Important: Do not invent usage logs. Replace the template rows with real execution evidence before final submission.

7. Cost estimate and local/cloud stack discussion

Estimated monthly cost

The estimated monthly cost is approximately $20 per month.
This is because the project uses Codex as the AI agent model through a paid subscription plan. No additional API, cloud server, or paid database costs are currently required.
The cost can be further optimized by assigning different models to different agent roles. For example, lightweight or cheaper models can handle simple tasks such as news collection, duplicate filtering, formatting, and logging, while stronger models can be reserved for higher-level reasoning tasks such as verification, ranking, and final briefing generation. This role-based model selection can reduce unnecessary use of expensive models and make the system more cost-efficient.

Local/cloud split

Local: scheduling, workflow rules, backup logs, and hash manifest generation
Cloud/API: Codex-based AI agent reasoning, web search, Discord posting, and Notion logging

This hybrid stack keeps evidence logs and backup files local while using cloud-based tools only for tasks that require external access or strong reasoning capability. Since the system mainly relies on a paid Codex subscription, the estimated operating cost remains approximately $20 per month, with no additional cloud server or paid database cost currently required.

8. Privacy and security summary

Data handled

- News candidate metadata: title, source, link, importance, trace
- Final briefing text
- Tool usage logs
- Error logs
- Optional Notion page link
- Discord delivery evidence

Privacy design

- The workflow focuses on public news data, not sensitive personal data.
- Local backup logs are kept to avoid total dependence on external services.
- Secrets such as API keys, Discord tokens, and Notion tokens must not be committed to GitHub.
- `.env`, token files, local credentials, and raw private logs should be excluded by `.gitignore`.

Threat model

| Threat                  | Risk               | Mitigation                                    |
|                         |                    |                                               |
| Hallucinated news       | False briefing     | Source verification and candidate pool review |
| Duplicate or stale news | Low-quality output | Freshness and duplicate checks                |
| Single-agent failure    | Unchecked mistakes | Agent role separation                         |
| Notion failure          | Missing evidence   | Mandatory local backup logs                   |
| Log tampering           | Weak auditability  | Optional SHA-256 hash manifest                |
| Secret leakage          | Account compromise | `.gitignore` and no token commits             |


9. Technical rigor and smartening method

Architecture

```text
OpenClaw Cron 07:00 KST
        |
        v
Hermes Runtime
        |
        +--> Agent B: collect >=15 candidates
        |
        +--> Agent A: verify, dedupe, diversify, select final 10
        |
        +--> Discord delivery
        |
        +--> Local backup log
        |
        +--> Notion structured log
        |
        +--> Optional hash manifest
```

Smartening method

The project applies a Week 11-style smartening method through:

- tool-connected agents,
- role-separated collaboration,
- retrieval/search-based candidate collection,
- verification and reflection before final delivery,
- structured logging and monitoring.

Measurable evidence to include

- Number of candidate items collected each day
- Number of rejected duplicate/stale items
- Number of final delivered items
- Discord delivery evidence
- Notion/local log evidence
- Error frequency and recovery behavior