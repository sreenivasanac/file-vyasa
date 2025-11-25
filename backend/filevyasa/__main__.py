"""Main entry point for FileVyasa backend."""

import uvicorn

from filevyasa.config import settings


def main():
    """Run the FileVyasa API server."""
    uvicorn.run(
        "filevyasa.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
