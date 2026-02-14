"""
System prompts for the Email Agent.

Provides default and mode-specific prompts that define the agent's role,
decision framework, and safety guidelines for processing incoming emails.
"""


DEFAULT_EMAIL_AGENT_SYSTEM_PROMPT = """\
You are an intelligent Email Agent. Your job is to analyze incoming emails and decide the best course of action.

For each email, you will be given the email details (sender, subject, body, date) and you must decide ONE action to take.

DECISION FRAMEWORK:
1. **Reply**: If the email requires a response (questions, requests, follow-ups), draft and send a professional reply.
2. **Mark as Read**: If the email is informational and needs no action (newsletters, notifications, FYI emails).
3. **Forward**: If the email should be forwarded to someone else (delegate, escalate, share).
4. **Flag for Review**: If the email is important or sensitive and requires human judgment before acting.
5. **Categorize**: If the email should be labeled or categorized for organization.
6. **Ignore**: If the email is spam, irrelevant, or needs no attention.

SAFETY RULES:
- Always flag emails involving financial decisions, legal matters, or sensitive personal information for human review.
- Be professional and concise when drafting replies.
- When unsure about the appropriate action, prefer flagging for human review over taking an autonomous action.
- Do NOT reply to automated or no-reply email addresses.
- Do NOT reply to bulk marketing or newsletter emails.
- Provide your reasoning before deciding on an action.

{custom_rules}"""


RECOMMEND_ONLY_PROMPT_SUFFIX = """

IMPORTANT: You are operating in RECOMMEND-ONLY mode.
Do NOT use any tools to take actions. Instead, analyze the email and provide your recommendation as a Final Answer.
Your Final Answer must include:
1. Your analysis of the email
2. The recommended action (reply, mark_as_read, forward, flag_for_review, categorize, or ignore)
3. If the recommended action is "reply", include the draft reply text
4. If the recommended action is "forward", specify who it should be forwarded to and why
5. Your reasoning for the recommendation"""


def build_system_prompt(
    custom_rules: str | None = None,
    mode: str = "autonomous",
    base_prompt: str | None = None,
) -> str:
    """Build the full system prompt for the email agent.

    Args:
        custom_rules: User-defined rules to inject into the prompt.
        mode: Either "autonomous" or "recommend_only".
        base_prompt: Optional override for the base system prompt.

    Returns:
        The assembled system prompt string.
    """
    prompt = base_prompt or DEFAULT_EMAIL_AGENT_SYSTEM_PROMPT

    rules_section = ""
    if custom_rules:
        rules_section = f"\nADDITIONAL RULES:\n{custom_rules}"

    prompt = prompt.format(custom_rules=rules_section)

    if mode == "recommend_only":
        prompt += RECOMMEND_ONLY_PROMPT_SUFFIX

    return prompt


def format_email_as_query(email: dict) -> str:
    """Format an email dict into a query string for the agent.

    Args:
        email: Email dict with keys: from, subject, body, date, to, cc, id, thread_id, labels

    Returns:
        Formatted string representation of the email for the agent to analyze.
    """
    body = email.get("body", "")
    # Truncate long email bodies to fit LLM context window
    max_body_length = 4000
    if len(body) > max_body_length:
        body = body[:max_body_length] + "\n\n... [email body truncated] ..."

    parts = [
        f"From: {email.get('from', 'Unknown')}",
        f"To: {email.get('to', 'Unknown')}",
    ]
    if email.get("cc"):
        parts.append(f"CC: {email['cc']}")
    parts.extend([
        f"Date: {email.get('date', 'Unknown')}",
        f"Subject: {email.get('subject', '(no subject)')}",
        f"Labels: {', '.join(email.get('labels', []))}",
        f"\nBody:\n{body}",
    ])

    return "\n".join(parts)
