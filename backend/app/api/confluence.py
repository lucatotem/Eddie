from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.confluence_service import confluence_service

router = APIRouter()

class PageResponse(BaseModel):
    id: str
    title: str
    body: Optional[str] = None
    labels: List[str] = []
    space_key: Optional[str] = None

class PageTestResponse(BaseModel):
    """Response for testing page access"""
    success: bool
    page_id: str
    accessible: bool
    error: Optional[str] = None
    details: Optional[dict] = None

@router.get("/test-page/{page_id}", response_model=PageTestResponse)
async def test_page_access(page_id: str):
    """
    Test if a specific page is accessible
    Returns detailed info about why it might not work
    Usage: GET /api/confluence/test-page/123456
    """
    try:
        page = confluence_service.get_page_by_id(page_id)
        
        if page:
            return PageTestResponse(
                success=True,
                page_id=page_id,
                accessible=True,
                details={
                    "title": page.get("title"),
                    "space": page.get("space", {}).get("key"),
                    "url": page.get("_links", {}).get("webui")
                }
            )
        else:
            return PageTestResponse(
                success=False,
                page_id=page_id,
                accessible=False,
                error="Page not found or you don't have access"
            )
    except Exception as e:
        return PageTestResponse(
            success=False,
            page_id=page_id,
            accessible=False,
            error=str(e)
        )

@router.get("/page/{page_id}", response_model=PageResponse)
async def get_page(page_id: str):
    """
    Get a single confluence page
    Usage: GET /api/confluence/page/123456
    """
    page = confluence_service.get_page_by_id(page_id)
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found - check the ID?")
    
    # Transform confluence's weird format into something sane
    labels = [label.get("name", "") for label in page.get("metadata", {}).get("labels", {}).get("results", [])]
    
    return PageResponse(
        id=page["id"],
        title=page["title"],
        body=page.get("body", {}).get("storage", {}).get("value"),
        labels=labels,
        space_key=page.get("space", {}).get("key")
    )

@router.get("/search", response_model=List[PageResponse])
async def search_pages(label: str, limit: int = 50):
    """
    Search pages by label - this is the main way we find role-specific content
    Usage: GET /api/confluence/search?label=dev-onboarding&limit=10
    """
    pages = confluence_service.search_pages_by_label(label, limit)
    
    # Map confluence response to our cleaner format
    results = []
    for page in pages:
        labels = [l.get("name", "") for l in page.get("metadata", {}).get("labels", {}).get("results", [])]
        results.append(PageResponse(
            id=page["id"],
            title=page["title"],
            body=page.get("body", {}).get("storage", {}).get("value"),
            labels=labels
        ))
    
    return results

@router.get("/space/{space_key}", response_model=List[PageResponse])
async def get_space_pages(space_key: str, limit: int = 25):
    """
    Get all pages from a space
    Usage: GET /api/confluence/space/ONBOARD?limit=50
    """
    pages = confluence_service.get_space_pages(space_key, limit)
    
    results = []
    for page in pages:
        results.append(PageResponse(
            id=page["id"],
            title=page["title"],
            body=page.get("body", {}).get("storage", {}).get("value"),
            labels=[]
        ))
    
    return results
