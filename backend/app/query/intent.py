INTENTS = [
    "summary",
    "comparison",
    "strategy_alignment",
    "gap_detection",
    "risk_review",
    "executive_questions",
    "cross_division_theme",
]


def classify_intent(question: str) -> str:
    text = question.lower()
    if any(word in text for word in ["compare", "versus", "vs", "quarter"]):
        return "comparison"
    if any(word in text for word in ["align", "objective", "pillar", "strategy"]):
        return "strategy_alignment"
    if any(word in text for word in ["gap", "missing", "not covered"]):
        return "gap_detection"
    if any(word in text for word in ["risk", "issue", "blocker"]):
        return "risk_review"
    if any(word in text for word in ["challenge", "question for leadership", "executive"]):
        return "executive_questions"
    if any(word in text for word in ["cross division", "across divisions", "theme"]):
        return "cross_division_theme"
    return "summary"
