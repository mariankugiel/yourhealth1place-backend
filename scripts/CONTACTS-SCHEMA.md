# Emergency Contacts JSON Schema

## Current Implementation

The emergency contacts are stored in the `user_emergency` table as a JSONB column called `contacts`.

### Contact JSON Structure

Each contact in the array has the following fields:

```json
{
  "name": "John Doe",
  "relationship": "Spouse",
  "phone": "+15551234567",
  "email": "john.doe@example.com"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full name of the emergency contact |
| `relationship` | string | Yes | Relationship to the user (e.g., "Spouse", "Parent", "Friend") |
| `phone` | string | Yes | Complete phone number with country code (e.g., "+15551234567") |
| `email` | string | Optional | Email address of the contact |

### Database Schema

**Table**: `user_emergency`  
**Column**: `contacts` (JSONB)  
**Example**:
```sql
INSERT INTO user_emergency (user_id, contacts)
VALUES (
  'user-uuid-here',
  '[
    {
      "name": "John Doe",
      "relationship": "Spouse",
      "phone": "+15551234567",
      "email": "john.doe@example.com"
    },
    {
      "name": "Jane Smith",
      "relationship": "Mother",
      "phone": "+442076543210",
      "email": "jane.smith@example.com"
    }
  ]'::jsonb
);
```

### Backend API

**POST/PUT** `/api/v1/auth/emergency`

Request body:
```json
{
  "contacts": [
    {
      "name": "John Doe",
      "relationship": "Spouse",
      "phone": "+15551234567",
      "email": "john.doe@example.com"
    }
  ]
}
```

### Frontend TypeScript Interface

```typescript
export interface UserEmergency {
  contacts?: Array<{
    name: string
    relationship: string
    phone: string
    email: string
  }>
  allergies?: string
  medications?: string
  health_problems?: string
  pregnancy_status?: string
  organ_donor?: boolean
}
```

### Backend Pydantic Schema

```python
class UserEmergency(BaseModel):
    contacts: Optional[list[Dict[str, Any]]] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    health_problems: Optional[str] = None
    pregnancy_status: Optional[str] = None
    organ_donor: Optional[bool] = None
```

## Notes

- ✅ **Simple phone storage**: Phone number stored as single string with country code (e.g., "+15551234567")
- ✅ **JSONB storage**: PostgreSQL JSONB provides efficient querying and indexing
- ✅ **Flexible schema**: Easy to add more fields in the future without migrations
- ✅ **Validation**: Frontend uses Zod, backend uses Pydantic for validation
- ✅ **UI Flexibility**: Frontend UI still uses separate country code and phone fields, but combines them when saving

