import time
from pathlib import Path

import fastapi.responses
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import FileResponse


def run_webserver():
    openwb_root = Path(__file__).parents[2]

    app = FastAPI()

    @app.get("/")
    async def root():
        return fastapi.responses.RedirectResponse("/web/", status.HTTP_303_SEE_OTHER)

    @app.get("/web/")
    async def web_root():
        return FileResponse(openwb_root.joinpath("web", "themes", "standard", "theme.html"))

    @app.get("/sample")
    async def sample():
        return f"Hello world! Time is {time.time()}"

    app.mount("/web", StaticFiles(directory=openwb_root / "web", html=True), name="static")
    uvicorn.run(app, host="0.0.0.0", port=80)
