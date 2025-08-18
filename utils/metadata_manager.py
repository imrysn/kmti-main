"""
Metadata Management Utility for KMTI File Approval System
Handles metadata file operations in the logs directory
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class MetadataManager:
    """Manages metadata files in the logs directory"""
    
    def __init__(self):
        self.logs_base = r"\\KMTI-NAS\Shared\data\logs\file_metadata"
        self.local_fallback = "data/logs/file_metadata"
        
    def get_metadata_directory(self, team_tag: str, year: str) -> Tuple[bool, str]:
        """
        Get metadata directory path with fallback handling
        Returns (success, directory_path)
        """
        # Try network logs directory first
        network_dir = os.path.join(self.logs_base, team_tag, year)
        
        try:
            os.makedirs(network_dir, exist_ok=True)
            return True, network_dir
        except Exception as e:
            print(f"[METADATA] Network directory unavailable: {e}")
            print(f"[METADATA] Using local fallback directory")
            
            # Fallback to local directory
            local_dir = os.path.join(self.local_fallback, team_tag, year)
            try:
                os.makedirs(local_dir, exist_ok=True)
                return True, local_dir
            except Exception as e2:
                print(f"[METADATA] Error creating local directory: {e2}")
                return False, f"Could not create metadata directory: {e2}"
    
    def save_metadata(self, filename: str, metadata: Dict, team_tag: str, year: str) -> Tuple[bool, str]:
        """
        Save metadata file to logs directory
        Returns (success, message)
        """
        try:
            success, metadata_dir = self.get_metadata_directory(team_tag, year)
            if not success:
                return False, metadata_dir
            
            metadata_filename = f"{os.path.splitext(filename)[0]}.metadata.json"
            metadata_path = os.path.join(metadata_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"[METADATA] Saved metadata: {metadata_path}")
            return True, f"Metadata saved: {metadata_path}"
            
        except Exception as e:
            error_msg = f"Error saving metadata for {filename}: {e}"
            print(f"[METADATA] {error_msg}")
            return False, error_msg
    
    def save_rejected_file_metadata(self, filename: str, metadata: Dict, team_tag: str, year: str) -> Tuple[bool, str]:
        """
        Save metadata file for rejected files to a separate rejected directory
        Returns (success, message)
        """
        try:
            # Create rejected files metadata directory
            rejected_logs_base = os.path.join(self.logs_base.replace("file_metadata", "rejected_files_metadata"))
            rejected_local_fallback = self.local_fallback.replace("file_metadata", "rejected_files_metadata")
            
            # Try network directory first
            network_dir = os.path.join(rejected_logs_base, team_tag, year)
            
            try:
                os.makedirs(network_dir, exist_ok=True)
                metadata_dir = network_dir
            except Exception as e:
                print(f"[REJECTED_METADATA] Network directory unavailable: {e}")
                # Fallback to local directory
                local_dir = os.path.join(rejected_local_fallback, team_tag, year)
                try:
                    os.makedirs(local_dir, exist_ok=True)
                    metadata_dir = local_dir
                except Exception as e2:
                    return False, f"Could not create rejected metadata directory: {e2}"
            
            metadata_filename = f"{os.path.splitext(filename)[0]}.rejected.metadata.json"
            metadata_path = os.path.join(metadata_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"[REJECTED_METADATA] Saved rejected file metadata: {metadata_path}")
            return True, f"Rejected file metadata saved: {metadata_path}"
            
        except Exception as e:
            error_msg = f"Error saving rejected file metadata for {filename}: {e}"
            print(f"[REJECTED_METADATA] {error_msg}")
            return False, error_msg
    
    def load_metadata(self, filename: str, team_tag: str, year: str) -> Dict:
        """
        Load metadata file from logs directory
        Returns metadata dict (empty if not found)
        """
        metadata_filename = f"{os.path.splitext(filename)[0]}.metadata.json"
        
        # Try network directory first
        network_path = os.path.join(self.logs_base, team_tag, year, metadata_filename)
        if os.path.exists(network_path):
            try:
                with open(network_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[METADATA] Error reading network metadata: {e}")
        
        # Try local fallback
        local_path = os.path.join(self.local_fallback, team_tag, year, metadata_filename)
        if os.path.exists(local_path):
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[METADATA] Error reading local metadata: {e}")
        
        print(f"[METADATA] No metadata found for {filename} in {team_tag}/{year}")
        return {}
    
    def get_all_metadata_files(self, team_tag: str, year: str) -> List[Dict]:
        """
        Get all metadata files for a team and year
        Returns list of metadata info dicts
        """
        metadata_files = []
        
        # Check network directory
        network_dir = os.path.join(self.logs_base, team_tag, year)
        if os.path.exists(network_dir):
            try:
                for filename in os.listdir(network_dir):
                    if filename.endswith('.metadata.json'):
                        file_path = os.path.join(network_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                metadata['_metadata_file'] = file_path
                                metadata['_source'] = 'network'
                                metadata_files.append(metadata)
                        except Exception as e:
                            print(f"[METADATA] Error reading {filename}: {e}")
            except Exception as e:
                print(f"[METADATA] Error accessing network metadata directory: {e}")
        
        # Check local fallback
        local_dir = os.path.join(self.local_fallback, team_tag, year)
        if os.path.exists(local_dir):
            try:
                for filename in os.listdir(local_dir):
                    if filename.endswith('.metadata.json'):
                        file_path = os.path.join(local_dir, filename)
                        
                        # Skip if we already have this from network
                        if any(m.get('_metadata_file', '').endswith(filename) for m in metadata_files):
                            continue
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                metadata['_metadata_file'] = file_path
                                metadata['_source'] = 'local'
                                metadata_files.append(metadata)
                        except Exception as e:
                            print(f"[METADATA] Error reading {filename}: {e}")
            except Exception as e:
                print(f"[METADATA] Error accessing local metadata directory: {e}")
        
        return metadata_files
    
    def search_metadata(self, search_criteria: Dict) -> List[Dict]:
        """
        Search metadata files based on criteria
        search_criteria can include: team_tag, year, user_id, approved_by, etc.
        """
        results = []
        
        # Determine search scope
        teams_to_search = [search_criteria['team_tag']] if 'team_tag' in search_criteria else self.get_all_teams()
        years_to_search = [search_criteria['year']] if 'year' in search_criteria else None
        
        for team in teams_to_search:
            if years_to_search is None:
                years = self.get_available_years(team)
            else:
                years = years_to_search
            
            for year in years:
                metadata_files = self.get_all_metadata_files(team, year)
                
                for metadata in metadata_files:
                    # Apply search criteria
                    matches = True
                    
                    for key, value in search_criteria.items():
                        if key.startswith('_'):  # Skip internal keys
                            continue
                        
                        # Handle nested keys (e.g., 'original_submission.user_id')
                        if '.' in key:
                            parts = key.split('.')
                            data = metadata
                            for part in parts:
                                data = data.get(part, {})
                                if not isinstance(data, dict):
                                    break
                            
                            if data != value:
                                matches = False
                                break
                        else:
                            # Direct key search
                            if metadata.get(key) != value:
                                matches = False
                                break
                    
                    if matches:
                        results.append(metadata)
        
        return results
    
    def get_all_teams(self) -> List[str]:
        """Get all teams that have metadata"""
        teams = set()
        
        # Check network directory
        if os.path.exists(self.logs_base):
            try:
                for item in os.listdir(self.logs_base):
                    if os.path.isdir(os.path.join(self.logs_base, item)):
                        teams.add(item)
            except:
                pass
        
        # Check local directory
        if os.path.exists(self.local_fallback):
            try:
                for item in os.listdir(self.local_fallback):
                    if os.path.isdir(os.path.join(self.local_fallback, item)):
                        teams.add(item)
            except:
                pass
        
        return sorted(list(teams))
    
    def get_available_years(self, team_tag: str) -> List[str]:
        """Get available years for a team"""
        years = set()
        
        # Check network directory
        team_dir = os.path.join(self.logs_base, team_tag)
        if os.path.exists(team_dir):
            try:
                for item in os.listdir(team_dir):
                    if os.path.isdir(os.path.join(team_dir, item)) and item.isdigit():
                        years.add(item)
            except:
                pass
        
        # Check local directory
        local_team_dir = os.path.join(self.local_fallback, team_tag)
        if os.path.exists(local_team_dir):
            try:
                for item in os.listdir(local_team_dir):
                    if os.path.isdir(os.path.join(local_team_dir, item)) and item.isdigit():
                        years.add(item)
            except:
                pass
        
        return sorted(list(years), reverse=True)  # Most recent first
    
    def cleanup_old_metadata(self, project_base_dir: str) -> Tuple[int, List[str]]:
        """
        Clean up old metadata files from project directories
        Returns (files_removed, errors)
        """
        files_removed = 0
        errors = []
        
        try:
            if not os.path.exists(project_base_dir):
                return 0, ["Project directory not found"]
            
            for team_name in os.listdir(project_base_dir):
                team_path = os.path.join(project_base_dir, team_name)
                
                if not os.path.isdir(team_path):
                    continue
                
                for year_name in os.listdir(team_path):
                    year_path = os.path.join(team_path, year_name)
                    
                    if not os.path.isdir(year_path) or not year_name.isdigit():
                        continue
                    
                    # Find and remove old metadata files
                    for filename in os.listdir(year_path):
                        if filename.endswith('.metadata.json'):
                            file_path = os.path.join(year_path, filename)
                            try:
                                os.remove(file_path)
                                files_removed += 1
                                print(f"[CLEANUP] Removed old metadata: {file_path}")
                            except Exception as e:
                                error_msg = f"Error removing {file_path}: {e}"
                                errors.append(error_msg)
                                print(f"[CLEANUP] {error_msg}")
        
        except Exception as e:
            errors.append(f"Error during cleanup: {e}")
        
        return files_removed, errors


# Global instance
_metadata_manager = None

def get_metadata_manager() -> MetadataManager:
    """Get global metadata manager instance"""
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = MetadataManager()
    return _metadata_manager

# Convenience functions
def save_file_metadata(filename: str, metadata: Dict, team_tag: str, year: str) -> Tuple[bool, str]:
    """Convenience function to save metadata"""
    return get_metadata_manager().save_metadata(filename, metadata, team_tag, year)

def load_file_metadata(filename: str, team_tag: str, year: str) -> Dict:
    """Convenience function to load metadata"""
    return get_metadata_manager().load_metadata(filename, team_tag, year)

def search_file_metadata(**criteria) -> List[Dict]:
    """Convenience function to search metadata"""
    return get_metadata_manager().search_metadata(criteria)
