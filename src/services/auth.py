import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt


from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.conf import config


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM

    def __init__(self):
        self.cache = redis.Redis(
            host=config.REDIS_DOMAIN,
            port=config.REDIS_PORT,
            db=0,
            password=config.REDIS_PASSWORD,
        )

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies that a plain text password matches the given hashed password.

        Args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the plain password matches the hashed password, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hashes the provided plain-text password using the configured password context.

        Args:
            password (str): The plain-text password to be hashed.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    # define a function to generate a new access token
    async def create_access_token( self, data: dict, expires_delta: Optional[float] = None):
        """
        Generates a JSON Web Token (JWT) access token with the provided data and expiration.
        Args:
            data (dict): The data to include in the token payload.
            expires_delta (Optional[float], optional): The number of seconds until the token expires. 
                If not provided, defaults to 15 minutes.
        Returns:
            str: The encoded JWT access token.
        Notes:
            - The token payload will include issued-at ("iat"), expiration ("exp"), and "scope" fields.
            - Uses the instance's SECRET_KEY and ALGORITHM for encoding.
        """
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Generates a JWT refresh token with the provided data and expiration.

        Args:
            data (dict): The payload data to include in the token.
            expires_delta (Optional[float], optional): The number of seconds until the token expires. 
                If not provided, defaults to 7 days.

        Returns:
            str: The encoded JWT refresh token.

        Notes:
            - The token includes issued-at ("iat"), expiration ("exp"), and scope ("refresh_token") claims.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes and validates a refresh JWT token.

        Args:
            refresh_token (str): The JWT refresh token to decode.

        Returns:
            str: The email address extracted from the token's payload if the token is valid and has the correct scope.

        Raises:
            HTTPException: If the token's scope is invalid or if the token cannot be validated.
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        Retrieves the current authenticated user based on the provided JWT access token.
        This method first attempts to decode and validate the JWT token. If the token is valid and contains the correct scope,
        it extracts the user's email from the token payload. The method then checks if the user data is available in the cache.
        If not found in the cache, it fetches the user from the database. If the user cannot be found or the token is invalid,
        an HTTP 401 Unauthorized exception is raised.
        Args:
            token (str): JWT access token provided by the client, automatically extracted via dependency injection.
            db (AsyncSession): Asynchronous database session, provided via dependency injection.
        Returns:
            User: The authenticated user object.
        Raises:
            HTTPException: If the credentials are invalid or the user does not exist.
        """

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user_hash = str(email)

        user = self.cache.get(user_hash)
        
        if user is None:
            print("GET_CURRENT_USER EMAIL:", email)
            user = await repository_users.get_user_by_email(email, db)
            print("GET_CURRENT_USER FOUND:", user)
            if user is None:
                raise credentials_exception
        else:
            print("User from cache")
            user = pickle.loads(user)
        return user

    def create_email_token(self, data: dict):
        """
        Generates a JWT email token with the provided data and a 1-day expiration.

        Args:
            data (dict): The payload data to include in the token.

        Returns:
            str: The encoded JWT token as a string.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        Extracts the email address from a JWT token.

        Args:
            token (str): The JWT token containing the user's email in the 'sub' claim.

        Returns:
            str: The email address extracted from the token.

        Raises:
            HTTPException: If the token is invalid or cannot be decoded.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )


auth_service = Auth()