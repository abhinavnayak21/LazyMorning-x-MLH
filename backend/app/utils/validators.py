import re
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def validate_and_filter_tasks(
    extracted_titles: List[str],
    valid_task_titles: List[str]
) -> List[str]:
    """
    Ensure tasks mentioned by the AI correspond to actual user tasks.
    Filters out any hallucinated task titles.
    """
    valid_lower_map = {t.strip().lower(): t for t in valid_task_titles}
    approved = []
    for item in extracted_titles:
        item_clean = item.strip().strip("-*•0123456789. ")
        item_lower = item_clean.lower()
        # Direct match or partial match
        matched = False
        for db_lower, db_orig in valid_lower_map.items():
            if db_lower in item_lower or item_lower in db_lower:
                approved.append(db_orig)
                matched = True
                break
        if not matched and item_clean:
            logger.info(f"Filtered out unverified task reference: '{item_clean}'")
    return approved

def parse_ai_briefing_response(
    raw_text: str,
    valid_tasks: List[Dict[str, Any]],
    valid_notes: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], List[str], str]:
    """
    Parses LLM output into structured briefing components.
    Falls back gracefully if sections are missing or malformed.
    """
    todays_focus = ""
    top_priorities: List[Dict[str, Any]] = []
    upcoming_deadlines: List[Dict[str, Any]] = []
    unfinished_items: List[str] = []
    suggested_first_step = ""

    lines = raw_text.splitlines()
    current_section = None
    section_buffers: Dict[str, List[str]] = {
        "focus": [],
        "priorities": [],
        "deadlines": [],
        "unfinished": [],
        "first_step": []
    }

    for line in lines:
        l_strip = line.strip()
        lower = l_strip.lower()

        if "today's focus" in lower or "todays focus" in lower or "1. focus" in lower:
            current_section = "focus"
            continue
        elif "top" in lower and "priorit" in lower or "2. priorities" in lower:
            current_section = "priorities"
            continue
        elif "upcoming deadline" in lower or "deadlines" in lower or "3. deadlines" in lower:
            current_section = "deadlines"
            continue
        elif "unfinished" in lower or "pending" in lower or "4. unfinished" in lower:
            current_section = "unfinished"
            continue
        elif "suggested first step" in lower or "first step" in lower or "5. first step" in lower:
            current_section = "first_step"
            continue

        if current_section and l_strip:
            section_buffers[current_section].append(l_strip)

    # 1. Parse focus
    if section_buffers["focus"]:
        todays_focus = " ".join(section_buffers["focus"]).strip()
        todays_focus = re.sub(r'^[#*\-:\s]+', '', todays_focus)

    # 2. Parse priorities
    raw_prio_lines = section_buffers["priorities"]
    rank = 1
    for p_line in raw_prio_lines:
        clean_p = re.sub(r'^\d+[\.\)]\s*', '', p_line).strip("-*• ")
        if clean_p and rank <= 3:
            # Check against valid tasks
            matched_task = None
            for vt in valid_tasks:
                if vt["title"].lower() in clean_p.lower() or clean_p.lower() in vt["title"].lower():
                    matched_task = vt
                    break

            title = matched_task["title"] if matched_task else clean_p
            due = matched_task.get("due_date", "Today") if matched_task else "Today"
            priority = matched_task.get("priority", "High") if matched_task else "High"
            tag = f"Due {due} - {priority} priority" if due else f"{priority} priority"
            note = matched_task.get("description", "Focus on this critical item first.") if matched_task else "Key priority for today."

            top_priorities.append({
                "rank": rank,
                "title": title,
                "tag": tag,
                "note": note
            })
            rank += 1

    # 3. Parse deadlines
    for d_line in section_buffers["deadlines"]:
        clean_d = d_line.strip("-*• ")
        if clean_d and len(upcoming_deadlines) < 4:
            # Extract title and date
            upcoming_deadlines.append({
                "title": clean_d,
                "due": "Upcoming",
                "priority": "High"
            })

    # 4. Parse unfinished
    for u_line in section_buffers["unfinished"]:
        clean_u = u_line.strip("-*• ")
        if clean_u:
            unfinished_items.append(clean_u)

    # 5. Suggested first step
    if section_buffers["first_step"]:
        suggested_first_step = " ".join(section_buffers["first_step"]).strip()
        suggested_first_step = re.sub(r'^[#*\-:\s]+', '', suggested_first_step)

    # Defaults if missing
    if not todays_focus:
        todays_focus = "Focus on your highest priority deliverables and start the day with calm momentum."
    if not suggested_first_step:
        suggested_first_step = "Review your top priority task and complete the first quick sub-step to build momentum."

    return todays_focus, top_priorities, upcoming_deadlines, unfinished_items, suggested_first_step
