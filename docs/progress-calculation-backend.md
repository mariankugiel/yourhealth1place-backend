# Backend Progress Calculation System Implementation

## Overview

This document describes the backend implementation of the comprehensive progress calculation system for health goals, supporting `below` and `above` target operators.

## Database Schema Changes

### Updated Goal Model (`health_plans.py`)

```python
class Goal(Base):
    __tablename__ = "health_plan_goals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    connected_metric_id = Column(Integer, ForeignKey("health_record_metrics.id"))
    
    # New progress calculation fields
    target_operator = Column(String(20), default='equal')  # "below" or "above"
    target_value = Column(Numeric(10, 2))  # Target value for the goal
    baseline_value = Column(Numeric(10, 2))  # Starting value when goal was created
    current_value = Column(Numeric(10, 2))  # Latest recorded value
    progress_percentage = Column(Integer, default=0)  # Calculated progress percentage
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
```

### Database Migration

Migration file: `0015_add_progress_calculation_fields.py`

Adds the following columns to `health_plan_goals` table:
- `target_operator` (VARCHAR(20), default: 'equal')
- `target_value` (NUMERIC(10,2))
- `baseline_value` (NUMERIC(10,2))
- `current_value` (NUMERIC(10,2))
- `progress_percentage` (INTEGER, default: 0)

## API Endpoints Updates

### 1. GET /health-goals

**Updated Response Structure:**
```json
{
  "id": 1,
  "name": "Lose weight",
  "target": {
    "operator": "below",
    "value": 90.0
  },
  "current": {
    "value": 98.0,
    "status": "normal",
    "unit": "kg"
  },
  "baseline_value": 100.0,
  "progress": 20,
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "created_at": "2024-01-01T00:00:00Z",
  "metric_id": 1
}
```

**Features:**
- Automatically calculates progress when retrieving goals
- Updates `current_value` and `progress_percentage` in database
- Handles missing baseline values gracefully

### 2. POST /health-goals

**Updated Request Structure:**
```json
{
  "name": "Lose weight",
  "metric_id": 1,
  "target": {
    "operator": "below",
    "value": 90.0
  },
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

**Features:**
- Automatically captures baseline value from current metric value
- Stores target operator and value separately
- Initializes progress at 0%

### 3. PUT /health-goals/{goal_id}

**Updated Request Structure:**
```json
{
  "name": "Updated goal name",
  "target": {
    "operator": "above",
    "value": 10000.0
  }
}
```

**Features:**
- Updates target operator and value
- Maintains baseline value (not updated)
- Recalculates progress on next retrieval

### 4. POST /health-goals/{goal_id}/update-progress

**New Endpoint for Manual Progress Updates**

**Response:**
```json
{
  "id": 1,
  "progress": 45,
  "current_value": 95.0,
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Features:**
- Manually triggers progress recalculation
- Updates current value from latest health record
- Useful for real-time progress updates

## Progress Calculation Logic

### Backend Implementation

```python
def calculate_progress(current_value: float, target_value: float, target_operator: str, baseline_value: float = None) -> int:
    """
    Calculate progress percentage for health goals
    
    Args:
        current_value: Current metric value
        target_value: Target value for the goal
        target_operator: "below" or "above"
        baseline_value: Starting value when goal was created
    
    Returns:
        Progress percentage (0-100)
    """
```

### Calculation Examples

#### Below Operator (Weight Loss)
- Goal: "Below 90kg"
- Baseline: 100kg
- Current: 98kg
- Progress: (100-98)/(100-90) × 100 = 20%

#### Above Operator (Steps)
- Goal: "Above 10000 steps"
- Baseline: 5000 steps
- Current: 8500 steps
- Progress: (8500-5000)/(10000-5000) × 100 = 70%

## Data Flow

### 1. Goal Creation
1. User creates goal with target operator and value
2. System captures current metric value as baseline
3. Goal stored with baseline_value and progress_percentage = 0

### 2. Progress Updates
1. User updates health record (metric value)
2. System retrieves latest value for goal's metric
3. Progress calculated using baseline, current, and target values
4. Goal updated with new current_value and progress_percentage

### 3. Goal Retrieval
1. System fetches goal data
2. Retrieves latest metric value
3. Calculates current progress
4. Updates goal in database
5. Returns goal with current progress

## Error Handling

### Missing Data
- Missing baseline value: Estimates baseline from current and target values
- Missing current value: Returns 0% progress
- Missing target value: Returns 0% progress

### Invalid Data
- Invalid target operator: Defaults to 'equal' (0% progress)
- Non-numeric values: Returns 0% progress
- Division by zero: Returns 0% progress

## Benefits

1. **Accurate Progress Tracking**: Uses baseline values for meaningful progress calculation
2. **Flexible Target Types**: Supports both "below" and "above" operators
3. **Real-time Updates**: Progress automatically updates when health records change
4. **Database Efficiency**: Stores calculated progress to avoid repeated calculations
5. **Backward Compatibility**: Maintains existing API structure while adding new features

## Future Enhancements

1. **Batch Progress Updates**: Update progress for all goals at once
2. **Progress History**: Track progress changes over time
3. **Goal Completion Detection**: Automatically mark goals as completed at 100%
4. **Progress Notifications**: Alert users when significant progress is made
5. **Goal Recommendations**: Suggest new goals based on progress patterns
