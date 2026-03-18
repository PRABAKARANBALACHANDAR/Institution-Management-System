from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse, HTMLResponse
import asyncio
import hashlib
import io
from html import escape
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import jwt
from sqlalchemy.orm import Session
from database import MYSQL_SessionLocal, PG_SessionLocal, get_pg_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import Optional
from crud.analytics_ops import revenue_analysis, student_performance_analysis, faculty_performance_analysis, get_institution_growth
from schemas.permissions import MYSQL_Permissions

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = ['Inter', 'Roboto', 'DejaVu Sans', 'sans-serif']

router=APIRouter(tags=["Analytics"], prefix="/analytics")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def _render_dashboard_content(revenue: dict, faculty_perf: list[dict], student_perf: list[dict], growth: dict) -> str:
    faculty_items = "".join(
        f"<li>{escape(item.get('faculty_name', 'Unknown'))} - {float(item.get('performance_score', 0)):.2f}</li>"
        for item in faculty_perf[:5]
    ) or "<li>No faculty analytics available</li>"

    student_items = "".join(
        f"<li>{escape(item.get('student_name', 'Unknown'))} - {float(item.get('avg_marks', 0)):.2f}</li>"
        for item in student_perf[:5]
    ) or "<li>No student analytics available</li>"

    growth_items = "".join(
        f"<li>{escape(str(year))}: {count}</li>"
        for year, count in growth.get("student_distribution", {}).items()
    ) or "<li>No growth data available</li>"

    return f"""
    <p>Month: {revenue["month"]}/{revenue["year"]}</p>

    <h2>Revenue</h2>
    <p>Fees Collected: {revenue["total_fees_collected"]}</p>
    <p>Salary Paid: {revenue["total_salary_paid"]}</p>
    <p>Net Revenue: {revenue["net_revenue"]}</p>

    <h2>Top Faculty</h2>
    <ul>{faculty_items}</ul>

    <h2>Top Students</h2>
    <ul>{student_items}</ul>

    <h2>Growth</h2>
    <p>Total Students: {growth.get("total_students", 0)}</p>
    <ul>{growth_items}</ul>
"""

def _render_simple_dashboard_html(revenue: dict, faculty_perf: list[dict], student_perf: list[dict], growth: dict) -> str:
    content_html = _render_dashboard_content(revenue, faculty_perf, student_perf, growth)
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Analytics Dashboard</title>
</head>
<body>
    <h1>Analytics Dashboard</h1>
    <p id="dashboard-status">Connecting...</p>

    <h2>Chart View</h2>
    <img id="dashboard-plot" src="/analytics/dashboard/view" alt="Analytics chart" style="max-width: 100%; height: auto;" />

    <div id="dashboard-content">
        {content_html}
    </div>

    <script>
        const statusEl = document.getElementById("dashboard-status");
        const plotEl = document.getElementById("dashboard-plot");
        const contentEl = document.getElementById("dashboard-content");
        const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
        let ws = null;
        let reconnectTimer = null;
        let reconnectDelayMs = 2000;

        function scheduleReconnect() {{
            if (reconnectTimer) {{
                return;
            }}

            statusEl.textContent = "Reconnecting...";
            reconnectTimer = window.setTimeout(() => {{
                reconnectTimer = null;
                connectWebSocket();
            }}, reconnectDelayMs);
            reconnectDelayMs = Math.min(reconnectDelayMs * 2, 10000);
        }}

        function connectWebSocket() {{
            ws = new WebSocket(`${{wsProtocol}}://${{window.location.host}}/analytics/dashboard/ws`);

            ws.onopen = function () {{
                reconnectDelayMs = 2000;
                statusEl.textContent = "Live updates connected";
            }};

            ws.onmessage = function (event) {{
                const message = JSON.parse(event.data);
                if (message.type === "heartbeat") {{
                    statusEl.textContent = "Live updates connected";
                    return;
                }}

                if (message.content_html) {{
                    contentEl.innerHTML = message.content_html;
                    plotEl.src = `/analytics/dashboard/view?t=${{Date.now()}}`;
                    statusEl.textContent = "Updated";
                }}
            }};

            ws.onclose = function () {{
                statusEl.textContent = "Connection closed";
                scheduleReconnect();
            }};

            ws.onerror = function () {{
                statusEl.textContent = "Connection error";
                ws.close();
            }};
        }}

        connectWebSocket();
    </script>
 </body>
</html>
"""

def _build_dashboard_data(db_pg: Session) -> dict:
    revenue = revenue_analysis(db_pg)
    faculty_perf = sorted(
        faculty_performance_analysis(db_pg),
        key=lambda item: item.get("performance_score", 0),
        reverse=True,
    )
    student_perf = sorted(
        student_performance_analysis(db_pg, {}),
        key=lambda item: item.get("avg_marks", 0),
        reverse=True,
    )
    growth = get_institution_growth(db_pg)
    return {
        "revenue": revenue,
        "faculty_perf": faculty_perf,
        "student_perf": student_perf,
        "growth": growth,
    }

def _dashboard_signature(data: dict) -> str:
    serializable = {
        "revenue": data["revenue"],
        "faculty_perf": data["faculty_perf"][:5],
        "student_perf": data["student_perf"][:5],
        "growth": data["growth"],
    }
    return hashlib.sha256(json.dumps(serializable, sort_keys=True, default=str).encode("utf-8")).hexdigest()

def _get_ws_user(websocket: WebSocket) -> MYSQL_Permissions | None:
    token = websocket.cookies.get("access_token")
    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

    username = payload.get("sub")
    if not username:
        return None

    db = MYSQL_SessionLocal()
    try:
        user = db.query(MYSQL_Permissions).filter(MYSQL_Permissions.username == username).first()
        if not user:
            return None
        role_val = getattr(user.role, "value", user.role)
        if str(role_val).lower() == "admin" or getattr(user, "get_analytics", 0) == 1:
            return user
        return None
    finally:
        db.close()


class RevenueReportSummary(BaseModel):
    month:int
    year:int
    total_fees_collected:float
    total_salary_paid:float
    net_revenue:float

@router.get("/dashboard", response_class=HTMLResponse)
def view_dashboard_page(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    data = _build_dashboard_data(db_pg)
    return HTMLResponse(
        _render_simple_dashboard_html(
            data["revenue"],
            data["faculty_perf"],
            data["student_perf"],
            data["growth"],
        )
    )

@router.websocket("/dashboard/ws")
async def dashboard_updates(websocket: WebSocket):
    user = _get_ws_user(websocket)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    last_signature = None

    try:
        while True:
            db_pg = PG_SessionLocal()
            try:
                data = _build_dashboard_data(db_pg)
            finally:
                db_pg.close()

            current_signature = _dashboard_signature(data)
            if current_signature != last_signature:
                await websocket.send_text(json.dumps({
                    "type": "dashboard_update",
                    "content_html": _render_dashboard_content(
                        data["revenue"],
                        data["faculty_perf"],
                        data["student_perf"],
                        data["growth"],
                    )
                }))
                last_signature = current_signature
            else:
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return

@router.get("/dashboard/summary", response_model=RevenueReportSummary)
def get_revenue_analysis(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    return revenue_analysis(db_pg)

@router.get("/dashboard/view", response_class=StreamingResponse)
def view_analytics_dashboard(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics"))
):
    revenue = revenue_analysis(db_pg)
    faculty_perf = faculty_performance_analysis(db_pg)
    student_perf = student_performance_analysis(db_pg, {})

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.patch.set_facecolor('#f8f9fa')
    plt.subplots_adjust(top=0.9, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Institutional Management System - Advanced Analytics', 
                 fontsize=22, fontweight='bold', color='#1a1a1a', y=0.98)

    # 1. Revenue Visualization (Seaborn Barplot)
    ax_rev = axes[0, 0]
    rev_labels = ['Fees', 'Salary', 'Net']
    rev_vals = [revenue["total_fees_collected"], revenue["total_salary_paid"], revenue["net_revenue"]]
    sns.barplot(x=rev_labels, y=rev_vals, ax=ax_rev, palette=['#10b981', '#ef4444', "#f6e03b"], hue=rev_labels, legend=False)
    ax_rev.set_title('Monthly Financial Overview', fontsize=14, fontweight='semibold', pad=15)
    ax_rev.set_ylabel('Amount ($)', fontsize=12)
    
    # Add values on top of bars
    for i, v in enumerate(rev_vals):
        ax_rev.text(i, v + (max(rev_vals)*0.02 if max(rev_vals) > 0 else 100), 
                    f"${v:,.0f}", ha='center', fontweight='bold', color='#4b5563')
    
    # 2. Top Teacher Performance (Seaborn Horizontal Bar)
    ax_fac = axes[0, 1]
    top_fac = sorted(faculty_perf, key=lambda x: x.get("performance_score", 0), reverse=True)[:5]
    if top_fac:
        f_names = [f.get("faculty_name", "Unknown")[:15] for f in top_fac]
        f_scores = [float(f.get("performance_score", 0)) for f in top_fac]
        sns.barplot(x=f_scores, y=f_names, ax=ax_fac, palette="flare", hue=f_names, legend=False)
        ax_fac.set_xlim(0, max(f_scores)*1.1 if f_scores else 100)
    ax_fac.set_title('Top 5 Faculty Performance Marks', fontsize=14, fontweight='semibold', pad=15)
    ax_fac.set_xlabel('Score Index', fontsize=12)
    
    # 3. Top Student Performance (Seaborn Pointplot)
    ax_stu = axes[1, 0]
    top_stu = sorted(student_perf, key=lambda x: x.get("avg_marks", 0), reverse=True)[:10]
    if top_stu:
        s_names = [s.get("student_name", "Unknown")[:8] for s in top_stu]
        s_marks = [float(s.get("avg_marks", 0)) for s in top_stu]
        sns.lineplot(x=s_names, y=s_marks, ax=ax_stu, marker='o', markersize=10, 
                     linewidth=3, color='#f59e0b', label='Avg Marks')
        ax_stu.set_ylim(0, 110)
        ax_stu.tick_params(axis='x', rotation=30)
    ax_stu.set_title('Top 10 Student Academic Ranking', fontsize=14, fontweight='semibold', pad=15)
    ax_stu.set_ylabel('Average Marks', fontsize=12)
    
    # 4. Growth Trend (Seaborn countplot-style via bar)
    ax_grow = axes[1, 1]
    growth = get_institution_growth(db_pg)
    dist = growth.get("student_distribution", {})
    if dist:
        years = [str(y) for y in dist.keys()]
        counts = list(dist.values())
        sns.barplot(x=years, y=counts, ax=ax_grow, palette="viridis", hue=years, legend=False)
        ax_grow.set_ylabel('New Admissions', fontsize=12)
    else:
        ax_grow.text(0.5, 0.5, "Insufficient Data for Trend", ha='center', color='gray')
    
    ax_grow.set_title(f'Student Intake Trend (Total: {growth.get("total_students", 0)})', 
                      fontsize=14, fontweight='semibold', pad=15)

    # Final Polish
    sns.despine(left=True, bottom=True)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")

@router.get("/performance_analysis/students")
def get_student_performance_analysis(
    student_id: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    filters = {}
    if student_id:
        filters["student_id"] = student_id
    if semester:
        filters["semester"] = semester
    
    return student_performance_analysis(db_pg, filters)

@router.get("/performance_analysis/faculty")
def get_faculty_performance_analysis(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    return faculty_performance_analysis(db_pg)

@router.get("/institution_growth")
def get_growth_analysis(
    db_pg: Session = Depends(get_pg_db),
    user=Depends(RequirePermission("get_analytics")),
):
    return get_institution_growth(db_pg)
