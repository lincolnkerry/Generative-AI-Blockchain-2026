================================================================
		     Team name and members
================================================================
Solo project — Emilien PEYON (EECS, GIST, student ID 20268003).
================================================================
		     Primary project type
================================================================
Autonomous AI Agent / Educational Tool.
================================================================
		Problem statement and target user
================================================================
Continuous learning is one of the most valuable habits a student can build, yet sustaining it day after day is difficult: there is no system that pushes learners back to a topic, resources are scattered across the web, and a single static resource cannot adapt to how each person learns. The target user is any student who wants to keep learning consistently outside of formal coursework, but lacks the structure, time, or motivation to do so alone. AI Discord Tutor addresses this by reaching out to the student directly, on a platform they already use daily, and delivering personalized lessons automatically.
================================================================
	Installation and execution instructions
================================================================
AI Discord Tutor runs directly inside Discord, no separate installation is required on the user's side. To start, the user simply sends a direct message to the bot. Including the word "discover"  in the message activates Discovery mode, in which the agent searches the web to introduce a new topic. Including the word "revision", together with an attached document, activates Revision mode, in which the agent builds lessons strictly from that document. Once a mode is selected, the agent generates a syllabus, schedules the lessons, and begins sending them automatically every day.
================================================================
Differentiation statement versus big-tech assistants/platforms :
================================================================ 
Unlike mainstream AI assistants such as ChatGPT or Gemini, which wait passively for a new prompt, AI Discord Tutor is proactive: once a learning path is planned, it autonomously sends a lesson every day without any further request from the student. It also avoids the generic, one-size-fits-all answers typical of big-tech assistants by working in two strictly separated modes: Revision, where every lesson is grounded only in the documents the student personally supplies, and Discovery, where new topics are sourced from the web. The tutor lives inside Discord, a platform students already use daily, rather than asking them to open a new app or subscribe to a separate learning platform. Finally, where large platforms run on heavy, opaque infrastructure, AI Discord Tutor is built from a small set of transparent, single-purpose tools (PDF extraction, web search, scheduling, memory, formatting) on top of a lightweight model, keeping the cost of running it measured in cents rather than a recurring subscription.
================================================================
		   7-day usage log summary
================================================================
A detailed usage log covering the test period is provided in the logs/ folder of the project, recording each lesson sent, the mode used (Revision or Discovery), and the date and time of delivery.
================================================================
	Cost estimate and local/cloud stack discussion
================================================================
The agent runs on GPT-4o mini by using OpenRouter. Over a two-week period covering both the initial setup/testing phase and regular usage, the total API cost was $2.21, which extrapolates to roughly $4 per month at a similar usage level.
================================================================
		Privacy/security summary
================================================================
The current version does not implement dedicated privacy or security measures: all data is treated as public, with no encryption or access control in place. The only safeguard concerns documents uploaded for Revision mode, which are deleted after being processed and are not retained afterward.
================================================================
	Demo video link, 5 minutes or less
================================================================
A demo video is included in the "AI_AGENT_TUTOR\Slide_Report_Demo" as Demo_Video.mp4.*
================================================================
	Links to paper/report and slides
================================================================
The full project report and the presentation slides are included in the "AI_AGENT_TUTOR\Slide_Report_Demo"  folder.