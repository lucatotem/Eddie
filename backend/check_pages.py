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
            
            # Get plain text content
            from bs4 import BeautifulSoup
            content_html = page['content']
            soup = BeautifulSoup(content_html, 'html.parser')
            clean_text = soup.get_text(separator='\n', strip=True)
            
            print(f"\nContent ({len(clean_text)} chars):")
            print(clean_text)
        else:
            print(f"❌ Failed to fetch page")

if __name__ == "__main__":
    main()
