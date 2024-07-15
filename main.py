from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/timeline")
def get_timeline_preview(q: str):
    pass


uvicorn.run(app, host='0.0.0.0', port=8000)