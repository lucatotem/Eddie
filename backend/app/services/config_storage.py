"""
File-based storage for onboarding configs
Because setting up a DB for this would be overkill... right? RIGHT?
"""

import json
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from app.models.onboarding_config import OnboardingConfigFile, CreateOnboardingRequest, UpdateOnboardingRequest


class OnboardingConfigStorage:
    """Handles CRUD operations for onboarding config files"""
    
    def __init__(self, storage_dir: str = "onboarding"):
        self.storage_dir = Path(storage_dir)
        # Create the folder if it doesn't exist
        self.storage_dir.mkdir(exist_ok=True)
        # TODO: maybe add a .gitkeep file so the folder gets committed?
    
    def _get_file_path(self, config_id: str) -> Path:
        """Get the full path for a config file"""
        return self.storage_dir / f"{config_id}.json"
    
    def _generate_id(self, name: str) -> str:
        """Generate a filesystem-safe ID from the course name"""
        # Convert to lowercase, replace spaces with hyphens
        base_id = name.lower().replace(" ", "-")
        # Remove any weird characters that might break things
        safe_id = "".join(c for c in base_id if c.isalnum() or c == "-")
        
        # Check if this ID already exists, add a number if needed
        if self._get_file_path(safe_id).exists():
            counter = 1
            while self._get_file_path(f"{safe_id}-{counter}").exists():
                counter += 1
            safe_id = f"{safe_id}-{counter}"
        
        return safe_id
    
    def create(self, request: CreateOnboardingRequest) -> OnboardingConfigFile:
        """Create a new onboarding config file"""
        config_id = self._generate_id(request.name)
        
        config = OnboardingConfigFile(
            id=config_id,
            name=request.name,
            emoji=request.emoji,
            color=request.color,
            settings=request.settings,
            instructions=request.instructions,
            linked_pages=request.linked_pages,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to file
        file_path = self._get_file_path(config_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))
        
        return config
    
    def get(self, config_id: str) -> Optional[OnboardingConfigFile]:
        """Get a single config by ID"""
        file_path = self._get_file_path(config_id)
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Use model_validate to properly parse nested models
            return OnboardingConfigFile.model_validate(data)
    
    def list_all(self) -> List[OnboardingConfigFile]:
        """Get all saved configs"""
        configs = []
        
        # Find all .json files in the storage directory
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Use model_validate to properly parse nested models
                    configs.append(OnboardingConfigFile.model_validate(data))
            except Exception as e:
                # Skip corrupted files instead of crashing
                print(f"Warning: Couldn't load {file_path}: {e}")
                continue
        
        # Sort by updated_at, most recent first
        configs.sort(key=lambda x: x.updated_at, reverse=True)
        return configs
    
    def update(self, config_id: str, request: UpdateOnboardingRequest) -> Optional[OnboardingConfigFile]:
        """Update an existing config"""
        config = self.get(config_id)
        if not config:
            return None
        
        # Update only the fields that were provided
        update_data = request.model_dump(exclude_unset=True)
        
        # Special handling for settings to ensure it's properly typed
        if 'settings' in update_data and update_data['settings'] is not None:
            from app.models.onboarding_config import OnboardingSettings
            if isinstance(update_data['settings'], dict):
                update_data['settings'] = OnboardingSettings(**update_data['settings'])
        
        for field, value in update_data.items():
            setattr(config, field, value)
        
        # Update the timestamp
        config.updated_at = datetime.now()
        
        # Save back to file
        file_path = self._get_file_path(config_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))
        
        return config
    
    def delete(self, config_id: str) -> bool:
        """Delete a config file"""
        file_path = self._get_file_path(config_id)
        
        if not file_path.exists():
            return False
        
        file_path.unlink()  # Delete the file
        return True


# Singleton instance - because why make the user pass this around?
_storage = OnboardingConfigStorage()


def get_storage() -> OnboardingConfigStorage:
    """Get the global storage instance"""
    return _storage
