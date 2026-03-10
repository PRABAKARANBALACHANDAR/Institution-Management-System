from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from database import get_db, PG_SessionLocal, get_pg_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import Optional
from crud.analytics_ops import revenue_analysis, student_performance_analysis, faculty_performance_analysis, get_institution_growth

router=APIRouter(tags=["Analytics"], prefix="/analytics")

class RevenueReportSummary(BaseModel):
    month:int
    year:int
    total_fees_collected:float
    total_salary_paid:float
    net_revenue:float

@router.get("/dashboard", response_model=RevenueReportSummary)
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
    """
    Interactive Analytics Dashboard Visualizations via Matplotlib.
    """
    # Fetch Data
    revenue = revenue_analysis(db_pg)
    faculty_perf = faculty_performance_analysis(db_pg)
    student_perf = student_performance_analysis(db_pg, {})

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('IMS Analytics Dashboard', fontsize=18, fontweight='bold', color='#2c3e50')

    # 1. Revenue
    ax_rev = axes[0, 0]
    labels = ['Fees Collected', 'Salaries Paid', 'Net Revenue']
    values = [revenue["total_fees_collected"], revenue["total_salary_paid"], revenue["net_revenue"]]
    ax_rev.bar(labels, values, color=['#2ecc71', '#e74c3c', '#3498db'])
    ax_rev.set_title('Monthly Revenue Summary')
    for i, v in enumerate(values):
        ax_rev.text(i, v + (max(values)*0.01 if max(values) > 0 else 1), f"${v:,.2f}", ha='center', va='bottom', fontweight='bold')
    
    # 2. Teacher Performance
    ax_fac = axes[0, 1]
    top_fac = sorted(faculty_perf, key=lambda x: x.get("performance_score", 0), reverse=True)[:5]
    if top_fac:
        fac_labels = [f.get("faculty_name", "Unknown")[:12] for f in top_fac]
        fac_scores = [f.get("performance_score", 0) for f in top_fac]
        ax_fac.barh(fac_labels, fac_scores, color='#9b59b6')
        ax_fac.invert_yaxis()  # Labels read top-to-bottom
    ax_fac.set_title('Top 5 Teacher Performance Scores')
    
    # 3. Student Performance
    ax_stu = axes[1, 0]
    top_stu = sorted(student_perf, key=lambda x: x.get("avg_marks", 0), reverse=True)[:10]
    if top_stu:
        stu_labels = [s.get("student_name", "Unknown")[:10] for s in top_stu]
        stu_scores = [s.get("avg_marks", 0) for s in top_stu]
        ax_stu.plot(stu_labels, stu_scores, marker='o', linestyle='-', color='#f1c40f', linewidth=2, markersize=8)
        ax_stu.tick_params(axis='x', rotation=45)
    ax_stu.set_title('Top 10 Student Average Marks')
    ax_stu.grid(True, linestyle='--', alpha=0.6)
    
    # 4. Growth
    ax_grow = axes[1, 1]
    growth = get_institution_growth(db_pg)
    dist = growth.get("student_distribution", {})
    if dist:
        years_g = list(dist.keys())
        counts_g = list(dist.values())
        bars = ax_grow.bar(years_g, counts_g, color='#34495e')
        ax_grow.bar_label(bars, padding=3)
        ax_grow.set_ylabel('New Admissions')
    else:
        ax_grow.text(0.5, 0.5, "No Admission Data", ha='center')
    ax_grow.set_title(f'Annual Student Intake (Total: {growth.get("total_students", 0)})')

    plt.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
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