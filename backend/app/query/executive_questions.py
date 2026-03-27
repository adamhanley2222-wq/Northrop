def generate_executive_questions(gaps: list[str], evidence_count: int, risk_mentions: int) -> list[str]:
    questions: list[str] = []

    if evidence_count < 3:
        questions.append("Which objectives are currently under-evidenced and who owns closing the evidence gap?")

    if risk_mentions > 0:
        questions.append("Which unresolved risks require explicit executive escalation before next review?")

    for gap in gaps:
        if "accountability" in gap.lower():
            questions.append("Who is accountable for delivery where ownership is currently unclear?")
            break

    if not questions:
        questions.append("What is the most important follow-up question leadership should ask in the next review?")

    return questions[:4]
