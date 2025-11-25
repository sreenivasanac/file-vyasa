#!/usr/bin/env python3
"""Script to run the FileVyasa backend server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "filevyasa.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
