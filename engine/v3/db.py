"""
Supabase client for V3 engine.
All DB access goes through this module.
"""

import os
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get(
    "V3_SUPABASE_URL", "https://rndfpyuuredtqncegygi.supabase.co"
)
SUPABASE_SERVICE_KEY = os.environ.get(
    "V3_SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI",
)

_client = None


def get_client():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client
