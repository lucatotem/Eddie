"""
Check Confluence page content
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.confluence_service import ConfluenceService

def main():
    # Load credentials from environment
    from app.config import get_settings
    settings = get_settings()
    
    confluence_url = settings.confluence_url
    confluence_email = settings.confluence_user_email
    confluence_api_token = settings.confluence_api_token
    
    if not all([confluence_url, confluence_email, confluence_api_token]):
        print("❌ Missing Confluence credentials in environment")
        print(f"URL: {confluence_url}")
        print(f"Email: {confluence_email}")
        print(f"Token: {'*' * len(confluence_api_token) if confluence_api_token else 'MISSING'}")
        return
    
    service = ConfluenceService()
    
    # Page IDs from config
    page_ids = ["131421", "131440"]
    
    for page_id in page_ids:
        print(f"\n{'='*60}")
        print(f"PAGE {page_id}")
        print(f"{'='*60}")
        
        page = service.get_page_by_id(page_id)
        if page:
            print(f"Title: {page['title']}")
            print(f"Keys: {list(page.keys())}")
            
            # Get plain text content
            import html2text
            content_html = page.get('body', {}).get('storage', {}).get('value', page.get('content', ''))
            
            # Use html2text to convert to plain text
            h = html2text.HTML2Text()
            h.ignore_links = False
            clean_text = h.handle(content_html)
            
            print(f"\nContent ({len(clean_text)} chars):")
            print(clean_text)
        else:
            print(f"❌ Failed to fetch page")

if __name__ == "__main__":
    main()
