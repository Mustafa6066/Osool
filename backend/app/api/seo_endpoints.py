"""
SEO Endpoints — Dual-Engine Marketing Platform
-------------------------------------------------
Public (non-auth) endpoints for SEO pages, project listings,
developer profiles, and area guides.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models import (
    Developer, Area, SEOProject, PriceHistory, SEOPage,
    ProjectType, ProjectStatus, SEOPageType, PageStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["SEO & Content"])


# ═══════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class DeveloperOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    slug: str
    founded_year: Optional[int] = None
    total_projects: Optional[int] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    avg_delivery_score: Optional[int] = None
    avg_finish_quality: Optional[int] = None
    avg_resale_retention: Optional[int] = None
    payment_flexibility: Optional[int] = None
    overall_score: Optional[int] = None

    class Config:
        from_attributes = True


class AreaOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    slug: str
    city: Optional[str] = None
    avg_price_per_meter: Optional[float] = None
    price_growth_ytd: Optional[float] = None
    rental_yield: Optional[float] = None
    liquidity_score: Optional[float] = None
    demand_score: Optional[float] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectOut(BaseModel):
    id: int
    slug: str
    name: str
    name_ar: Optional[str] = None
    developer_id: Optional[int] = None
    area_id: Optional[int] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    min_price_per_meter: Optional[float] = None
    max_price_per_meter: Optional[float] = None
    avg_price_per_meter: Optional[float] = None
    down_payment_min: Optional[float] = None
    installment_years: Optional[int] = None
    expected_delivery: Optional[str] = None
    min_unit_size: Optional[float] = None
    max_unit_size: Optional[float] = None
    amenities: Optional[str] = None
    unit_types: Optional[str] = None
    construction_progress: Optional[float] = None
    predicted_roi_1y: Optional[float] = None
    predicted_roi_3y: Optional[float] = None
    predicted_roi_5y: Optional[float] = None

    class Config:
        from_attributes = True


class PriceHistoryOut(BaseModel):
    id: int
    area_id: Optional[int] = None
    project_id: Optional[int] = None
    date: Optional[str] = None
    price_per_m2: Optional[float] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class SEOPageOut(BaseModel):
    id: int
    slug: str
    page_type: str
    status: str
    title: Optional[str] = None
    title_ar: Optional[str] = None
    meta_desc: Optional[str] = None
    content_json: Optional[str] = None
    view_count: Optional[int] = None
    chat_conv_rate: Optional[float] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# DEVELOPERS
# ═══════════════════════════════════════════════════════════════

@router.get("/developers", response_model=List[DeveloperOut])
async def list_developers(
    sort: str = Query("overall_score", pattern="^(name|overall_score|founded_year|total_projects)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all developers with optional sorting."""
    col = getattr(Developer, sort, Developer.overall_score)
    order_col = col.desc() if order == "desc" else col.asc()
    result = await db.execute(select(Developer).order_by(order_col))
    return result.scalars().all()


@router.get("/developers/{slug}", response_model=DeveloperOut)
async def get_developer(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single developer by slug."""
    result = await db.execute(select(Developer).where(Developer.slug == slug))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    return dev


@router.get("/developers/{slug}/projects", response_model=List[ProjectOut])
async def get_developer_projects(slug: str, db: AsyncSession = Depends(get_db)):
    """Get all projects by a developer."""
    dev = await db.execute(select(Developer).where(Developer.slug == slug))
    developer = dev.scalar_one_or_none()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    result = await db.execute(
        select(SEOProject).where(SEOProject.developer_id == developer.id)
    )
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════
# AREAS
# ═══════════════════════════════════════════════════════════════

@router.get("/areas", response_model=List[AreaOut])
async def list_areas(
    city: Optional[str] = None,
    sort: str = Query("avg_price_per_meter", pattern="^(name|avg_price_per_meter|price_growth_ytd|rental_yield)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all areas with optional city filter and sorting."""
    q = select(Area)
    if city:
        q = q.where(Area.city == city)
    col = getattr(Area, sort, Area.avg_price_per_meter)
    order_col = col.desc() if order == "desc" else col.asc()
    result = await db.execute(q.order_by(order_col))
    return result.scalars().all()


@router.get("/areas/{slug}", response_model=AreaOut)
async def get_area(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single area by slug."""
    result = await db.execute(select(Area).where(Area.slug == slug))
    area = result.scalar_one_or_none()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return area


@router.get("/areas/{slug}/projects", response_model=List[ProjectOut])
async def get_area_projects(slug: str, db: AsyncSession = Depends(get_db)):
    """Get all projects in an area."""
    area = await db.execute(select(Area).where(Area.slug == slug))
    area_obj = area.scalar_one_or_none()
    if not area_obj:
        raise HTTPException(status_code=404, detail="Area not found")
    result = await db.execute(
        select(SEOProject).where(SEOProject.area_id == area_obj.id)
    )
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════
# PROJECTS
# ═══════════════════════════════════════════════════════════════

@router.get("/projects", response_model=List[ProjectOut])
async def list_projects(
    area: Optional[str] = None,
    developer: Optional[str] = None,
    project_type: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort: str = Query("name", pattern="^(name|min_price_per_meter|expected_delivery)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List projects with rich filtering."""
    q = select(SEOProject)

    if area:
        sub = select(Area.id).where(Area.slug == area).scalar_subquery()
        q = q.where(SEOProject.area_id == sub)
    if developer:
        sub = select(Developer.id).where(Developer.slug == developer).scalar_subquery()
        q = q.where(SEOProject.developer_id == sub)
    if project_type:
        q = q.where(SEOProject.project_type == project_type)
    if status:
        q = q.where(SEOProject.status == status)
    if min_price is not None:
        q = q.where(SEOProject.min_price_per_meter >= min_price)
    if max_price is not None:
        q = q.where(SEOProject.max_price_per_meter <= max_price)

    col = getattr(SEOProject, sort, SEOProject.name)
    order_col = col.desc() if order == "desc" else col.asc()
    result = await db.execute(q.order_by(order_col).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/projects/{slug}", response_model=ProjectOut)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single project by slug."""
    result = await db.execute(select(SEOProject).where(SEOProject.slug == slug))
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ═══════════════════════════════════════════════════════════════
# PRICE HISTORY
# ═══════════════════════════════════════════════════════════════

@router.get("/price-history/area/{slug}", response_model=List[PriceHistoryOut])
async def get_area_price_history(
    slug: str,
    months: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Get price history for an area."""
    area = await db.execute(select(Area).where(Area.slug == slug))
    area_obj = area.scalar_one_or_none()
    if not area_obj:
        raise HTTPException(status_code=404, detail="Area not found")
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.area_id == area_obj.id)
        .order_by(PriceHistory.date.desc())
        .limit(months)
    )
    return result.scalars().all()


@router.get("/price-history/project/{slug}", response_model=List[PriceHistoryOut])
async def get_project_price_history(
    slug: str,
    months: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Get price history for a project."""
    proj = await db.execute(select(SEOProject).where(SEOProject.slug == slug))
    proj_obj = proj.scalar_one_or_none()
    if not proj_obj:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.project_id == proj_obj.id)
        .order_by(PriceHistory.date.desc())
        .limit(months)
    )
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════
# SEO PAGES
# ═══════════════════════════════════════════════════════════════

@router.get("/pages", response_model=List[SEOPageOut])
async def list_seo_pages(
    page_type: Optional[str] = None,
    status: str = Query("PUBLISHED", pattern="^(DRAFT|PUBLISHED|ARCHIVED)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List SEO pages, default to published only."""
    q = select(SEOPage).where(SEOPage.status == status)
    if page_type:
        q = q.where(SEOPage.page_type == page_type)
    result = await db.execute(q.order_by(SEOPage.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/pages/{slug}", response_model=SEOPageOut)
async def get_seo_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single SEO page by slug."""
    result = await db.execute(select(SEOPage).where(SEOPage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


# ═══════════════════════════════════════════════════════════════
# COMPARISONS (Dynamic)
# ═══════════════════════════════════════════════════════════════

@router.get("/compare/developers/{slug1}/{slug2}")
async def compare_developers(
    slug1: str, slug2: str, db: AsyncSession = Depends(get_db)
):
    """Compare two developers side-by-side."""
    d1 = await db.execute(select(Developer).where(Developer.slug == slug1))
    d2 = await db.execute(select(Developer).where(Developer.slug == slug2))
    dev1 = d1.scalar_one_or_none()
    dev2 = d2.scalar_one_or_none()
    if not dev1 or not dev2:
        raise HTTPException(status_code=404, detail="One or both developers not found")

    # Count active projects per developer
    p1 = await db.execute(
        select(func.count(SEOProject.id)).where(SEOProject.developer_id == dev1.id)
    )
    p2 = await db.execute(
        select(func.count(SEOProject.id)).where(SEOProject.developer_id == dev2.id)
    )

    def dev_dict(d, proj_count):
        return {
            "name": d.name, "name_ar": d.name_ar, "slug": d.slug,
            "founded_year": d.founded_year,
            "total_projects": d.total_projects,
            "listed_projects": proj_count,
            "avg_delivery_score": d.avg_delivery_score,
            "avg_finish_quality": d.avg_finish_quality,
            "avg_resale_retention": d.avg_resale_retention,
            "payment_flexibility": d.payment_flexibility,
            "overall_score": d.overall_score,
        }

    return {
        "developer_1": dev_dict(dev1, p1.scalar()),
        "developer_2": dev_dict(dev2, p2.scalar()),
    }


@router.get("/compare/areas/{slug1}/{slug2}")
async def compare_areas(
    slug1: str, slug2: str, db: AsyncSession = Depends(get_db)
):
    """Compare two areas side-by-side."""
    a1 = await db.execute(select(Area).where(Area.slug == slug1))
    a2 = await db.execute(select(Area).where(Area.slug == slug2))
    area1 = a1.scalar_one_or_none()
    area2 = a2.scalar_one_or_none()
    if not area1 or not area2:
        raise HTTPException(status_code=404, detail="One or both areas not found")

    # Count projects per area
    p1 = await db.execute(
        select(func.count(SEOProject.id)).where(SEOProject.area_id == area1.id)
    )
    p2 = await db.execute(
        select(func.count(SEOProject.id)).where(SEOProject.area_id == area2.id)
    )

    def area_dict(a, proj_count):
        return {
            "name": a.name, "name_ar": a.name_ar, "slug": a.slug,
            "city": a.city,
            "avg_price_per_meter": a.avg_price_per_meter,
            "price_growth_ytd": a.price_growth_ytd,
            "rental_yield": a.rental_yield,
            "project_count": proj_count,
        }

    return {
        "area_1": area_dict(area1, p1.scalar()),
        "area_2": area_dict(area2, p2.scalar()),
    }
