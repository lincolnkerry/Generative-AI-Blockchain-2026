import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("LessonSender")

@mcp.tool()
def format_discovery_lesson(
    day_number: int,
    title: str,
    objective: str,
    main_concept: str,
    golden_rule: str,
    key_points: list[str],
    call_to_action: str,
    youtube_url: str,
    references: str,
    flashback_question: str | None = None,
    flashback_answer: str | None = None
) -> str:
    """
    Formats a lesson in the current discovery template for Discord.

    Args:
        day_number: The current day of the track.
        title: The specific topic of the day.
        objective: What the user will learn today.
        main_concept: A brief explanation of the core concept.
        golden_rule: The overarching philosophy or main actionable idea.
        key_points: A list of concrete, educational facts. CRITICAL: DO NOT write outlines, summaries, or titles (e.g., "Origin of meatballs"). You MUST write the actual historical facts or definitions (e.g., "Meatballs were brought to Sweden in the 18th century by King Charles XII").
        call_to_action: A practical task for the user.
        youtube_url: A valid YouTube URL.
        references: A valid website link or source used for this lesson.
        flashback_question: A question reviewing the previous day's concept.
        flashback_answer: The correct answer to the flashback question.
    """
    if not youtube_url:
        return "Error: youtube_url is required for the discovery lesson."
    if not references:
        return "Error: references are required for the discovery lesson."

    lines = []

    # Header
    lines.append(f"📚 Day {day_number} - {title}\n")

    # Objective
    lines.append("🎯 Objective for today:")
    lines.append(f"{objective}\n")

    # Flashback (Only if day > 1 and data provided)
    if day_number > 1 and flashback_question and flashback_answer:
        lines.append("🧠 Flashback:")
        lines.append(f"{flashback_question}")
        lines.append(f"👉 || {flashback_answer} || (click to reveal)\n")

    # Main content
    lines.append(f"📖 Point of the day: {main_concept}\n")
    lines.append(f"Main idea: {golden_rule}\n")

    # Key points
    lines.append("Key takeaways:")
    for i, point in enumerate(key_points, 1):
        lines.append(f"[{i}] : {point}")
    lines.append("")

    # YouTube / Deep Dive (required)
    lines.append("🍿 To go further:")
    lines.append("If you want to dive deeper or see another perspective, here's a great video on the topic:")
    lines.append(f"{youtube_url}\n")

    # Action item
    lines.append("🛠️ Your turn:")
    lines.append(f"{call_to_action}")

    # References (required)
    lines.append("\n🔗 References:")
    lines.append(f"{references}")

    return "\n".join(lines)


@mcp.tool()
def format_revision_lesson(
    day_number: int,
    title: str,
    concept_points: list[str],
    technical_detail: str,
    pop_quiz_question: str,
    pop_quiz_answer: str,
    deep_dive_estimated_time: str,
    deep_dive_resource: str,
    references: str
) -> str:
    """
    Formats a lesson in the revision template provided by the user.

    Args:
        day_number: The current day of the track.
        title: The specific topic of the day.
        concept_points: A list of factual points explaining the core concepts. MUST contain actual information, not just titles.
        technical_detail: A deep dive into a specific rule or mechanism.
        pop_quiz_question: A question testing the user's knowledge.
        pop_quiz_answer: The correct answer to the pop quiz.
        deep_dive_estimated_time: The estimated time in minutes.
        deep_dive_resource: A specific resource name or URL.
        references: A valid website link or source used for this lesson.
    """
    if not deep_dive_resource:
        return "Error: deep_dive_resource is required for the revision lesson."
    if not references:
        return "Error: references are required for the revision lesson."

    lines = []

    lines.append(f"🚀 Micro-Review Day {day_number}: {title}\n")
    lines.append("**📖 Concept of the Day:**\n")

    for point in concept_points:
        lines.append(f"- {point}")

    lines.append("\n**📐 The Technical Detail / Golden Rule:**")
    lines.append(technical_detail)

    lines.append("\n**🧠 Pop Quiz (Think before revealing!):**")
    lines.append(pop_quiz_question)

    lines.append("\n> **Answer:** || {0} ||".format(pop_quiz_answer))
    lines.append("**📺 Deep Dive (Estimated time: {0} min):**".format(deep_dive_estimated_time))
    lines.append(f"*Today's Resource:* {deep_dive_resource}")

    lines.append("\n🔗 References:")
    lines.append(f"{references}")

    return "\n".join(lines)


# Maintain backwards compatibility for existing calls.
format_and_send_lesson = format_discovery_lesson

if __name__ == "__main__":
    mcp.run()