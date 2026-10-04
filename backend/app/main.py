import logging, os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import Base, engine
from . import models  # noqa: F401
from .routers import auth, contacts, emergencies, facilities

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("medibridge")
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediBridge API", description="Emergency coordination platform. "
              "Informational/coordination use only; not a substitute for emergency services.")
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, contacts.router, emergencies.router, facilities.router):
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
