from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.routes import catalog, trends, analysis, roadmap, account, market_signals

app = FastAPI(title='SkillShift AI — Synthetic Starter', version='0.1.0')

for module in (catalog, trends, analysis, roadmap, account, market_signals):
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
