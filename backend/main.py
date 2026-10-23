from pathlib import Path
import os
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from backend.security import ApiSecurityMiddleware
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.routes import catalog, trends, analysis, roadmap, account, market_signals, what_if

# Explicitly opt into production hardening; local Vite/FastAPI development keeps
# the interactive OpenAPI docs for debugging.
APP_ENV = os.getenv('APP_ENV', 'development').strip().lower()
# Fail closed on typos like APP_ENV=prod instead of silently disabling
# production-only controls (host restrictions and hidden API docs).
if APP_ENV not in {'development', 'testing', 'production'}:
    raise RuntimeError('APP_ENV must be development, testing, or production')
PRODUCTION = APP_ENV == 'production'
allowed_hosts = [host.strip().lower() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
if PRODUCTION:
    import re
    if (not allowed_hosts or any(not re.fullmatch(
            r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', host
        ) for host in allowed_hosts)):
        raise RuntimeError('Production requires explicit, exact ALLOWED_HOSTS hostnames without wildcards or ports')
if PRODUCTION and os.getenv('AI_ENABLED', 'false').strip().lower() in {'true', 'yes', 'on', '1'}:
    if not os.getenv('AI_QUOTA_DB_PATH', '').strip():
        raise RuntimeError('Production AI requires an explicit, persistent AI_QUOTA_DB_PATH')

app = FastAPI(
    title='SkillShift AI', version='0.1.0',
    docs_url=None if PRODUCTION else '/docs',
    redoc_url=None if PRODUCTION else '/redoc',
    openapi_url=None if PRODUCTION else '/openapi.json',
)
app.add_middleware(ApiSecurityMiddleware)
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts, www_redirect=False)

for module in (catalog, trends, analysis, roadmap, account, market_signals, what_if):
    app.include_router(module.router)

@app.get('/api/health')
def health():
    return {'status':'ok', 'project':'skillshift-ai', 'stage':'starter_scaffold'}

frontend_dist = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if frontend_dist.is_dir():
    app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='frontend')
else:
    @app.get('/', response_class=HTMLResponse)
    def home():
        return '<h1>SkillShift backend is running</h1><p>Build frontend or run Vite locally.</p><a href="/docs">FastAPI docs</a>'
