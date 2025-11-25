#!/usr/bin/env python3
"""Script to run the FileVyasa backend server."""

import logging
import uvicorn


class HealthCheckFilter(logging.Filter):
    """Filter out health check requests from access logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/health" not in message


if __name__ == "__main__":
    # Add filter to suppress health check logs
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
    
    uvicorn.run(
        "filevyasa.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
