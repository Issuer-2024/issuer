from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.templating import Jinja2Templates
from app.v1.request_external_api import get_google_trend_daily_rank
from app.v2.config.rate_limit import check_rate_limit
from app.v2.content import get_content, create_content
from app.v2.creating.get_creating import get_creating_sep
from app.v2.keyword_rank import get_keyword_rank
from app.v2.recently_added.get_recently_added import get_recently_added_sep, get_recently_added_all

from app.v2.redis.redis_connection import connect_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_redis()
    yield
    # Clean up the ML models and release the resources


load_dotenv()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates_v1 = Jinja2Templates(directory="templates/v1")
templates_v2 = Jinja2Templates(directory="templates/v2")


# @app.get("/")
# async def render_main(request: Request):
#     return templates_v1.TemplateResponse(
#         request=request, name="index.html", context={
#             "keyword_suggestions": get_google_trend_daily_rank()
#         }
#     )
#
#
# @app.get("/report")
# def render_report(q: str, request: Request):
#     return templates_v1.TemplateResponse(
#         request=request, name="report.html", context={"issue_summary": get_today_issue_summary(q),
#                                                       "trend_variation": get_keyword_trend_variation(q),
#                                                       "suggestion_trend_data": get_suggestions_trend_data(q)
#                                                       }
#     )
#
#
# @app.get("/opinion")
# def render_opinion(q: str, request: Request):
#     return templates_v1.TemplateResponse(
#         request=request, name="opinion.html", context={"opinions": get_news_comments_opinion(q)}
#     )
#
#
# @app.get("/timeline")
# def render_timeline(q: str, request: Request):
#     return templates_v1.TemplateResponse(
#         request=request, name="timeline.html", context={"timeline": get_timeline_v2(q)}
#     )


@app.get("/")
async def render_main_v2(request: Request):
    return templates_v2.TemplateResponse(
        request=request, name="index.html", context={
            "keyword_suggestions": get_google_trend_daily_rank()
        }
    )


@app.get("/report")
async def render_report_v2(q: str, request: Request, background_task: BackgroundTasks):
    content = get_content(q)
    keyword_rank = get_keyword_rank()
    if not content:
        rate_limit_info = check_rate_limit()
        if not rate_limit_info['status']:
            return rate_limit_info['message']

        background_task.add_task(create_content, q, background_task)
        return templates_v2.TemplateResponse(
            request=request, name="creating.html", context={
                'keyword': q,
                'keyword_rank': keyword_rank
            }
        )

    return templates_v2.TemplateResponse(
        request=request, name="report.html", context={
            'content': content,
            'keyword_rank': keyword_rank
        }
    )


@app.get("/api/recent-add-sep")
async def get_recent_add_sep():
    return get_recently_added_sep()


@app.get("/api/creating-sep")
async def creating_sep():
    return get_creating_sep()


@app.get("/recently-added")
async def get_recently_add_all(request: Request):
    return templates_v2.TemplateResponse(
        request=request, name="recently_added_all.html", context={
            'recently_added_all': get_recently_added_all(),
            'keyword_rank': get_keyword_rank()
        }
    )


class OpinionRequest(BaseModel):
    opinion: str


@app.post("/find-opinion")
async def find_opinion(request: OpinionRequest):
    print(request.opinion)

    return


uvicorn.run(app, host='0.0.0.0', port=8000)
