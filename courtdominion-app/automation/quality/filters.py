import re
def quality_filter(text: str):
    checks = [
        (r"INSERT\s+TEXT\s+HERE", "AI placeholder detected"),
        (r"Lorem ipsum", "Filler text detected"),
        (r"{.*?}", "Potential template artifact"),
        (r"\*\*TODO\*\*", "Unresolved TODO"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return False, reason
    if len(text.split()) < 30:
        return False, "Too short"
    # crude duplicate detection: many repeated words
    words = text.lower().split()
    if len(words) > 0 and max(words.count(w) for w in set(words)) / len(words) > 0.3:
        return False, "Repetitive text detected"
    return True, None
