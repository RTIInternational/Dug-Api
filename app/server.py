import logging
import os
import uvicorn

from fastapi import FastAPI
from app.config import Config
from app.core.async_search import Search
from pydantic import BaseModel
import asyncio

logger = logging.getLogger(__name__)

APP = FastAPI(
    title="Dug Search API",
    root_path=os.environ.get("ROOT_PATH", "/"),
)


class GetFromIndex(BaseModel):
    index: str = "concepts_index"
    size: int = 0


class SearchConceptQuery(BaseModel):
    query: str
    index: str = "concepts_index"
    offset: int = 0
    size: int = 20


class SearchVariablesQuery(BaseModel):
    query: str
    index: str = "variables_index"
    concept: str = ""
    offset: int = 0
    size: int = 1000


class SearchKgQuery(BaseModel):
    query: str
    unique_id: str
    index: str = "kg_index"
    size: int = 100


search = Search(Config.from_env())


@APP.on_event("shutdown")
def shutdown_event():
    asyncio.run(search.es.close())


@APP.post('/search-api/dump_concepts')
async def dump_concepts(request: GetFromIndex):
    return {
        "message": "Dump result",
        "result": await search.dump_concepts(**request.dict()),
        "status": "success"
    }


@APP.get('/search-api/agg_data_types')
async def agg_data_types():
    return {
        "message": "Dump result",
        "result": await search.agg_data_type(),
        "status": "success"
    }


@APP.post('/search-api/search')
async def search_concepts(search_query: SearchConceptQuery):
    logger.debug(
        "\n############\nStarting /search request handling\n############\n")
    return {
        "message": "Search result",
        # Although index in provided by the query we will keep it around for backward compatibility, but
        # search concepts should always search against "concepts_index"
        "result": await search.search_concepts(**search_query.dict(exclude={"index"})),
        "status": "success"
    }


@APP.post('/search-api/search_kg')
async def search_kg(search_query: SearchKgQuery):
    return {
        "message": "Search result",
        # Although index in provided by the query we will keep it around for backward compatibility, but
        # search concepts should always search against "kg_index"
        "result": await search.search_kg(**search_query.dict(exclude={"index"})),
        "status": "success"
    }


@APP.post('/search-api/search_var')
async def search_var(search_query: SearchVariablesQuery):
    return {
        "message": "Search result",
        # Although index in provided by the query we will keep it around for backward compatibility, but
        # search concepts should always search against "variables_index"
        "result": await search.search_variables(**search_query.dict(exclude={"index"})),
        "status": "success"
    }

@APP.get('/search-api/')
async def base():
    return {
        "message": "Welcome to the Dug Search API",
        "result": "Please see our documentation for more information at the /search-api/docs page",
        "status": "success"
    }


if __name__ == '__main__':
    uvicorn.run(APP)
