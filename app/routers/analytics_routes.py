from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.orm import Session
from database import get_db, PG_SessionLocal, get_pg_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel
from typing import Optional
from crud.analytics_ops import revenue_analysis, student_performance_analysis, faculty_performance_analysis, get_institution_growth

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = ['Inter', 'Roboto', 'DejaVu Sans', 'sans-serif']

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