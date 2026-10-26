import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.note import Note
from backend.app.models.task import Task
from backend.app.models.briefing import Briefing
from backend.app.models.imported_file import ImportedFile
from backend.app.services.briefing_service import BriefingService
from backend.app.services.file_service import FileService
from backend.app.services.ai_service import ai_service
from backend.app.services.scheduler_service import scheduler_service
from backend.app.main import seed_initial_data_if_empty

# Ensure DB and seed data exist
Base.metadata.create_all(bind=engine)
seed_initial_data_if_empty()

st.set_page_config(
    page_title="LazyMorning — Your Overnight Life Assistant",
    page_icon="🦥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper to load image as base64 for reliable HTML embedding
def get_base64_image(image_path: Path) -> str:
    if image_path.exists():
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{encoded}"
    return ""

mascot_path = PROJECT_ROOT / "frontend" / "assets" / "mascot.jpg"
banner_path = PROJECT_ROOT / "frontend" / "assets" / "banner.jpg"
css_path = PROJECT_ROOT / "frontend" / "styles.css"

mascot_b64 = get_base64_image(mascot_path)
banner_b64 = get_base64_image(banner_path)

# Inject custom CSS
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <span style="font-size: 2rem;">🦥</span>
        <div class="sidebar-brand-name">LazyMorning</div>
    </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Notes",
            "Tasks",
            "Files",
            "Morning Briefing",
            "History",
            "Settings"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    if mascot_b64:
        st.markdown(f"""
        <div class="sidebar-footer">
            <img src="{mascot_b64}" alt="LazyMorning Mascot" />
            <div class="sidebar-footer-text">Slow plans, brighter days</div>
        </div>
        """, unsafe_allow_html=True)

# Database helper
def get_db():
    return SessionLocal()

# ----------------- 1. DASHBOARD -----------------
if nav_selection == "Dashboard":
    db = get_db()
    try:
        latest_briefing = BriefingService.get_latest_briefing(db)
        all_tasks = db.query(Task).all()
        pending_tasks = [t for t in all_tasks if not t.is_done]
        notes_count = db.query(Note).count()

        # Parse priorities & deadlines
        top_prios = json.loads(latest_briefing.top_priorities_json) if (latest_briefing and latest_briefing.top_priorities_json) else []
        deadlines = json.loads(latest_briefing.upcoming_deadlines_json) if (latest_briefing and latest_briefing.upcoming_deadlines_json) else []

        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            st.markdown("## Good morning! ☀️")
            st.markdown("<p style='color: #6B7280; margin-top: -10px; font-size: 1.05rem;'>Here's your briefing for today.</p>", unsafe_allow_html=True)
        with top_col2:
            now_str = datetime.now().strftime("%a, %b %d, %Y")
            st.markdown(f"<div style='text-align: right; color: #9CA3AF; font-size: 0.95rem; padding-top: 10px;'>{now_str}</div>", unsafe_allow_html=True)

        # Today's Focus Hero Card
        focus_text = latest_briefing.todays_focus if latest_briefing else "Take a breath and start your morning peacefully."
        mascot_img_html = f'<img src="{mascot_b64}" class="lm-hero-focus-img" alt="Sloth mascot" />' if mascot_b64 else ''

        st.markdown(f"""
        <div class="lm-hero-focus">
            <div class="lm-hero-focus-content">
                <div class="lm-hero-focus-header">
                    <span>🎯</span> Today's Focus
                </div>
                <div class="lm-hero-focus-text">
                    {focus_text}
                </div>
            </div>
            {mascot_img_html}
        </div>
        """, unsafe_allow_html=True)

        # 4 Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="lm-metric-card">
                <div class="lm-metric-icon" style="background: #D1FAE5; color: #059669;">✨</div>
                <div>
                    <div class="lm-metric-num">{len(top_prios) or 3}</div>
                    <div class="lm-metric-label">Top Priorities</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="lm-metric-card">
                <div class="lm-metric-icon" style="background: #FEE2E2; color: #DC2626;">⏳</div>
                <div>
                    <div class="lm-metric-num">{len(deadlines) or 2}</div>
                    <div class="lm-metric-label">Upcoming Deadlines</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="lm-metric-card">
                <div class="lm-metric-icon" style="background: #FEF3C7; color: #D97706;">📝</div>
                <div>
                    <div class="lm-metric-num">{len(pending_tasks)}</div>
                    <div class="lm-metric-label">Pending Tasks</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="lm-metric-card">
                <div class="lm-metric-icon" style="background: #EFF6FF; color: #2563EB;">📄</div>
                <div>
                    <div class="lm-metric-num">{notes_count}</div>
                    <div class="lm-metric-label">Total Notes</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # Two Columns: Latest Morning Briefing & Quick Actions
        col_left, col_right = st.columns([1.6, 1])
        with col_left:
            st.markdown("#### Latest Morning Briefing")
            gen_time = latest_briefing.generated_at.strftime("%I:%M %p") if latest_briefing else "6:30 AM"
            source_badge = f"<span class='badge-low'>Model: {latest_briefing.model_used}</span>" if latest_briefing else ""

            first_step = latest_briefing.suggested_first_step if latest_briefing else "Begin with your top item."
            st.markdown(f"""
            <div class="lm-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="color: #6B7280; font-size: 0.88rem;">🕒 Generated at {gen_time}</div>
                    <div>{source_badge}</div>
                </div>
                <div style="font-size: 0.96rem; color: #374151; line-height: 1.6; margin-bottom: 16px;">
                    <strong>Next Gentle Step:</strong> {first_step}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("View Full Briefing →", type="primary", use_container_width=True):
                st.session_state["nav_override"] = "Morning Briefing"
                st.rerun()

        with col_right:
            st.markdown("#### Quick Actions")
            st.markdown('<div class="lm-card">', unsafe_allow_html=True)

            if st.button("⚡ Generate Briefing Now", use_container_width=True):
                with st.spinner("Generating fresh morning briefing..."):
                    new_b = BriefingService.generate_briefing(db)
                    st.success(f"New briefing generated! ({new_b.source})")
                    st.rerun()

            c1, c2 = st.columns(2)
            with c1:
                with st.popover("➕ Add Note", use_container_width=True):
                    with st.form("quick_note_form"):
                        n_title = st.text_input("Title")
                        n_category = st.selectbox("Category", ["Work", "Personal", "Learning", "Ideas"])
                        n_content = st.text_area("Content")
                        if st.form_submit_button("Save Note"):
                            if n_title and n_content:
                                db.add(Note(title=n_title, content=n_content, category=n_category, tags=n_category))
                                db.commit()
                                st.success("Note saved!")
                                st.rerun()
            with c2:
                with st.popover("☑️ Create Task", use_container_width=True):
                    with st.form("quick_task_form"):
                        t_title = st.text_input("Task Title")
                        t_prio = st.selectbox("Priority", ["High", "Medium", "Low"])
                        t_due = st.text_input("Due Date", "Today, 5:00 PM")
                        if st.form_submit_button("Save Task"):
                            if t_title:
                                db.add(Task(title=t_title, priority=t_prio, due_date=t_due))
                                db.commit()
                                st.success("Task created!")
                                st.rerun()

            if st.button("📁 Import / Scan Files", use_container_width=True):
                scanned = FileService.scan_and_sync_files(db)
                st.info(f"Scanned {len(scanned)} files from imports/ folder.")
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    finally:
        db.close()

# ----------------- 2. MORNING BRIEFING -----------------
elif nav_selection == "Morning Briefing":
    db = get_db()
    try:
        latest = BriefingService.get_latest_briefing(db)

        # Header with Generate button
        head_col, btn_col = st.columns([3, 1.2])
        with head_col:
            st.markdown("## Morning Briefing")
            gen_time_str = latest.generated_at.strftime("%I:%M %p, %a, %b %d, %Y") if latest else "Not yet generated"
            st.markdown(f"<p style='color: #6B7280; margin-top: -10px;'>A concise summary to start your day. <span style='font-size: 0.85rem; color: #9CA3AF;'>• Generated at {gen_time_str}</span></p>", unsafe_allow_html=True)

        with btn_col:
            mode_choice = st.selectbox("Engine", ["Auto (Ollama/Offline)", "Force Fast Offline Engine"], index=0, label_visibility="collapsed")
            if st.button("⚡ Generate New Briefing", type="primary", use_container_width=True):
                with st.spinner("Analyzing tasks, notes, and approved files..."):
                    force_f = (mode_choice == "Force Fast Offline Engine")
                    new_b = BriefingService.generate_briefing(db, force_fallback=force_f)
                    st.success(f"Briefing generated via {new_b.source} ({new_b.model_used})!")
                    st.rerun()

        if not latest:
            st.info("No briefing generated yet. Click 'Generate New Briefing' above to create one!")
        else:
            # 1. Today's Focus Card
            st.markdown(f"""
            <div class="lm-hero-focus">
                <div class="lm-hero-focus-content">
                    <div class="lm-hero-focus-header">
                        <span>🎯</span> Today's Focus
                    </div>
                    <div class="lm-hero-focus-text">
                        {latest.todays_focus}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            top_prios = json.loads(latest.top_priorities_json) if latest.top_priorities_json else []
            deadlines = json.loads(latest.upcoming_deadlines_json) if latest.upcoming_deadlines_json else []
            unfinished = json.loads(latest.unfinished_items_json) if latest.unfinished_items_json else []

            # 2x2 Grid Layout
            c1, c2 = st.columns(2)

            with c1:
                # Top Priorities Card
                st.markdown("""
                <div class="lm-card" style="min-height: 260px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.05rem; margin-bottom: 14px; color: #1F2937;">
                        <span>📍</span> Top Priorities
                    </div>
                """, unsafe_allow_html=True)

                if top_prios:
                    for p in top_prios:
                        st.markdown(f"""
                        <div style="display: flex; gap: 12px; margin-bottom: 14px;">
                            <div style="background: #FEE2E2; color: #DC2626; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; flex-shrink: 0;">{p.get('rank', 1)}</div>
                            <div>
                                <div style="font-weight: 600; color: #1F2937; font-size: 0.95rem;">{p.get('title')}</div>
                                <div style="color: #DC2626; font-size: 0.8rem; font-weight: 500;">{p.get('tag')}</div>
                                <div style="color: #6B7280; font-size: 0.85rem; margin-top: 2px;">{p.get('note')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No top priorities recorded.")

                st.markdown("</div>", unsafe_allow_html=True)

                # Unfinished Items Card
                st.markdown("""
                <div class="lm-card" style="min-height: 200px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; color: #1F2937;">
                        <span>📁</span> Unfinished Items
                    </div>
                """, unsafe_allow_html=True)

                if unfinished:
                    for item in unfinished:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 8px; color: #4B5563; font-size: 0.9rem; margin-bottom: 8px;">
                            <span>•</span> {item}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("All clear! No pending items.")

                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                # Upcoming Deadlines Card
                st.markdown("""
                <div class="lm-card" style="min-height: 260px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.05rem; color: #1F2937;">
                            <span>🗓️</span> Upcoming Deadlines
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if deadlines:
                    for d in deadlines:
                        prio_class = "badge-high" if d.get("priority", "").lower() == "high" else "badge-medium" if d.get("priority", "").lower() == "medium" else "badge-low"
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #F3F4F6;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: #6B7280; font-size: 1.1rem;">📅</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 0.92rem; color: #1F2937;">{d.get('title')}</div>
                                    <div style="color: #6B7280; font-size: 0.8rem;">{d.get('due')}</div>
                                </div>
                            </div>
                            <div>
                                <span class="{prio_class}">{d.get('priority')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No deadlines due soon.")

                st.markdown("</div>", unsafe_allow_html=True)

                # Suggested First Step Card
                st.markdown(f"""
                <div class="lm-first-step">
                    <div class="lm-first-step-title">
                        <span>🧭</span> Suggested First Step
                    </div>
                    <div class="lm-first-step-text">
                        {latest.suggested_first_step}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    finally:
        db.close()

# ----------------- 3. NOTES -----------------
elif nav_selection == "Notes":
    db = get_db()
    try:
        head_col, btn_col = st.columns([3, 1])
        with head_col:
            st.markdown("## Notes")
            st.markdown("<p style='color: #6B7280; margin-top: -10px;'>Capture your thoughts, ideas, and important information.</p>", unsafe_allow_html=True)

        with btn_col:
            with st.popover("➕ New Note", use_container_width=True):
                with st.form("create_note_form", clear_on_submit=True):
                    st.markdown("### Create New Note")
                    nt_title = st.text_input("Title *")
                    nt_cat = st.selectbox("Category", ["Work", "Personal", "Learning", "Ideas", "General"])
                    nt_tags = st.text_input("Tags (comma-separated)", "Work, Ideas")
                    nt_body = st.text_area("Note Content *", height=150)
                    if st.form_submit_button("Save Note", type="primary"):
                        if nt_title and nt_body:
                            new_n = Note(title=nt_title, content=nt_body, category=nt_cat, tags=nt_tags)
                            db.add(new_n)
                            db.commit()
                            st.success("Note created successfully!")
                            st.rerun()
                        else:
                            st.error("Title and content are required.")

        # Search and Filters
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            search_query = st.text_input("Search notes...", placeholder="Type to filter titles or content...", label_visibility="collapsed")
        with f2:
            cat_options = ["All Categories", "Work", "Personal", "Learning", "Ideas", "General"]
            cat_filter = st.selectbox("Category", cat_options, label_visibility="collapsed")
        with f3:
            tag_options = ["All Tags", "Work", "Ideas", "Meeting", "Goals", "Books", "Focus"]
            tag_filter = st.selectbox("Tags", tag_options, label_visibility="collapsed")

        # Query notes
        query = db.query(Note)
        if cat_filter != "All Categories":
            query = query.filter(Note.category == cat_filter)
        if tag_filter != "All Tags":
            query = query.filter(Note.tags.like(f"%{tag_filter}%"))
        if search_query:
            s_term = f"%{search_query}%"
            query = query.filter((Note.title.ilike(s_term)) | (Note.content.ilike(s_term)))

        notes_list = query.order_by(Note.updated_at.desc()).all()

        if not notes_list:
            st.info("No notes found matching your search. Create one with '+ New Note'!")
        else:
            for n in notes_list:
                tag_chips = "".join([f"<span class='tag-pill'>{t.strip()}</span>" for t in n.tags.split(",") if t.strip()])
                date_str = n.updated_at.strftime("%b %d, %Y")

                st.markdown(f"""
                <div class="lm-card" style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="display: flex; gap: 14px;">
                            <div style="background: #EEF2FF; color: #4F46E5; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0;">📝</div>
                            <div>
                                <div style="font-weight: 700; font-size: 1.05rem; color: #1F2937;">{n.title}</div>
                                <div style="color: #4B5563; font-size: 0.9rem; margin: 4px 0 8px 0; line-height: 1.4;">{n.content[:200]}{'...' if len(n.content) > 200 else ''}</div>
                                <div>{tag_chips}</div>
                            </div>
                        </div>
                        <div style="text-align: right; color: #9CA3AF; font-size: 0.85rem; flex-shrink: 0;">
                            {date_str}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Edit / Delete row
                c_del, c_edit, c_space = st.columns([1, 1, 8])
                with c_del:
                    if st.button("🗑️ Delete", key=f"del_note_{n.id}", help="Delete note"):
                        db.delete(n)
                        db.commit()
                        st.rerun()
                with c_edit:
                    with st.popover("✏️ Edit", key=f"edit_pop_{n.id}"):
                        with st.form(f"edit_form_{n.id}"):
                            new_t = st.text_input("Title", value=n.title)
                            new_c = st.text_area("Content", value=n.content)
                            new_tags = st.text_input("Tags", value=n.tags or "")
                            if st.form_submit_button("Update Note"):
                                n.title = new_t
                                n.content = new_c
                                n.tags = new_tags
                                db.commit()
                                st.rerun()

    finally:
        db.close()

# ----------------- 4. TASKS -----------------
elif nav_selection == "Tasks":
    db = get_db()
    try:
        head_col, btn_col = st.columns([3, 1])
        with head_col:
            st.markdown("## Tasks")
            st.markdown("<p style='color: #6B7280; margin-top: -10px;'>Stay on top of what matters.</p>", unsafe_allow_html=True)

        with btn_col:
            with st.popover("➕ New Task", use_container_width=True):
                with st.form("create_task_form", clear_on_submit=True):
                    st.markdown("### Create New Task")
                    tsk_title = st.text_input("Task Title *")
                    tsk_prio = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                    tsk_due = st.text_input("Due Date", "Today, 5:00 PM")
                    tsk_desc = st.text_area("Description / Subtext", "Key item for review")
                    if st.form_submit_button("Create Task", type="primary"):
                        if tsk_title:
                            new_t = Task(title=tsk_title, priority=tsk_prio, due_date=tsk_due, description=tsk_desc)
                            db.add(new_t)
                            db.commit()
                            st.success("Task created!")
                            st.rerun()
                        else:
                            st.error("Task title is required.")

        all_tasks = db.query(Task).all()
        pending_count = sum(1 for t in all_tasks if not t.is_done)
        completed_count = sum(1 for t in all_tasks if t.is_done)

        tab_choice = st.radio(
            "Filter",
            [f"All ({len(all_tasks)})", f"Pending ({pending_count})", f"Completed ({completed_count})"],
            horizontal=True,
            label_visibility="collapsed"
        )

        filter_status = "all"
        if "Pending" in tab_choice:
            filter_status = "pending"
        elif "Completed" in tab_choice:
            filter_status = "completed"

        query = db.query(Task)
        if filter_status == "pending":
            query = query.filter(Task.is_done == False)
        elif filter_status == "completed":
            query = query.filter(Task.is_done == True)

        tasks_list = query.order_by(Task.is_done.asc(), Task.id.desc()).all()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        for t in tasks_list:
            prio_class = "badge-high" if (t.priority or "").lower() == "high" else "badge-medium" if (t.priority or "").lower() == "medium" else "badge-low"

            col_chk, col_content, col_badge, col_due, col_act = st.columns([0.4, 4, 1.2, 1.5, 0.8])

            with col_chk:
                is_checked = st.checkbox("", value=t.is_done, key=f"chk_task_{t.id}", label_visibility="collapsed")
                if is_checked != t.is_done:
                    t.is_done = is_checked
                    db.commit()
                    st.rerun()

            with col_content:
                title_style = "text-decoration: line-through; color: #9CA3AF;" if t.is_done else "font-weight: 600; color: #1F2937;"
                st.markdown(f"<div style='font-size: 0.95rem; {title_style}'>{t.title}</div>", unsafe_allow_html=True)
                if t.description and not t.is_done:
                    st.markdown(f"<div style='color: #6B7280; font-size: 0.82rem;'>{t.description}</div>", unsafe_allow_html=True)

            with col_badge:
                st.markdown(f"<span class='{prio_class}'>{t.priority}</span>", unsafe_allow_html=True)

            with col_due:
                st.markdown(f"<span style='color: #6B7280; font-size: 0.85rem;'>{t.due_date}</span>", unsafe_allow_html=True)

            with col_act:
                if st.button("🗑️", key=f"del_t_{t.id}", help="Delete task"):
                    db.delete(t)
                    db.commit()
                    st.rerun()

            st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px solid #F3F4F6;' />", unsafe_allow_html=True)

    finally:
        db.close()

# ----------------- 5. FILES (IMPORTED FILES) -----------------
elif nav_selection == "Files":
    db = get_db()
    try:
        head_col, btn_col = st.columns([3, 1.2])
        with head_col:
            st.markdown("## Imported Files")
            st.markdown("<p style='color: #6B7280; margin-top: -10px;'>Upload and manage text files for your morning briefings.</p>", unsafe_allow_html=True)

        with btn_col:
            with st.popover("➕ Import Files", use_container_width=True):
                uploaded_file = st.file_uploader("Upload TXT or MD file", type=["txt", "md"])
                if uploaded_file is not None:
                    imports_dir = Path(settings.IMPORTS_DIR).resolve()
                    imports_dir.mkdir(parents=True, exist_ok=True)
                    target = imports_dir / uploaded_file.name
                    with open(target, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    FileService.scan_and_sync_files(db)
                    st.success(f"Imported '{uploaded_file.name}'!")
                    st.rerun()

        # Action bar & filters
        c_scan, c_search, c_type = st.columns([1.2, 2, 1])
        with c_scan:
            if st.button("🔄 Rescan imports/ Folder", use_container_width=True):
                FileService.scan_and_sync_files(db)
                st.success("Files synced!")
                st.rerun()
        with c_search:
            search_f = st.text_input("Search files...", placeholder="Filename...", label_visibility="collapsed")
        with c_type:
            type_f = st.selectbox("Type", ["All Types", "TXT", "MD"], label_visibility="collapsed")

        # Query files
        q = db.query(ImportedFile)
        if type_f != "All Types":
            q = q.filter(ImportedFile.file_type == type_f)
        if search_f:
            q = q.filter(ImportedFile.filename.ilike(f"%{search_f}%"))

        files_list = q.order_by(ImportedFile.imported_at.desc()).all()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Security Notice
        st.markdown("""
        <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; padding: 10px 14px; font-size: 0.85rem; color: #4B5563; margin-bottom: 16px;">
            🔒 <strong>Privacy & Security Gate:</strong> Files must be explicitly approved before their content is included in morning briefing context.
        </div>
        """, unsafe_allow_html=True)

        for f_rec in files_list:
            badge_icon = "📄 TXT" if f_rec.file_type == "TXT" else "📝 MD"
            appr_status = "<span class='badge-high' style='background:#D1FAE5; color:#065F46;'>✅ Approved for AI</span>" if f_rec.is_approved else "<span class='badge-medium'>⏳ Needs Approval</span>"

            st.markdown(f"""
            <div class="lm-card" style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="background: #F3F4F6; padding: 8px 12px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; color: #4F46E5;">{badge_icon}</div>
                        <div>
                            <div style="font-weight: 700; color: #1F2937; font-size: 1rem;">{f_rec.filename}</div>
                            <div style="color: #9CA3AF; font-size: 0.82rem;">{f_rec.file_size_str} • Imported {f_rec.imported_at.strftime('%b %d, %Y')}</div>
                        </div>
                    </div>
                    <div>
                        {appr_status}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Actions row
            c_appr, c_view, c_rm, c_sp = st.columns([1.6, 1.4, 0.8, 4])
            with c_appr:
                btn_label = "Revoke Approval" if f_rec.is_approved else "✅ Approve for AI"
                if st.button(btn_label, key=f"appr_{f_rec.id}"):
                    FileService.approve_file(db, f_rec.id, not f_rec.is_approved)
                    st.rerun()
            with c_view:
                with st.popover("👁️ Preview"):
                    st.markdown(f"**Filename:** {f_rec.filename}")
                    st.code(f_rec.full_content or f_rec.content_preview, language=f_rec.file_type.lower())
            with c_rm:
                if st.button("🗑️", key=f"del_f_{f_rec.id}", help="Delete file"):
                    FileService.delete_file(db, f_rec.id)
                    st.rerun()

    finally:
        db.close()

# ----------------- 6. HISTORY -----------------
elif nav_selection == "History":
    db = get_db()
    try:
        st.markdown("## Briefing History")
        st.markdown("<p style='color: #6B7280; margin-top: -10px;'>View and revisit your past morning briefings.</p>", unsafe_allow_html=True)

        history = BriefingService.get_briefing_history(db, limit=30)
        if not history:
            st.info("No briefings saved yet.")
        else:
            for b in history:
                date_str = b.generated_at.strftime("%a, %b %d, %Y")
                time_str = b.generated_at.strftime("%I:%M %p")
                source_tag = f"<span class='badge-low'>AI ({b.model_used})</span>" if b.source == "ai" else "<span class='badge-medium'>Local Engine</span>"

                st.markdown(f"""
                <div class="lm-card" style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 1.4rem;">📅</span>
                            <div>
                                <div style="font-weight: 700; font-size: 1rem; color: #1F2937;">{date_str} <span style="font-weight: 400; color: #9CA3AF; font-size: 0.88rem;">{time_str}</span></div>
                                <div style="color: #4B5563; font-size: 0.9rem; margin-top: 2px;">{b.todays_focus[:120]}...</div>
                            </div>
                        </div>
                        <div>
                            {source_tag}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"📖 Read Full Briefing ({date_str} - {time_str})"):
                    st.markdown(f"### Today's Focus\n{b.todays_focus}")

                    h_prios = json.loads(b.top_priorities_json) if b.top_priorities_json else []
                    if h_prios:
                        st.markdown("### Top Priorities")
                        for p in h_prios:
                            st.markdown(f"- **{p.get('title')}** ({p.get('tag')}) — {p.get('note')}")

                    h_dead = json.loads(b.upcoming_deadlines_json) if b.upcoming_deadlines_json else []
                    if h_dead:
                        st.markdown("### Upcoming Deadlines")
                        for d in h_dead:
                            st.markdown(f"- **{d.get('title')}**: {d.get('due')} [{d.get('priority')}]")

                    st.markdown(f"### Suggested First Step\n{b.suggested_first_step}")

                    # Export as TXT
                    txt_content = f"LAZYMORNING BRIEFING - {date_str} {time_str}\n\nFOCUS:\n{b.todays_focus}\n\nFIRST STEP:\n{b.suggested_first_step}\n"
                    st.download_button(
                        label="📥 Export Briefing as .txt",
                        data=txt_content,
                        file_name=f"briefing_{b.id}_{b.generated_at.strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key=f"dl_b_{b.id}"
                    )

    finally:
        db.close()

# ----------------- 7. SETTINGS -----------------
elif nav_selection == "Settings":
    db = get_db()
    try:
        st.markdown("## Settings")
        st.markdown("<p style='color: #6B7280; margin-top: -10px;'>Configure your morning assistant preferences.</p>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown('<div class="lm-card">', unsafe_allow_html=True)
            st.markdown("#### 🕒 Briefing Schedule")
            new_time = st.text_input("Daily Briefing Time", value=settings.BRIEFING_TIME, help="Format: HH:MM (24-hr)")
            new_tz = st.selectbox("Timezone", ["Asia/Kolkata", "UTC", "America/New_York", "Europe/London"], index=0)
            enable_sched = st.toggle("Enable scheduled daily briefing", value=settings.ENABLE_SCHEDULE)

            if st.button("Save Schedule Settings", type="primary"):
                settings.BRIEFING_TIME = new_time
                settings.TIMEZONE = new_tz
                settings.ENABLE_SCHEDULE = enable_sched
                scheduler_service.reschedule(new_time)
                if enable_sched:
                    scheduler_service.resume()
                else:
                    scheduler_service.pause()
                st.success("Schedule settings updated!")
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="lm-card">', unsafe_allow_html=True)
            st.markdown("#### ☁️ Cloudflare & AI Configuration")

            provider_choice = st.radio(
                "AI Backend Mode",
                ["Ollama via Cloudflare Tunnel / Local", "Cloudflare Workers AI (Serverless Qwen)"],
                index=0 if settings.AI_PROVIDER == "ollama" else 1,
                horizontal=True
            )

            if provider_choice == "Ollama via Cloudflare Tunnel / Local":
                ollama_url = st.text_input(
                    "Ollama / Cloudflare Tunnel URL",
                    value=settings.OLLAMA_BASE_URL,
                    help="Enter your Cloudflare Tunnel URL (e.g. https://your-tunnel.trycloudflare.com) or local URL (http://localhost:11434)"
                )
                avail_models = ai_service.list_models()
                m_val = settings.OLLAMA_MODEL if settings.OLLAMA_MODEL in avail_models else avail_models[0]
                selected_model = st.selectbox("Model", avail_models, index=avail_models.index(m_val))

                with st.expander("🛡️ Cloudflare Access / Zero Trust Headers (Optional)"):
                    cf_client_id = st.text_input("CF-Access-Client-Id", value=settings.CF_ACCESS_CLIENT_ID)
                    cf_client_secret = st.text_input("CF-Access-Client-Secret", value=settings.CF_ACCESS_CLIENT_SECRET, type="password")
                    cf_bearer = st.text_input("Bearer Token / Authorization", value=settings.CF_BEARER_TOKEN, type="password")

                cf_acc_id = settings.CF_ACCOUNT_ID
                cf_token = settings.CF_API_TOKEN
                cf_w_model = settings.CF_WORKERS_AI_MODEL
                new_provider = "ollama"

            else:
                st.caption("Runs Qwen 2.5 on Cloudflare's serverless GPU edge without local installation.")
                cf_acc_id = st.text_input("Cloudflare Account ID", value=settings.CF_ACCOUNT_ID)
                cf_token = st.text_input("Cloudflare API Token", value=settings.CF_API_TOKEN, type="password")
                cf_w_model = st.selectbox(
                    "Cloudflare Workers AI Model",
                    [
                        "@cf/qwen/qwen2.5-7b-instruct",
                        "@cf/meta/llama-3.1-8b-instruct",
                        "@cf/mistral/mistral-7b-instruct-v0.2"
                    ],
                    index=0
                )
                ollama_url = settings.OLLAMA_BASE_URL
                selected_model = settings.OLLAMA_MODEL
                cf_client_id = settings.CF_ACCESS_CLIENT_ID
                cf_client_secret = settings.CF_ACCESS_CLIENT_SECRET
                cf_bearer = settings.CF_BEARER_TOKEN
                new_provider = "cloudflare_workers_ai"

            test_btn = st.button("🧪 Test Connection")
            is_conn = ai_service.is_available()

            if test_btn:
                # Temporarily check connection
                if is_conn:
                    if new_provider == "cloudflare_workers_ai":
                        st.success(f"🟢 Successfully connected to Cloudflare Workers AI! ({cf_w_model})")
                    else:
                        is_cf = "trycloudflare.com" in ollama_url or "https://" in ollama_url
                        lbl = "Cloudflare Tunnel" if is_cf else "Local Ollama"
                        st.success(f"🟢 Successfully connected to {lbl}! Model: {selected_model}")
                else:
                    st.warning("🟡 Endpoint not reached. Local offline fallback engine is active and ready.")

            if is_conn:
                if settings.AI_PROVIDER == "cloudflare_workers_ai":
                    st.markdown(f"<span style='color: #059669; font-weight: 600;'>🟢 Connected: Cloudflare Workers AI ({settings.CF_WORKERS_AI_MODEL})</span>", unsafe_allow_html=True)
                else:
                    is_cf = "trycloudflare.com" in settings.OLLAMA_BASE_URL or "https://" in settings.OLLAMA_BASE_URL
                    lbl = "Cloudflare Tunnel" if is_cf else "Local Ollama"
                    st.markdown(f"<span style='color: #059669; font-weight: 600;'>🟢 Connected: {lbl} ({settings.OLLAMA_MODEL})</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #4F46E5; font-weight: 600;'>🟢 Local Offline Engine Active (100% Reliable)</span>", unsafe_allow_html=True)

            if st.button("Save AI Settings", type="primary"):
                settings.AI_PROVIDER = new_provider
                settings.OLLAMA_BASE_URL = ollama_url
                settings.OLLAMA_MODEL = selected_model
                settings.CF_ACCESS_CLIENT_ID = cf_client_id
                settings.CF_ACCESS_CLIENT_SECRET = cf_client_secret
                settings.CF_BEARER_TOKEN = cf_bearer
                settings.CF_ACCOUNT_ID = cf_acc_id
                settings.CF_API_TOKEN = cf_token
                settings.CF_WORKERS_AI_MODEL = cf_w_model

                ai_service.provider = new_provider
                ai_service.base_url = ollama_url.rstrip("/")
                ai_service.model = cf_w_model if new_provider == "cloudflare_workers_ai" else selected_model

                st.success("AI and Cloudflare settings saved successfully!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Mascot Banner Card
        if banner_b64:
            st.markdown(f"""
            <div class="lm-banner-footer">
                <img src="{banner_b64}" alt="LazyMorning Relaxed Sloth" />
                <div class="lm-banner-overlay">
                    <h3>Let AI handle the busy work, so you can take it slow.</h3>
                    <p>LazyMorning — Your Overnight Life Assistant</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    finally:
        db.close()
