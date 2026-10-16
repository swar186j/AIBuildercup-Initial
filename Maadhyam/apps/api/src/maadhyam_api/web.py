"""Optional production SPA serving for a single-origin free demo."""
from pathlib import Path
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class SPAFiles(StaticFiles):
    async def get_response(self, path, scope):
        path = path.replace('\\', '/')
        if any(part.startswith('.') for part in Path(path).parts):
            raise HTTPException(404)
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404)
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or Path(path).suffix:
                raise
            response = await super().get_response('index.html', scope)
        if response.status_code == 404 and not Path(path).suffix:
            response = await super().get_response('index.html', scope)
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable' if path.startswith('assets/') else 'no-cache'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response


def mount_web(app, directory):
    path = Path(directory).resolve()
    if not (path / 'index.html').is_file():
        raise RuntimeError('Build the frontend before enabling MAADHYAM_WEB_DIST')
    app.mount('/', SPAFiles(directory=str(path), html=True), name='web')
