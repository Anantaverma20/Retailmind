"""Error handling utilities."""
from typing import Dict, Any


def handle_database_error(error: Exception, logger) -> Dict[str, Any]:
    """
    Standardize database error handling across handlers.
    
    Args:
        error: Exception that occurred
        logger: Logger instance
        
    Returns:
        Standardized error response dictionary
    """
    error_msg = str(error).lower()
    logger.error(f"Database error: {error}", exc_info=True)
    
    if "connection" in error_msg or "timeout" in error_msg:
        return {"error": True, "error_message": "Database connection error. Please try again."}
    elif "not found" in error_msg:
        return {"error": True, "error_message": "Requested data not found."}
    else:
        return {"error": True, "error_message": f"Database operation failed: {str(error)}"}


def handle_generic_error(error: Exception, operation: str, logger) -> Dict[str, Any]:
    """
    Handle generic errors with standardized messages.
    
    Args:
        error: Exception that occurred
        operation: Description of the operation that failed
        logger: Logger instance
        
    Returns:
        Standardized error response dictionary
    """
    error_msg = str(error).lower()
    logger.error(f"Error in {operation}: {error}", exc_info=True)
    
    return {"error": True, "error_message": f"Unable to {operation}: {str(error)}"}

