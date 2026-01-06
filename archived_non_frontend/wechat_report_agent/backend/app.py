import os
import logging
import pkgutil
import importlib
from flask import Flask


def create_app():
    """Create an independent Flask app for the backend package.

    This factory no longer depends on the old monolithic module. It will
    register any available blueprints under `backend.routes` and provide a
    minimal CORS after_request hook similar to the original app so local
    frontends keep working.
    """
    app = Flask(__name__)

    # Minimal structured logger
    logger = logging.getLogger('backend.app')
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)

    # Load instance config into env if present (best-effort, non-fatal)
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        inst = os.path.join(base, '..', 'instance', 'config.json')
        inst = os.path.abspath(inst)
        if os.path.exists(inst):
            import json
            with open(inst, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in cfg.items():
                if isinstance(v, str) and not os.environ.get(k):
                    os.environ[k] = v
            logger.info('Loaded instance config from %s', inst)
    except Exception:
        logger.debug('no instance config loaded')

    # tiny CORS-like after_request to keep compatibility with local UI
    @app.after_request
    def _add_cors_headers(response):
        allowed_origin = os.environ.get('ALLOW_ORIGIN', '*')
        response.headers['Access-Control-Allow-Origin'] = allowed_origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type,Accept,Origin,User-Agent'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        response.headers['Access-Control-Expose-Headers'] = 'X-AI-COUNTS'
        return response

    # Register any blueprints found under `backend.routes` (best-effort).
    # Will attempt to import every module in the `routes` directory and
    # register the first blueprint-like attribute it finds.
    try:
        routes_dir = os.path.join(os.path.dirname(__file__), 'routes')
        pkg_prefix = 'wechat_report_agent.backend.routes'
        for finder, modname, ispkg in pkgutil.iter_modules([routes_dir]):
            if modname.startswith('_'):
                continue
            module_name = f'{pkg_prefix}.{modname}'
            try:
                mod = importlib.import_module(module_name)
            except Exception as e:
                logger.debug('failed to import %s: %s', module_name, e)
                continue

            # common blueprint attribute names used in this package
            candidates = ('bp', 'blueprint', f'{modname}_bp', f'{modname}_blueprint', 'api_bp', 'system_bp')
            registered = False
            for attr in candidates:
                bp = getattr(mod, attr, None)
                if bp is not None:
                    try:
                        app.register_blueprint(bp)
                        logger.info('Registered blueprint %s from %s', attr, module_name)
                        registered = True
                        break
                    except Exception as e:
                        logger.debug('failed to register blueprint %s from %s: %s', attr, module_name, e)
            if not registered:
                logger.debug('no blueprint found in %s', module_name)
    except Exception as e:
        logger.debug('blueprint scan failed: %s', e)

    return app
