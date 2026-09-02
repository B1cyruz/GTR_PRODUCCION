import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtr_project.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='details_json') THEN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='details') THEN
                    ALTER TABLE audit_logs RENAME COLUMN details TO details_json;
                ELSE
                    ALTER TABLE audit_logs ADD COLUMN details_json TEXT;
                END IF;
            END IF;
        END $$;
    """)
    print("Column details_json verified/created successfully.")
