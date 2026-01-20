"""User-friendly error handling utilities."""

from typing import Optional
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
from asyncpg.exceptions import InFailedSQLTransactionError


def get_user_friendly_error_message(exc: Exception) -> str:
    """
    Convert technical exceptions to user-friendly error messages.
    
    Args:
        exc: The exception that occurred
        
    Returns:
        A user-friendly error message string
    """
    # Handle SQLAlchemy transaction errors
    if isinstance(exc, SQLAlchemyError):
        # Check for transaction rollback errors
        error_str = str(exc).lower()
        
        if "transaction" in error_str and ("rolled back" in error_str or "aborted" in error_str):
            return "A database error occurred. Please try again in a moment."
        
        if "infailed" in error_str or "transaction is aborted" in error_str:
            return "A database error occurred. Please try again in a moment."
        
        if isinstance(exc, IntegrityError):
            if "unique constraint" in error_str or "duplicate" in error_str:
                return "This item already exists. Please try a different option."
            return "A data integrity error occurred. Please check your input and try again."
        
        if isinstance(exc, OperationalError):
            if "connection" in error_str or "timeout" in error_str:
                return "Unable to connect to the database. Please try again in a moment."
            return "A database operation failed. Please try again."
        
        # Generic SQLAlchemy error
        return "A database error occurred. Please try again."
    
    # Handle asyncpg specific errors
    if "InFailedSQLTransactionError" in str(type(exc)) or isinstance(exc.__cause__, InFailedSQLTransactionError):
        return "A database error occurred. Please try again in a moment."
    
    # Handle HTTP exceptions (already user-friendly)
    if hasattr(exc, "detail") and isinstance(exc.detail, str):
        return exc.detail
    
    # Handle ValueError and other common exceptions
    if isinstance(exc, ValueError):
        return str(exc)
    
    if isinstance(exc, RuntimeError):
        return str(exc)
    
    # Generic fallback - don't expose technical details
    return "Something went wrong. Please try again or contact support if the problem persists."


def should_log_error(exc: Exception) -> bool:
    """
    Determine if an error should be logged (technical errors should be logged,
    but user-friendly messages shouldn't be).
    
    Args:
        exc: The exception that occurred
        
    Returns:
        True if the error should be logged
    """
    # Always log database errors for debugging
    if isinstance(exc, SQLAlchemyError):
        return True
    
    # Log unexpected errors
    if not isinstance(exc, (ValueError, RuntimeError)) and not hasattr(exc, "status_code"):
        return True
    
    return False
