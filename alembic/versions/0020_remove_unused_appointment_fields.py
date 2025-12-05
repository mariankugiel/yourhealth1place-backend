"""Remove unused appointment fields and document virtual meeting URL storage

Revision ID: 0020
Revises: ac6540543e78
Create Date: 2025-01-27 12:00:00.000000

This migration removes all unused fields from appointments table since we're using Acuity as the source of truth.
Removed fields:
- appointment_type_id (we use Acuity appointment types)
- location_id (we get location from Acuity if needed)
- appointment_type_pricing_id (pricing comes from Acuity)
- appointment_category (derived from Acuity appointment type category)
- booked_by, booked_at, booking_notes (use created_by, created_at)
- reason, symptoms, diagnosis, treatment_plan, prescription (clinical notes, not in Acuity)
- private_notes (not in Acuity)
- medical_condition_updates (not in Acuity)
- follow_up_required, follow_up_date, follow_up_notes (not in Acuity)
- manual_appointment_id (only if manual appointments are supported)
- stripe_payment_intent_id, stripe_charge_id (only if we process payments)
- related_document_ids (can be handled separately)
- virtual_meeting_password (Daily.co doesn't use passwords)
- virtual_meeting_id, virtual_meeting_platform (not needed, room name derived from acuity_appointment_id)
- health_plan_id (not used)

Also:
- Adds acuity_appointment_type_id to store Acuity's appointment type ID
- Documents that virtual_meeting_url is now stored in DB instead of Acuity custom fields

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = 'ac6540543e78'
branch_labels = None
depends_on = None


def upgrade():
    """Remove all unused fields from appointments table"""
    
    # Check if the appointments table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'appointments' not in inspector.get_table_names():
        print("appointments table does not exist, skipping migration")
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('appointments')]
    
    # List of fields to remove
    fields_to_remove = [
        'appointment_type_id',
        'location_id',
        'appointment_type_pricing_id',
        'appointment_category',
        'booked_by',
        'booked_at',
        'booking_notes',
        'reason',
        'symptoms',
        'diagnosis',
        'treatment_plan',
        'prescription',
        'private_notes',
        'medical_condition_updates',
        'follow_up_required',
        'follow_up_date',
        'follow_up_notes',
        'manual_appointment_id',
        'stripe_payment_intent_id',
        'stripe_charge_id',
        'related_document_ids',
        'virtual_meeting_password',
        'virtual_meeting_id',
        'virtual_meeting_platform',
        'health_plan_id'  # Already commented out but remove if exists
    ]
    
    # Drop foreign key constraints first if they exist
    # Get foreign keys
    fk_constraints = []
    try:
        fks = inspector.get_foreign_keys('appointments')
        for fk in fks:
            if fk['constrained_columns']:
                col_name = fk['constrained_columns'][0]
                if col_name in fields_to_remove:
                    fk_constraints.append({
                        'name': fk['name'],
                        'column': col_name
                    })
    except Exception as e:
        print(f"Warning: Could not get foreign keys: {e}")
    
    # Drop foreign key constraints
    for fk in fk_constraints:
        try:
            print(f"Dropping foreign key constraint '{fk['name']}' on column '{fk['column']}'...")
            op.drop_constraint(fk['name'], 'appointments', type_='foreignkey')
        except Exception as e:
            print(f"Warning: Could not drop foreign key {fk['name']}: {e}")
    
    # Remove columns
    for field in fields_to_remove:
        if field in columns:
            print(f"Dropping '{field}' column from appointments table...")
            try:
                op.drop_column('appointments', field)
            except Exception as e:
                print(f"Warning: Could not drop column {field}: {e}")
    
    # Ensure virtual_meeting_url exists and is nullable
    if 'virtual_meeting_url' not in columns:
        print("Adding 'virtual_meeting_url' column to appointments table...")
        op.add_column('appointments', 
                     sa.Column('virtual_meeting_url', sa.Text(), nullable=True))
    
    # Add acuity_appointment_type_id if it doesn't exist
    if 'acuity_appointment_type_id' not in columns:
        print("Adding 'acuity_appointment_type_id' column to appointments table...")
        op.add_column('appointments', 
                     sa.Column('acuity_appointment_type_id', sa.String(length=255), nullable=True))
    
    # Add location column if it doesn't exist
    if 'location' not in columns:
        print("Adding 'location' column to appointments table...")
        op.add_column('appointments', 
                     sa.Column('location', sa.Text(), nullable=True))
    
    print("✅ Migration complete: Removed all unused fields, added acuity_appointment_type_id and location, virtual meeting info now stored in DB")


def downgrade():
    """Add back the removed columns (for rollback purposes)"""
    
    # Check if the appointments table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'appointments' not in inspector.get_table_names():
        print("appointments table does not exist, skipping rollback")
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('appointments')]
    
    # Add back removed columns
    fields_to_add = {
        'appointment_type_id': sa.Column('appointment_type_id', sa.Integer(), sa.ForeignKey('appointment_types.id'), nullable=True),
        'location_id': sa.Column('location_id', sa.Integer(), sa.ForeignKey('professional_locations.id'), nullable=True),
        'appointment_type_pricing_id': sa.Column('appointment_type_pricing_id', sa.Integer(), sa.ForeignKey('appointment_type_pricing.id'), nullable=True),
        'appointment_category': sa.Column('appointment_category', sa.String(length=50), nullable=True),
        'booked_by': sa.Column('booked_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        'booked_at': sa.Column('booked_at', sa.DateTime(), nullable=True),
        'booking_notes': sa.Column('booking_notes', sa.Text(), nullable=True),
        'reason': sa.Column('reason', sa.Text(), nullable=True),
        'symptoms': sa.Column('symptoms', sa.Text(), nullable=True),
        'diagnosis': sa.Column('diagnosis', sa.Text(), nullable=True),
        'treatment_plan': sa.Column('treatment_plan', sa.Text(), nullable=True),
        'prescription': sa.Column('prescription', sa.Text(), nullable=True),
        'private_notes': sa.Column('private_notes', sa.Text(), nullable=True),
        'medical_condition_updates': sa.Column('medical_condition_updates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        'follow_up_required': sa.Column('follow_up_required', sa.Boolean(), nullable=True),
        'follow_up_date': sa.Column('follow_up_date', sa.Date(), nullable=True),
        'follow_up_notes': sa.Column('follow_up_notes', sa.Text(), nullable=True),
        'manual_appointment_id': sa.Column('manual_appointment_id', sa.Integer(), sa.ForeignKey('manual_appointments.id'), nullable=True),
        'stripe_payment_intent_id': sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        'stripe_charge_id': sa.Column('stripe_charge_id', sa.String(length=255), nullable=True),
        'related_document_ids': sa.Column('related_document_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        'virtual_meeting_password': sa.Column('virtual_meeting_password', sa.String(length=100), nullable=True),
        'virtual_meeting_id': sa.Column('virtual_meeting_id', sa.String(length=255), nullable=True),
        'virtual_meeting_platform': sa.Column('virtual_meeting_platform', sa.String(length=50), nullable=True),
        'health_plan_id': sa.Column('health_plan_id', sa.Integer(), nullable=True)
    }
    
    for field_name, column_def in fields_to_add.items():
        if field_name not in columns:
            print(f"Adding back '{field_name}' column to appointments table...")
            try:
                op.add_column('appointments', column_def)
            except Exception as e:
                print(f"Warning: Could not add column {field_name}: {e}")
    
    # Remove location column if it exists
    if 'location' in columns:
        print("Removing 'location' column from appointments table...")
        try:
            op.drop_column('appointments', 'location')
        except Exception as e:
            print(f"Warning: Could not drop column location: {e}")
    
    # Remove acuity_appointment_type_id column if it exists
    if 'acuity_appointment_type_id' in columns:
        print("Removing 'acuity_appointment_type_id' column from appointments table...")
        try:
            op.drop_column('appointments', 'acuity_appointment_type_id')
        except Exception as e:
            print(f"Warning: Could not drop column acuity_appointment_type_id: {e}")
    
    print("✅ Rollback complete: Added back removed fields, removed location and acuity_appointment_type_id")
