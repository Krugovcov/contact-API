from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    Asynchronously creates a new user in the database.
    Args:
        body (UserSchema): The data required to create a new user.
        db (AsyncSession, optional): The database session dependency.
    Returns:
        User: The newly created user instance.
    Raises:
        Exception: If there is an error generating the Gravatar image.
    Side Effects:
        Adds a new user to the database and commits the transaction.
    """
    
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    Asynchronously updates the refresh token for a given user in the database.

    Args:
        user (User): The user instance whose refresh token is to be updated.
        token (str | None): The new refresh token value. Can be None to clear the token.
        db (AsyncSession): The asynchronous database session used to commit the changes.

    Returns:
        None
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Marks the user's email as confirmed in the database.

    Args:
        email (str): The email address of the user to confirm.
        db (AsyncSession): The asynchronous database session.

    Returns:
        None

    Raises:
        Any exception raised by `get_user_by_email` or database commit operations.
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    Updates the avatar URL of a user identified by their email address.

    Args:
        email (str): The email address of the user whose avatar URL is to be updated.
        url (str | None): The new avatar URL to set. If None, the avatar will be cleared.
        db (AsyncSession): The asynchronous database session to use for the operation.

    Returns:
        User: The updated user object with the new avatar URL.

    Raises:
        ValueError: If the user with the specified email does not exist.
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user