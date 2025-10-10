import requests
from typing import List, Dict, Optional
from app.config import get_settings
import re

settings = get_settings()

class ConfluenceService:
    """
    Service for talking to Confluence API
    
    Handles fetching pages, searching, and dealing with folder structures.
    """
    
    def __init__(self):
        # confluence URLs are confusing, some have /wiki some don't 🤷
        base = settings.confluence_url.rstrip('/')
        
        # try not to double up the /wiki part
        if '/wiki' in base:
            self.base_url = f"{base}/rest/api"
        else:
            self.base_url = f"{base}/wiki/rest/api"
            
        self.auth = (settings.confluence_user_email, settings.confluence_api_token)
        self.headers = {"Accept": "application/json"}
        
        print(f"[Confluence] API initialized: {self.base_url}")
    
    def get_page_by_id(self, page_id: str) -> Optional[Dict]:
        """Fetch a single page from Confluence by ID"""
        url = f"{self.base_url}/content/{page_id}"
        params = {"expand": "body.storage,metadata.labels,space"}
        
        print(f"\n[DEBUG] Fetching page {page_id}")
        print(f"   URL: {url}")
        print(f"   Auth: {self.auth[0]} (token length: {len(self.auth[1])})")
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            print(f"   Status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"   ERROR: {e}")
            print(f"   Response: {response.text if 'response' in locals() else 'No response'}")
            return None
    
    def search_pages_by_label(self, label: str, limit: int = 50) -> List[Dict]:
        """
        Search pages by label - this is how we filter by role
        Returns a list of pages or empty list if something breaks
        """
        url = f"{self.base_url}/content/search"
        # CQL is basically SQL but for confluence and somehow worse
        cql = f'label="{label}" AND type=page'
        params = {
            "cql": cql,
            "expand": "body.storage,metadata.labels",
            "limit": limit
        }
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Search failed: {e}")
            return []
    
    def get_space_pages(self, space_key: str, limit: int = 25) -> List[Dict]:
        """Get all pages from a space - useful for bulk operations"""
        url = f"{self.base_url}/content"
        params = {
            "spaceKey": space_key,
            "type": "page",
            "limit": limit,
            "expand": "body.storage"
        }
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Failed to get space pages: {e}")
            return []
    
    def extract_linked_page_ids(self, html_content: str) -> List[str]:
        """
        Extract linked Confluence page IDs from HTML content
        Looks for confluence page links in the HTML
        """
        # Confluence links look like: /wiki/spaces/SPACE/pages/123456/Page+Title
        # or /pages/123456 in internal links
        page_id_pattern = r'/pages/(\d+)'
        matches = re.findall(page_id_pattern, html_content)
        return list(set(matches))  # Remove duplicates
    
    def get_child_pages(self, parent_page_id: str, recursive: bool = True) -> List[str]:
        """
        Get all child pages under a parent (like a folder)
        If recursive=True, goes deep into subfolders too
        """
        url = f"{self.base_url}/content/{parent_page_id}/child/page"
        params = {"limit": 100}  # Should be enough for most folders
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            child_ids = []
            for child in data.get("results", []):
                child_ids.append(child["id"])
                
                # Go deeper if recursive (folder within folder)
                if recursive:
                    grandchildren = self.get_child_pages(child["id"], recursive=True)
                    child_ids.extend(grandchildren)
            
            return child_ids
        except requests.exceptions.RequestException as e:
            print(f"Failed to get child pages for {parent_page_id}: {e}")
            return []
    
    def is_page_a_folder(self, page_id: str) -> bool:
        """
        Check if a page has child pages (basically a folder)
        Not a real folder, but confluence doesn't have those so... 🤷
        """
        url = f"{self.base_url}/content/{page_id}/child/page"
        params = {"limit": 1}  # Just need to know if ANY exist
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return len(data.get("results", [])) > 0
        except:
            return False
    
    def get_onboarding_config(self, config_page_id: str, recursive_folders: bool = True) -> Optional[Dict]:
        """
        Get an onboarding configuration from a Confluence page
        The page should contain:
        - Instructions for the role
        - Links to pages OR folders (pages with children) that contain the learning material
        
        If a linked page has children, we grab all of them too
        """
        page = self.get_page_by_id(config_page_id)
        if not page:
            return None
        
        body_html = page.get("body", {}).get("storage", {}).get("value", "")
        
        # Extract directly linked page IDs
        linked_page_ids = self.extract_linked_page_ids(body_html)
        
        # Expand any "folders" (pages with children)
        all_source_ids = []
        for page_id in linked_page_ids:
            all_source_ids.append(page_id)  # Add the page itself
            
            # Check if it has children (is a folder)
            children = self.get_child_pages(page_id, recursive=recursive_folders)
            if children:
                # It's a folder! Get all pages inside
                all_source_ids.extend(children)
        
        # Remove duplicates (in case someone linked both a folder and a page inside it)
        all_source_ids = list(set(all_source_ids))
        
        return {
            "id": page["id"],
            "title": page["title"],
            "instructions": body_html,
            "source_page_ids": all_source_ids,
            "labels": [label.get("name", "") for label in page.get("metadata", {}).get("labels", {}).get("results", [])]
        }
    
    def get_all_onboarding_configs(self, label: str = "onboarding-config") -> List[Dict]:
        """
        Get all onboarding configurations
        These are special pages labeled as onboarding configs
        """
        pages = self.search_pages_by_label(label)
        configs = []
        
        for page in pages:
            body_html = page.get("body", {}).get("storage", {}).get("value", "")
            linked_page_ids = self.extract_linked_page_ids(body_html)
            
            # Expand folders
            all_source_ids = []
            for page_id in linked_page_ids:
                all_source_ids.append(page_id)
                children = self.get_child_pages(page_id, recursive=True)
                all_source_ids.extend(children)
            
            all_source_ids = list(set(all_source_ids))
            
            configs.append({
                "id": page["id"],
                "title": page["title"],
                "instructions": body_html,
                "source_page_ids": all_source_ids,
                "labels": [label.get("name", "") for label in page.get("metadata", {}).get("labels", {}).get("results", [])]
            })
        
        return configs

# Singleton pattern - fancy way of saying "only create this once"
confluence_service = ConfluenceService()
