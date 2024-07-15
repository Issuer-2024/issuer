from fastapi import FastAPI
import uvicorn

app = FastAPI()

uvicorn.run(app, host='0.0.0.0', port=8000)