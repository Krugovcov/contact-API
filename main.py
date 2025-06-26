from ipaddress import ip_address
import re
from pathlib import Path
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

BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src", "static")

app.mount("/static", StaticFiles(directory=directory), name="static")                                                                                            
app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')

templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Handles the root endpoint by rendering the 'index.html' template with a custom context.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        TemplateResponse: The rendered HTML response for the index page.
    """
    return templates.TemplateResponse("index.html", {"request": request, "our":"Build anything you want with Tajoco"})

@app.on_event("startup")
async def startup():
    """
    Asynchronous startup function to initialize the Redis connection and configure FastAPILimiter.

    This function creates an asynchronous Redis client using configuration parameters
    for host, port, database, and password. It then initializes the FastAPILimiter
    with the Redis client to enable rate limiting in the FastAPI application.

    Raises:
        RedisError: If the connection to the Redis server fails.
    """
    r = await Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, decode_responses=True, password=config.REDIS_PASSWORD)
    await FastAPILimiter.init(r)

@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Performs a health check on the database connection.

    This asynchronous function attempts to execute a simple SQL query ("SELECT 1") to verify that the database is accessible and properly configured. If the query executes successfully and returns a result, a welcome message is returned. If the query fails or returns no result, an HTTP 500 error is raised indicating a database configuration issue.

    Args:
        db (AsyncSession, optional): The asynchronous database session dependency.

    Returns:
        dict: A dictionary containing a welcome message if the database is healthy.

    Raises:
        HTTPException: If the database is not configured correctly or if there is an error connecting to the database.
    """
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
    
    