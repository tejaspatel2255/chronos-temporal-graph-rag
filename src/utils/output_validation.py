import re

def is_degenerate_output(text: str) -> bool:
    """
    Validates if LLM generated output is degenerate, such as moderation labels
    or incomplete fragments under ~20 words.
    
    Conditions for degeneracy:
    1. A known moderation label pattern: matches regex `^(safe|unsafe|flagged|blocked)\b.{0,20}$` (case-insensitive)
    2. Short content (under 20 words) that lacks any standard terminal punctuation (. ! ? etc.) at the end.
    """
    if not text or not isinstance(text, str):
        return True
    
    clean_text = text.strip()
    if not clean_text:
        return True
        
    # Check 1: Moderation label pattern (e.g. "safe", "User Safety: safe" if it fits structure, etc.)
    # Note: Regex specifically looks for safe/unsafe/flagged/blocked at the boundary, followed by up to 20 chars
    moderation_pattern = re.compile(r'^(safe|unsafe|flagged|blocked)\b.{0,20}$', re.IGNORECASE)
    if moderation_pattern.match(clean_text):
        return True
        
    # Also catch common variations like "User Safety: safe", "Content: safe", etc.
    # by checking if the text matches standard label prefixing.
    extended_mod_pattern = re.compile(r'^[\w\s_-]+:\s*(safe|unsafe|flagged|blocked)\b.{0,20}$', re.IGNORECASE)
    if extended_mod_pattern.match(clean_text):
        return True

    # Check 2: Short fragments under ~20 words lacking terminal punctuation
    words = clean_text.split()
    if len(words) < 20:
        # Check if last character is terminal punctuation
        last_char = clean_text[-1]
        if last_char not in ('.', '!', '?', '"', "'", '`', ')'):
            return True

    return False
