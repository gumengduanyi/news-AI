# backend package for reorganized helpers
# Expose components for gradual migration
from .auth import require_token, write_instance_config
from .db import get_db_conn, init_db_if_needed, row_to_dict
from .docx_utils import simple_generate_docx
from .ai_utils import normalize_ai_content_for_render, ensure_structured_ai_response, sanitize_ai_content, _last_ai_debug
