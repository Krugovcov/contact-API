from ipaddress import ip_address
import re
from typing import Callable
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.database.db import get_db
from src.routes import contacts, auth, users
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.conf import config

app = FastAPI()

banned_ips = [ip_address("192.168.1.1"), ip_address("192.168.1.2")]
user_agent_ban_list = [r"bot-Yandex", r"Python-urllib", r"Googlebot"]
origin = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#@app.middleware("http")
#async def ban_ips(request:Request, call_next: Callable):
    #ip = ip_address(request.client.host)
    #if ip in banned_ips:
        #return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
    #response = await call_next(request)

@app.middleware("http")
async def user_agent_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get("User-Agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "User agent is banned"})
    response = await call_next(request)
    return response

app.mount("/static", StaticFiles(directory="src/static"), name="static")                                                                                            
app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')

templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "our":"Build anything you want with Tajoco"})

@app.on_event("startup")
async def startup():
    r = await Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, decode_responses=True, password=config.REDIS_PASSWORD)
    await FastAPILimiter.init(r)

@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result=result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")