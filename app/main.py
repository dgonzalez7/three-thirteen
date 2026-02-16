import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Three Thirteen")
templates = Jinja2Templates(directory="app/templates")

DETECTIVES = [
    "Sherlock Holmes",
    "Hercule Poirot",
    "Miss Marple",
    "Philip Marlowe",
    "Sam Spade",
    "Nancy Drew",
    "Inspector Morse",
    "Brother Cadfael",
    "Lord Peter Wimsey",
    "C. Auguste Dupin",
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    detective = random.choice(DETECTIVES)
    return templates.TemplateResponse(
        "hello.html", {"request": request, "name": detective}
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}
