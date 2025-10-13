"""replace Child with Son and Daughter in familyrelation enum

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    # The database has UPPERCASE enum values, so we need to work with that
    # Strategy: Add SON and DAUGHTER to existing enum, keep everything uppercase
    
    # Since migrations 0009 already added 'Son' and 'Daughter', we need to add uppercase versions
    # and normalize the data
    
    # Step 1: Convert relation column to TEXT type temporarily
    op.execute("ALTER TABLE family_medical_history ALTER COLUMN relation TYPE TEXT")
    
    # Step 2: Normalize all values to UPPERCASE (matching existing enum)
    op.execute("""
        UPDATE family_medical_history 
        SET relation = UPPER(relation)
    """)
    
    # Step 3: Convert CHILD to SON
    op.execute("""
        UPDATE family_medical_history 
        SET relation = 'SON' 
        WHERE relation = 'CHILD'
    """)
    
    # Step 4: Drop old enum completely
    op.execute("DROP TYPE IF EXISTS familyrelation CASCADE")
    
    # Step 5: Create new enum type with uppercase values (no CHILD, with SON and DAUGHTER)
    op.execute("""
        CREATE TYPE familyrelation AS ENUM (
            'FATHER',
            'MOTHER', 
            'BROTHER',
            'SISTER',
            'SON',
            'DAUGHTER',
            'MATERNAL_GRANDFATHER',
            'MATERNAL_GRANDMOTHER',
            'PATERNAL_GRANDFATHER',
            'PATERNAL_GRANDMOTHER'
        )
    """)
    
    # Step 6: Convert column back to enum type
    op.execute("""
        ALTER TABLE family_medical_history 
        ALTER COLUMN relation TYPE familyrelation 
        USING relation::familyrelation
    """)


def downgrade():
    # Reverse the process
    
    # Step 1: Convert column to TEXT
    op.execute("ALTER TABLE family_medical_history ALTER COLUMN relation TYPE TEXT")
    
    # Step 2: Update Son/Daughter back to Child
    op.execute("""
        UPDATE family_medical_history 
        SET relation = 'Child' 
        WHERE relation IN ('Son', 'Daughter')
    """)
    
    # Step 3: Create old enum type with Child
    op.execute("""
        CREATE TYPE familyrelation_old AS ENUM (
            'Father',
            'Mother',
            'Brother',
            'Sister',
            'Child',
            'Maternal Grandfather',
            'Maternal Grandmother',
            'Paternal Grandfather',
            'Paternal Grandmother'
        )
    """)
    
    # Step 4: Alter column to use old type
    op.execute("""
        ALTER TABLE family_medical_history 
        ALTER COLUMN relation TYPE familyrelation_old 
        USING relation::familyrelation_old
    """)
    
    # Step 5: Drop new type and rename old one
    op.execute("DROP TYPE IF EXISTS familyrelation")
    op.execute("ALTER TYPE familyrelation_old RENAME TO familyrelation")

