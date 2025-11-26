"""Main entry point for FileVyasa backend."""

import logging

import uvicorn

from filevyasa.config import settings


class HealthCheckFilter(logging.Filter):
    """Filter out health check requests from access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/health" not in message


def main():
    """Run the FileVyasa API server."""
    # Add filter to suppress health check logs
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

    uvicorn.run(
        "filevyasa.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
