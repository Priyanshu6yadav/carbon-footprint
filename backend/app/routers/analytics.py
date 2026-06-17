"""
CarbonTrack — Analytics & Reporting Router.
Provides aggregated carbon metrics, category breakdowns, habit tracking rates,
eco-score trends, and PDF exports. All results are cached in Redis.
"""
from datetime import datetime, timedelta, timezone
import json
from io import BytesIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
import redis.asyncio as aioredis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.database import get_db
from app.redis_client import get_redis
from app.models.carbon_log import CarbonLog
from app.models.eco_score import EcoScore
from app.models.habit import Habit, HabitLog
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(tags=["analytics"])


# ─── Helper Functions ─────────────────────────────────────────────

def parse_date_range(range_type: str, start_str: Optional[str], end_str: Optional[str]):
    """Parses date range query parameters and returns start, end, and aggregation bucket."""
    end_date = datetime.now(timezone.utc)
    if range_type == "week":
        start_date = end_date - timedelta(days=7)
        bucket = "day"
    elif range_type == "month":
        start_date = end_date - timedelta(days=30)
        bucket = "day"
    elif range_type == "year":
        start_date = end_date - timedelta(days=365)
        bucket = "month"
    elif range_type == "custom":
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid custom date format. Use YYYY-MM-DD.",
            )
        diff_days = (end_date - start_date).days
        if diff_days > 180:
            bucket = "month"
        else:
            bucket = "day"
    else:
        # Default to month
        start_date = end_date - timedelta(days=30)
        bucket = "day"
        range_type = "month"

    return start_date, end_date, bucket, range_type


async def check_cache(redis: aioredis.Redis, key: str) -> Optional[dict]:
    try:
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    return None


async def write_cache(redis: aioredis.Redis, key: str, data: any, expire: int = 300):
    try:
        await redis.set(key, json.dumps(data), ex=expire)
    except Exception:
        pass


# ─── Endpoints ───────────────────────────────────────────────────

@router.get("/carbon-trend")
async def get_carbon_trend(
    range_type: str = Query("month", alias="range"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Time-bucketed carbon totals grouped by day or month."""
    start_date, end_date, bucket, range_name = parse_date_range(range_type, start, end)
    
    # 1. Check cache
    cache_key = f"analytics:{current_user.id}:carbon-trend:{range_name}:{start_date.date()}:{end_date.date()}"
    cached = await check_cache(redis, cache_key)
    if cached is not None:
        return cached

    # 2. Query
    period_field = func.date_trunc(bucket, CarbonLog.created_at).label("period")
    stmt = (
        select(
            period_field,
            func.sum(CarbonLog.transport_total).label("transport"),
            func.sum(CarbonLog.energy_total).label("energy"),
            func.sum(CarbonLog.food_total).label("food"),
            func.sum(CarbonLog.shopping_total).label("shopping"),
            func.sum(CarbonLog.total_monthly_kg).label("total"),
        )
        .where(
            CarbonLog.user_id == current_user.id,
            CarbonLog.created_at >= start_date,
            CarbonLog.created_at <= end_date,
        )
        .group_by("period")
        .order_by("period")
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Format response
    data = []
    for r in rows:
        data.append({
            "period": r.period.date().isoformat(),
            "transport": float(r.transport or 0.0),
            "energy": float(r.energy or 0.0),
            "food": float(r.food or 0.0),
            "shopping": float(r.shopping or 0.0),
            "total": float(r.total or 0.0),
        })

    # 3. Write cache
    await write_cache(redis, cache_key, data)
    return data


@router.get("/category-breakdown")
async def get_category_breakdown(
    range_type: str = Query("month", alias="range"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Aggregate emissions by category for selected range."""
    start_date, end_date, _, range_name = parse_date_range(range_type, start, end)
    
    # 1. Check cache
    cache_key = f"analytics:{current_user.id}:category-breakdown:{range_name}:{start_date.date()}:{end_date.date()}"
    cached = await check_cache(redis, cache_key)
    if cached is not None:
        return cached

    # 2. Query
    stmt = (
        select(
            func.sum(CarbonLog.transport_total).label("transport"),
            func.sum(CarbonLog.energy_total).label("energy"),
            func.sum(CarbonLog.food_total).label("food"),
            func.sum(CarbonLog.shopping_total).label("shopping"),
        )
        .where(
            CarbonLog.user_id == current_user.id,
            CarbonLog.created_at >= start_date,
            CarbonLog.created_at <= end_date,
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    data = {
        "transport": float(row.transport or 0.0) if row else 0.0,
        "energy": float(row.energy or 0.0) if row else 0.0,
        "food": float(row.food or 0.0) if row else 0.0,
        "shopping": float(row.shopping or 0.0) if row else 0.0,
    }

    # 3. Write cache
    await write_cache(redis, cache_key, data)
    return data


@router.get("/habit-completion")
async def get_habit_completion(
    range_type: str = Query("month", alias="range"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Completion rate per active habit in the selected range."""
    start_date, end_date, _, range_name = parse_date_range(range_type, start, end)
    
    # 1. Check cache
    cache_key = f"analytics:{current_user.id}:habit-completion:{range_name}:{start_date.date()}:{end_date.date()}"
    cached = await check_cache(redis, cache_key)
    if cached is not None:
        return cached

    total_days = max(1, (end_date - start_date).days)

    # 2. Query completions count per active habit
    stmt = (
        select(
            Habit.id,
            Habit.name,
            Habit.slug,
            Habit.icon,
            func.count(HabitLog.id).label("logged_days"),
        )
        .select_from(Habit)
        .outerjoin(
            HabitLog,
            (HabitLog.habit_id == Habit.id)
            & (HabitLog.user_id == current_user.id)
            & (HabitLog.log_date >= start_date.date())
            & (HabitLog.log_date <= end_date.date()),
        )
        .where(Habit.is_active == True)  # noqa: E712
        .group_by(Habit.id, Habit.name, Habit.slug, Habit.icon)
    )
    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for r in rows:
        logged = r.logged_days or 0
        data.append({
            "id": str(r.id),
            "name": r.name,
            "slug": r.slug,
            "icon": r.icon,
            "logged_days": logged,
            "completion_rate": min(1.0, float(logged / total_days)),
        })

    # 3. Write cache
    await write_cache(redis, cache_key, data)
    return data


@router.get("/eco-score-trend")
async def get_eco_score_trend(
    range_type: str = Query("month", alias="range"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Historical eco score trend grouped by day or month."""
    start_date, end_date, bucket, range_name = parse_date_range(range_type, start, end)
    
    # 1. Check cache
    cache_key = f"analytics:{current_user.id}:eco-score-trend:{range_name}:{start_date.date()}:{end_date.date()}"
    cached = await check_cache(redis, cache_key)
    if cached is not None:
        return cached

    # 2. Query
    period_field = func.date_trunc(bucket, EcoScore.created_at).label("period")
    stmt = (
        select(
            period_field,
            func.avg(EcoScore.score).label("score"),
        )
        .where(
            EcoScore.user_id == current_user.id,
            EcoScore.created_at >= start_date,
            EcoScore.created_at <= end_date,
        )
        .group_by("period")
        .order_by("period")
    )
    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for r in rows:
        data.append({
            "period": r.period.date().isoformat(),
            "score": float(round(r.score or 0.0, 1)),
        })

    # 3. Write cache
    await write_cache(redis, cache_key, data)
    return data


@router.get("/report/pdf")
async def export_pdf_report(
    range_type: str = Query("month", alias="range"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """Generates and returns a server-side PDF sustainability report."""
    start_date, end_date, _, range_name = parse_date_range(range_type, start, end)

    # 1. Gather all analytical data (using internal calls or identical queries)
    carbon_trend = await get_carbon_trend(range_type, start, end, db, redis, current_user)
    breakdown = await get_category_breakdown(range_type, start, end, db, redis, current_user)
    habits = await get_habit_completion(range_type, start, end, db, redis, current_user)
    eco_trend = await get_eco_score_trend(range_type, start, end, db, redis, current_user)

    # 2. Build PDF Document with ReportLab
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#065f46"), # Emerald 800
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4b5563"), # Gray 600
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'H2Section',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0f766e"), # Teal 700
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#111827") # Gray 900
    )
    
    elements = []
    
    # ─── HEADER ───
    elements.append(Paragraph("CarbonTrack Sustainability Report", title_style))
    elements.append(Paragraph(
        f"<b>User:</b> {current_user.full_name or current_user.username} | "
        f"<b>Scope:</b> {range_name.capitalize()} Range ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))
    
    # ─── SECTION 1: EMISSIONS ───
    elements.append(Paragraph("1. Carbon Footprint Analysis", h2_style))
    total_co2 = sum(breakdown.values())
    elements.append(Paragraph(
        f"In the selected period, your total recorded carbon footprint was <b>{total_co2:.1f} kg CO₂e</b>. "
        "Here is the detailed category-by-category breakdown of your emissions:",
        body_style
    ))
    elements.append(Spacer(1, 10))
    
    # Emissions table
    em_table_data = [
        [Paragraph("<b>Emission Category</b>", body_style), Paragraph("<b>Emissions (kg CO₂e)</b>", body_style), Paragraph("<b>Breakdown %</b>", body_style)]
    ]
    for category_name, category_val in breakdown.items():
        pct = (category_val / total_co2 * 100) if total_co2 > 0 else 0.0
        em_table_data.append([
            Paragraph(category_name.capitalize(), body_style),
            Paragraph(f"{category_val:.1f} kg", body_style),
            Paragraph(f"{pct:.1f}%", body_style)
        ])
        
    t_em = Table(em_table_data, colWidths=[180, 160, 160])
    t_em.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    # Quick fix for headers color
    for i in range(3):
        t_em.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
        
    elements.append(t_em)
    elements.append(Spacer(1, 15))
    
    # ─── SECTION 2: ECO SCORES & HABITS ───
    elements.append(Paragraph("2. Sustainability Metrics & Habits", h2_style))
    avg_score = sum(d["score"] for d in eco_trend) / len(eco_trend) if eco_trend else 0.0
    elements.append(Paragraph(
        f"Your average Eco-Score during this period was <b>{avg_score:.1f}/100</b>. "
        "Below is your daily eco-habit adoption log and rate of completion:",
        body_style
    ))
    elements.append(Spacer(1, 10))
    
    # Habits table
    hb_table_data = [
        [Paragraph("<b>Habit</b>", body_style), Paragraph("<b>Logged Days</b>", body_style), Paragraph("<b>Completion Rate</b>", body_style)]
    ]
    for h in habits:
        pct = h["completion_rate"] * 100
        hb_table_data.append([
            Paragraph(h["name"], body_style),
            Paragraph(f"{h['logged_days']} days", body_style),
            Paragraph(f"{pct:.1f}%", body_style)
        ])
        
    t_hb = Table(hb_table_data, colWidths=[200, 150, 150])
    t_hb.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#065f46")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    for i in range(3):
        t_hb.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
        
    elements.append(t_hb)
    elements.append(Spacer(1, 25))
    
    # Footer
    elements.append(Paragraph("<b>Recommendation:</b> Keep logging your daily metrics and matching active challenges to continuously earn XP and improve your score!", body_style))
    
    doc.build(elements)
    
    pdf_buffer.seek(0)
    pdf_data = pdf_buffer.getvalue()
    
    # Return as PDF file attachment response
    filename = f"CarbonTrack_Report_{range_name}_{start_date.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
