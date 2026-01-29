# Prison Roll Call - Server

FastAPI server for the Prison Roll Call face recognition system.

## Overview

This server acts as the "brain" of the Prison Roll Call system, providing:
- Face detection and recognition via ML models
- Inmate database management
- Roll call workflow coordination
- Face embedding storage and matching
- RESTful API for mobile clients

## Architecture

The server runs on a laptop configured as a WiFi hotspot, creating a closed local network with no internet connectivity. Mobile devices connect to this hotspot to perform roll call operations.

## Requirements

- Python 3.11+
- 16GB RAM minimum
- Optional: NVIDIA GPU (RTX 3060+) for faster inference

## Installation

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install development dependencies (optional):
```bash
pip install -e ".[dev]"
```

## Project Structure

```
server/
├── app/                    # Application code
│   ├── api/               # API routes and middleware
│   ├── db/                # Database and repositories
│   ├── ml/                # Machine learning models
│   ├── models/            # Pydantic data models
│   └── services/          # Business logic
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
└── scripts/              # Utility scripts
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_face_detector.py -v
```

## Development

### Code Formatting
```bash
black app/ tests/
```

### Type Checking
```bash
mypy app/
```

### Linting
```bash
flake8 app/ tests/
```

## Running the Server

Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Configuration is managed via environment variables and `app/config.py`. See the design document for detailed configuration options.

## Testing Workflow (TDD)

This project follows Test-Driven Development:

1. **Write tests first** - Define expected behavior
2. **See them fail (RED)** - Verify tests fail correctly
3. **Implement** - Write minimal code to pass tests
4. **See them pass (GREEN)** - Verify tests pass
5. **Refactor** - Improve code while keeping tests green

## License

Proprietary - Prison Roll Call System

## Contributing

See `PROJECT_TODO.md` for the development roadmap and current task status.

## Security Notes

- All data is encrypted at rest (AES-256)
- No internet connectivity required
- Face embeddings are one-way transformations
- API key authentication for all endpoints
- Regular security audits recommended

## Support

For technical support, contact the development team.
