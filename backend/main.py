from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from regenerate import Regenerate

regenerator = Regenerate()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/generate/")
async def generate(body: dict):
    input_text = body['input_text']
    plot_type = body['plot_type']

    regenerate_output = regenerator(input_text, plot_type)
    return {
        "infographicId": regenerate_output['infographic_id'],
        "infographicType": "img",
    }