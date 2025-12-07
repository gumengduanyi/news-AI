import os
import logging


def create_app():
    """App factory that returns the existing Flask app from the monolithic module.

    This keeps backward compatibility while providing a single place to start the
    backend in the new layout. It intentionally imports the original module,
    which defines `app` and all routes.
    """
    # Import here to avoid circular imports at package import time
    try:
        from wechat_report_agent import prompt_qdrant_api
    except Exception:
        # Try relative import fallback when running from the package dir
        import importlib
        prompt_qdrant_api = importlib.import_module('wechat_report_agent.prompt_qdrant_api')

    # Ensure logger level is sane
    logger = logging.getLogger('prompt_qdrant_api')
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)

    # Register newly-migrated blueprints if available
    try:
        from wechat_report_agent.backend.routes.system import system_bp
        prompt_qdrant_api.app.register_blueprint(system_bp)
    except Exception:
        logger.debug('system blueprint not available for registration')

    try:
        from wechat_report_agent.backend.routes.api import api_bp
        prompt_qdrant_api.app.register_blueprint(api_bp)
    except Exception:
        logger.debug('api blueprint not available for registration')

    return prompt_qdrant_api.app
