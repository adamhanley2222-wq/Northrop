from openai import OpenAI
from pinecone import Pinecone

from app.core.config import settings


def get_openai_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def get_pinecone_client() -> Pinecone | None:
    if not settings.pinecone_api_key:
        return None
    return Pinecone(api_key=settings.pinecone_api_key)
