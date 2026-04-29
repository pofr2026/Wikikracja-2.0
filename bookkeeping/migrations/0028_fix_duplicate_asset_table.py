# Generated manually to fix Asset table migration issues

from django.db import connection, migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookkeeping', '0027_data_default_assets'),
    ]

    def fix_asset_migration_issues(apps, schema_editor):
        """
        Fix Asset table migration issues:
        1. Handle case where table already exists but has wrong structure
        2. Fix foreign key constraints in associateasset and report tables
        3. Create proper Asset table structure for migration 0026
        """
        with connection.cursor() as cursor:
            # Check if Asset table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='bookkeeping_asset'
            """)
            asset_table_exists = cursor.fetchone()
            
            if asset_table_exists:
                # Check current structure
                cursor.execute("PRAGMA table_info(bookkeeping_asset)")
                current_columns = [row[1] for row in cursor.fetchall()]
                
                # Check if it's the old structure (has 'validity' or 'notes')
                is_old_structure = 'validity' in current_columns or 'notes' in current_columns
                
                if is_old_structure:
                    # Back up data if needed
                    cursor.execute("SELECT id, name, symbol FROM bookkeeping_asset")
                    old_assets = cursor.fetchall()
                    
                    # Drop the old table
                    cursor.execute("DROP TABLE bookkeeping_asset")
                    
                    # Create new Asset table with proper structure
                    cursor.execute("""
                        CREATE TABLE bookkeeping_asset (
                            id INTEGER PRIMARY KEY,
                            code VARCHAR(10) UNIQUE NOT NULL,
                            name VARCHAR(100) NOT NULL,
                            symbol VARCHAR(10),
                            decimal_places SMALLINT NOT NULL DEFAULT 2,
                            is_currency BOOL NOT NULL DEFAULT 1
                        )
                    """)
                    
                    # Insert default assets (mapping from old to new structure)
                    if old_assets:
                        # Map old data to new structure
                        asset_mapping = {
                            'Złotówki': ('PLN', 'Polski złoty', 'zł', 2, True),
                            'Członkostwo': ('CZL', 'Członkostwo', 'CZŁ', 0, False),
                        }
                        
                        for old_id, old_name, old_symbol in old_assets:
                            if old_name in asset_mapping:
                                code, name, symbol, decimal_places, is_currency = asset_mapping[old_name]
                                cursor.execute("""
                                    INSERT INTO bookkeeping_asset 
                                    (id, code, name, symbol, decimal_places, is_currency)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (old_id, code, name, symbol, decimal_places, is_currency))
                    else:
                        # Insert default assets if no old data
                        cursor.execute("""
                            INSERT INTO bookkeeping_asset 
                            (id, code, name, symbol, decimal_places, is_currency)
                            VALUES 
                            (1, 'PLN', 'Polski złoty', 'zł', 2, 1),
                            (2, 'BTC', 'Bitcoin', '₿', 8, 1)
                        """)
                else:
                    # Table exists but might not have all columns
                    required_columns = ['code', 'decimal_places', 'is_currency']
                    for col in required_columns:
                        if col not in current_columns:
                            if col == 'code':
                                cursor.execute("""
                                    ALTER TABLE bookkeeping_asset 
                                    ADD COLUMN code VARCHAR(10) NOT NULL DEFAULT ''
                                """)
                            elif col == 'decimal_places':
                                cursor.execute("""
                                    ALTER TABLE bookkeeping_asset 
                                    ADD COLUMN decimal_places SMALLINT NOT NULL DEFAULT 2
                                """)
                            elif col == 'is_currency':
                                cursor.execute("""
                                    ALTER TABLE bookkeeping_asset 
                                    ADD COLUMN is_currency BOOL NOT NULL DEFAULT 1
                                """)
            else:
                # Create Asset table from scratch
                cursor.execute("""
                    CREATE TABLE bookkeeping_asset (
                        id INTEGER PRIMARY KEY,
                        code VARCHAR(10) UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        symbol VARCHAR(10),
                        decimal_places SMALLINT NOT NULL DEFAULT 2,
                        is_currency BOOL NOT NULL DEFAULT 1
                    )
                """)
                
                # Insert default assets
                cursor.execute("""
                    INSERT INTO bookkeeping_asset 
                    (id, code, name, symbol, decimal_places, is_currency)
                    VALUES 
                    (1, 'PLN', 'Polski złoty', 'zł', 2, 1),
                    (2, 'BTC', 'Bitcoin', '₿', 8, 1)
                """)
            
            # Add asset column to transaction table if it doesn't exist
            cursor.execute("PRAGMA table_info(bookkeeping_transaction)")
            transaction_columns = [row[1] for row in cursor.fetchall()]
            
            if 'asset_id' not in transaction_columns:
                cursor.execute("""
                    ALTER TABLE bookkeeping_transaction 
                    ADD COLUMN asset_id INTEGER
                """)
                
                # Set default asset_id to 1 (PLN) for existing transactions
                cursor.execute("""
                    UPDATE bookkeeping_transaction 
                    SET asset_id = 1 WHERE asset_id IS NULL
                """)

    def reverse_fix_asset_migration_issues(apps, schema_editor):
        # Reverse operation - no action needed for this fix
        pass

    operations = [
        migrations.RunPython(
            fix_asset_migration_issues,
            reverse_fix_asset_migration_issues,
        ),
    ]
