"""Lightweight, explainable negotiation helper; no API key required."""
import re
STOP_WORDS = {"the","a","an","and","or","but","to","of","for","in","on","at","with","is","are","be","i","we","you","they","want","need","would","like","that","this","it","my","our","their","please","must","should","can","could","will","from","as"}

def _terms(text):
    words = re.findall(r"[a-zA-Z0-9']+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}

def understand_demands(party_a, party_b):
    if not (party_a or "").strip() or not (party_b or "").strip():
        raise ValueError("Please enter demands for both parties.")
    a, b = _terms(party_a), _terms(party_b)
    return {"party_a_summary": party_a.strip(), "party_b_summary": party_b.strip(),
            "shared_terms": sorted(a & b), "party_a_terms": sorted(a - b),
            "party_b_terms": sorted(b - a)}

def find_common_ground(party_a, party_b):
    result = understand_demands(party_a, party_b)
    shared = result["shared_terms"]
    explanation = ("Both parties mention related priorities: " + ", ".join(shared[:12]) + ".") if shared else (
        "No exact keywords overlap. Clarify the reasons behind each demand and identify a broader shared goal.")
    return {"common_terms": shared, "party_a_unique": result["party_a_terms"],
            "party_b_unique": result["party_b_terms"], "explanation": explanation}

def suggest_balanced_solution(party_a, party_b):
    understand_demands(party_a, party_b)
    common = find_common_ground(party_a, party_b)
    shared_line = ("Build the agreement around shared priorities: " + ", ".join(common["common_terms"][:8]) + ".") if common["common_terms"] else (
        "First agree on one overall objective that matters to both parties.")
    return {"proposal": [
        "Both parties identify which parts of their demand are essential and which are flexible.",
        shared_line,
        "Use a phased or trial arrangement so neither party must accept the entire change immediately.",
        "Share responsibilities and benefits fairly, with clear deadlines.",
        "Review the outcome together and adjust it if either party is unfairly affected."],
        "party_a_consideration": "Preserve the most important reasonable points in Party A's request: " + party_a.strip(),
        "party_b_consideration": "Preserve the most important reasonable points in Party B's request: " + party_b.strip(),
        "note": "This is an AI-generated discussion proposal, not a binding agreement. Both parties should review it."}
