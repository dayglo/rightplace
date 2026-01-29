#!/usr/bin/env python3
"""Quick verification that TestClient is working with the fixed httpx version."""

import sys
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

def homepage(request):
    return JSONResponse({'hello': 'world'})

def test_testclient_works():
    """Verify TestClient can be instantiated and used."""
    app = Starlette(routes=[
        Route('/', homepage),
    ])

    try:
        # This is the line that was failing with httpx 0.28.1
        with TestClient(app) as client:
            response = client.get('/')
            assert response.status_code == 200
            assert response.json() == {'hello': 'world'}

        print("✓ TestClient instantiation: SUCCESS")
        print("✓ TestClient HTTP requests: SUCCESS")
        return True
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
            print("✗ TestClient instantiation: FAILED")
            print(f"  Error: {e}")
            return False
        raise

if __name__ == '__main__':
    success = test_testclient_works()
    sys.exit(0 if success else 1)
