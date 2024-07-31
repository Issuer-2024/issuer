from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.v1.opinion import get_news_comments_opinion
from app.v1.report import get_keyword_trend_variation, get_suggestions_trend_data
from app.v1.report import get_today_issue_summary
from app.v1.request_external_api import get_google_trend_daily_rank
from app.v1.timeline.get_timeline import get_timeline_v2
from app.v2.content import get_content
from app.v2.keyword_rank import get_keyword_rank

from redis_om import get_redis_connection

redis = None
db_redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis
    global db_redis
    redis = get_redis_connection(
        host="localhost",
        port=6379,
        decode_responses=True
    )
    db_redis = redis
    yield
    # Clean up the ML models and release the resources
    redis.close()


load_dotenv()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates_v1 = Jinja2Templates(directory="templates/v1")
templates_v2 = Jinja2Templates(directory="templates/v2")


@app.get("/")
async def render_main(request: Request):
    return templates_v1.TemplateResponse(
        request=request, name="index.html", context={
            "keyword_suggestions": get_google_trend_daily_rank()
        }
    )


@app.get("/report")
def render_report(q: str, request: Request):
    return templates_v1.TemplateResponse(
        request=request, name="report.html", context={"issue_summary": get_today_issue_summary(q),
                                                      "trend_variation": get_keyword_trend_variation(q),
                                                      "suggestion_trend_data": get_suggestions_trend_data(q)
                                                      }
    )


@app.get("/opinion")
def render_opinion(q: str, request: Request):
    return templates_v1.TemplateResponse(
        request=request, name="opinion.html", context={"opinions": get_news_comments_opinion(q)}
    )


@app.get("/timeline")
def render_timeline(q: str, request: Request):
    return templates_v1.TemplateResponse(
        request=request, name="timeline.html", context={"timeline": get_timeline_v2(q)}
    )


@app.get("/test/")
async def render_main_v2(request: Request):
    return templates_v2.TemplateResponse(
        request=request, name="index.html", context={
            "keyword_suggestions": get_google_trend_daily_rank()
        }
    )


@app.get("/test/report")
async def render_report_v2(q: str, request: Request):
    return templates_v2.TemplateResponse(
        request=request, name="report.html", context={
            'content': get_content(q),
            'keyword_rank': get_keyword_rank()
        }
    )


uvicorn.run(app, host='0.0.0.0', port=8000)
