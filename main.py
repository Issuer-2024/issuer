import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.main_search import get_keyword_suggestion
from app.opinion import get_news_comments_opinion
from app.report import get_keyword_trend_variation, get_suggestions_trend_data
from app.report.toady_issue_summary import get_today_issue_summary
from app.timeline.get_timeline import get_timeline
from app.timeline.get_timeline import get_timeline_v2

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def render_main(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "keyword_suggestions": get_keyword_suggestion()
        }
    )


@app.get("/report")
def render_report(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="report.html", context={"issue_summary": get_today_issue_summary(q),
                                                      "trend_variation": get_keyword_trend_variation(q),
                                                      "suggestion_trend_data": get_suggestions_trend_data(q)
                                                      }
    )


@app.get("/opinion")
def render_opinion(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="opinion.html", context={"opinions": get_news_comments_opinion(q)}
    )


@app.get("/timeline")
def render_timeline(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="timeline.html", context={"timeline": get_timeline_v2(q)}
    )


uvicorn.run(app, host='0.0.0.0', port=8000)
