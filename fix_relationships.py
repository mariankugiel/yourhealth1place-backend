#!/usr/bin/env python3
"""
Relationship Fix Script
This script automatically fixes common SQLAlchemy relationship issues.
"""

import os
import re

def fix_relationship_issues():
    """Fix common relationship issues by converting back_populates to backref where appropriate."""
    
    # Common patterns to fix
    fixes = [
        # Convert back_populates to backref for relationships that don't have corresponding back_populates
        (r'back_populates="insights"', 'backref="insights"'),
        (r'back_populates="plan_progress"', 'backref="plan_progress"'),
        (r'back_populates="goals"', 'backref="goals"'),
        (r'back_populates="tasks"', 'backref="tasks"'),
        (r'back_populates="recommendations"', 'backref="recommendations"'),
        (r'back_populates="assignments"', 'backref="assignments"'),
        (r'back_populates="appointments"', 'backref="appointments"'),
        (r'back_populates="messages"', 'backref="messages"'),
        (r'back_populates="tracking"', 'backref="tracking"'),
        (r'back_populates="tracking_details"', 'backref="tracking_details"'),
        (r'back_populates="task_tracking"', 'backref="task_tracking"'),
        (r'back_populates="goal_tracking"', 'backref="goal_tracking"'),
        (r'back_populates="details"', 'backref="details"'),
        (r'back_populates="attachments"', 'backref="attachments"'),
        (r'back_populates="reminders"', 'backref="reminders"'),
        (r'back_populates="document_assignments"', 'backref="document_assignments"'),
        (r'back_populates="slots"', 'backref="slots"'),
        (r'back_populates="pricing"', 'backref="pricing"'),
        (r'back_populates="availability_schedules"', 'backref="availability_schedules"'),
        (r'back_populates="appointment_slots"', 'backref="appointment_slots"'),
        (r'back_populates="locations"', 'backref="locations"'),
        (r'back_populates="practice"', 'backref="practice"'),
        (r'back_populates="sections"', 'backref="sections"'),
        (r'back_populates="metrics"', 'backref="metrics"'),
        (r'back_populates="health_records"', 'backref="health_records"'),
        (r'back_populates="health_data_permissions"', 'backref="health_data_permissions"'),
        (r'back_populates="sync_logs"', 'backref="sync_logs"'),
        (r'back_populates="subscriptions"', 'backref="subscriptions"'),
        (r'back_populates="permissions"', 'backref="permissions"'),
        (r'back_populates="access_logs"', 'backref="access_logs"'),
        (r'back_populates="documents"', 'backref="documents"'),
    ]
    
    models_dir = "app/models"
    files_fixed = 0
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply fixes
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content)
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed += 1
                print(f"Fixed relationships in {filename}")
    
    print(f"\nFixed relationships in {files_fixed} files")

if __name__ == "__main__":
    fix_relationship_issues()
