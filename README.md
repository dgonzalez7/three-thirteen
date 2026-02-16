# Three Thirteen

An online version of the card game Three Thirteen (3-13).

## Current Status

Infrastructure scaffolding with a "Hello, Detective!" placeholder app.

## Local Development
```powershell
# Run with Docker
docker build -t three-thirteen .
docker run -p 8000:8000 three-thirteen

# Run tests
pip install -r requirements.txt
pytest app/tests/
```

## Architecture

- **App:** Python / FastAPI
- **Container:** Docker
- **Cloud:** AWS App Runner
- **CI/CD:** GitHub Actions
- **IaC:** Terraform