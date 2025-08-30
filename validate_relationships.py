#!/usr/bin/env python3
"""
Relationship Validation Script
This script validates that all SQLAlchemy relationships are properly defined
and don't have conflicts.
"""

import os
import re
from typing import Dict, List, Set, Tuple

def extract_relationships_from_file(file_path: str) -> Dict[str, List[str]]:
    """Extract all relationships from a Python file."""
    relationships = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all relationship definitions
    relationship_pattern = r'(\w+)\s*=\s*relationship\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*back_populates\s*=\s*["\']([^"\']+)["\'])?\s*(?:,\s*backref\s*=\s*["\']([^"\']+)["\'])?'
    matches = re.findall(relationship_pattern, content)
    
    for match in matches:
        local_name = match[0]
        target_model = match[1]
        back_populates = match[2] if match[2] else None
        backref = match[3] if match[3] else None
        
        if local_name not in relationships:
            relationships[local_name] = []
        
        relationships[local_name].append({
            'target_model': target_model,
            'back_populates': back_populates,
            'backref': backref
        })
    
    return relationships

def validate_relationships(models_dir: str) -> List[str]:
    """Validate all relationships in the models directory."""
    errors = []
    all_relationships = {}
    
    # Collect all relationships from all model files
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)
            file_relationships = extract_relationships_from_file(file_path)
            
            for local_name, rels in file_relationships.items():
                if local_name not in all_relationships:
                    all_relationships[local_name] = []
                all_relationships[local_name].extend(rels)
    
    # Check for conflicts
    for local_name, rels in all_relationships.items():
        for rel in rels:
            if rel['back_populates']:
                # Check if the target model has the corresponding relationship
                target_model = rel['target_model']
                back_populates_name = rel['back_populates']
                
                # Look for the target relationship
                target_found = False
                for other_name, other_rels in all_relationships.items():
                    for other_rel in other_rels:
                        if (other_rel['target_model'] == target_model and 
                            other_name == back_populates_name):
                            target_found = True
                            break
                    if target_found:
                        break
                
                if not target_found:
                    errors.append(f"Missing relationship: {target_model}.{back_populates_name} referenced by {local_name}")
    
    return errors

def main():
    """Main validation function."""
    models_dir = "app/models"
    
    if not os.path.exists(models_dir):
        print(f"Models directory not found: {models_dir}")
        return
    
    print("Validating SQLAlchemy relationships...")
    errors = validate_relationships(models_dir)
    
    if errors:
        print(f"\nFound {len(errors)} relationship errors:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    else:
        print("✅ All relationships are valid!")
        return True

if __name__ == "__main__":
    main()
