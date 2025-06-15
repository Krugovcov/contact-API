from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import UserSchema, TokenSchema, UserResponse, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes in a UserSchema object, which is validated by pydantic.
        If the email already exists, it raises an HTTPException with status code 409 (Conflict).
        Otherwise, it hashes the password and creates a new user using create_user from repositories/users.py.

    :param body: UserSchema: Validate the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Get the database session
    :return: A user object
    :doc-author: Trelent
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXIST)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login",  response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Handles user login by verifying credentials and generating JWT tokens.

    Args:
        body (OAuth2PasswordRequestForm, optional): The form data containing username (email) and password. Provided by FastAPI dependency injection.
        db (AsyncSession, optional): The asynchronous database session. Provided by FastAPI dependency injection.

    Raises:
        HTTPException: If the user with the given email does not exist.
        HTTPException: If the user's email is not confirmed.
        HTTPException: If the provided password is invalid.

    Returns:
        dict: A dictionary containing the access token, refresh token, and token type.
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email, "test": "Сергій Багмет"})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token',  response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),db: AsyncSession = Depends(get_db)):
    """
    Refreshes the access and refresh tokens for an authenticated user.
    Args:
        credentials (HTTPAuthorizationCredentials): The HTTP authorization credentials containing the refresh token.
        db (AsyncSession): The asynchronous database session dependency.
    Returns:
        dict: A dictionary containing the new access token, refresh token, and token type.
    Raises:
        HTTPException: If the provided refresh token is invalid or does not match the user's stored token.
    Process:
        - Decodes the provided refresh token to extract the user's email.
        - Retrieves the user from the database using the extracted email.
        - Validates that the provided refresh token matches the one stored for the user.
        - If valid, generates new access and refresh tokens.
        - Updates the user's stored refresh token in the database.
        - Returns the new tokens and token type.
    """
    
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms a user's email address using a verification token.

    Args:
        token (str): The email verification token.
        db (AsyncSession, optional): The database session dependency.

    Returns:
        dict: A message indicating whether the email was already confirmed or has just been confirmed.

    Raises:
        HTTPException: If the user does not exist or the verification fails.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,db: AsyncSession = Depends(get_db)):
     
    """Handles email confirmation requests.

        This endpoint receives a request to send a confirmation email to a user. If the user's email is already confirmed,
        it returns a message indicating so. Otherwise, it schedules an email to be sent in the background and returns a message
        prompting the user to check their email for confirmation.
        
        Args:
            body (RequestEmail): The request body containing the user's email address.
            background_tasks (BackgroundTasks): FastAPI background tasks manager for scheduling email sending.
            request (Request): The incoming HTTP request object, used to extract base URL.
            db (AsyncSession, optional): Database session dependency.
        Returns:
            dict: A message indicating whether the email is already confirmed or instructing the user to check their email.
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Handles a request to track when a user opens an email by their username.

    Args:
        username (str): The username of the user who opened the email.
        response (Response): The HTTP response object.
        db (AsyncSession, optional): The asynchronous database session dependency.

    Returns:
        FileResponse: An inline PNG image used as a tracking pixel.

    Side Effects:
        Logs to the console that the user has opened the email and simulates saving this event to the database.
    """
    print('--------------------------------')
    print(f'{username} зберігаємо що він відкрив email в БД')
    print('--------------------------------')
    return FileResponse("src/static/open_check.png", media_type="image/png", content_disposition_type="inline")