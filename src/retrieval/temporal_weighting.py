import re
import math
from datetime import datetime

def apply_temporal_weighting(candidates: list[dict], timeframe: str, classifications: list[str]) -> list[dict]:
    """Applies a boost/decay factor to candidates based on timeframe matching, recency, or historical decay."""
    if not candidates:
        return []
        
    timeframe = timeframe.strip().lower() if timeframe else ""
    classifications = [c.upper() for c in classifications]

    weighted_candidates = []
    
    for cand in candidates:
        score = cand["score"]
        meta = cand.get("metadata", {})
        cand_text = cand.get("text", "").lower()
        
        cand_quarter = str(meta.get("quarter", "")).lower()
        cand_date_str = str(meta.get("date", "") or meta.get("created_at", "")).lower()
        
        # 1. Exact Period Boost (e.g. Q2 2024 matching)
        if timeframe:
            if (timeframe in cand_quarter or 
                timeframe in cand_date_str or 
                timeframe in cand_text):
                score *= 1.5
        
        # 2. Recency Boost ("latest", "recent", "current", "newest")
        if any(word in timeframe for word in ["latest", "recent", "current", "newest", "last"]):
            doc_date = None
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    clean_date = re.match(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?)?", cand_date_str)
                    if clean_date:
                        doc_date = datetime.strptime(clean_date.group(0), fmt)
                        break
                except ValueError:
                    continue
            
            if doc_date:
                # Use June 30, 2024 as our data anchor
                ref_date = datetime(2024, 6, 30)
                days_diff = abs((ref_date - doc_date).days)
                # Exponential decay
                decay = math.exp(-0.002 * days_diff)
                score *= (0.5 + 0.5 * decay)
                
        new_cand = cand.copy()
        new_cand["score"] = score
        weighted_candidates.append(new_cand)
        
    return weighted_candidates
