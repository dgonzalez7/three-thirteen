# Development Setup

## Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

## Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Frontend Setup
```bash
cd frontend
npm install
```

## Running Locally

### Development Mode
```bash
# Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

### Docker Development
```bash
docker-compose up --build
```

## Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

## Code Quality
```bash
# Backend formatting
cd backend
black .
isort .

# Frontend formatting
cd frontend
npm run lint
npm run format
```

## Environment Variables
Create `.env` files as needed:
- `backend/.env` for backend configuration
- `frontend/.env` for frontend configuration
