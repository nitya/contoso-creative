import os
import json
from typing import Dict, List
import prompty
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
)
from azure.core.credentials import AzureKeyCredential

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_VERSION = "2023-07-01-preview"
AZURE_OPENAI_DEPLOYMENT = "text-embedding-ada-002"
AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY")
AZURE_AI_SEARCH_INDEX = "contoso-products"


@prompty.trace
def generate_embeddings(queries: List[str]) -> str:

    client = AzureOpenAI(
        api_version=AZURE_OPENAI_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        api_key=AZURE_OPENAI_KEY,
    )

    embeddings = client.embeddings.create(input=queries, model=AZURE_OPENAI_DEPLOYMENT)
    embs = [emb.embedding for emb in embeddings.data]
    items = [{"item": queries[i], "embedding": embs[i]} for i in range(len(queries))]

    return items


@prompty.trace
def retrieve_products(items: List[Dict[str, any]], index_name: str) -> str:
    search_client = SearchClient(
        endpoint=AZURE_AI_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(AZURE_AI_SEARCH_KEY),
    )

    products = []
    for item in items:
        vector_query = VectorizedQuery(
            vector=item["embedding"], k_nearest_neighbors=3, fields="contentVector"
        )
        results = search_client.search(
            search_text=item["item"],
            vector_queries=[vector_query],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="default",
            query_caption=QueryCaptionType.EXTRACTIVE,
            query_answer=QueryAnswerType.EXTRACTIVE,
            top=2,
        )

        docs = [
            {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "url": doc["url"],
            }
            for doc in results
        ]

        # Remove duplicates
        products.extend([i for i in docs if i["id"] not in [x["id"] for x in products]])

    return {"requests": [item["item"] for item in items], "products": products}


@prompty.trace
def find_products(context: str) -> Dict[str, any]:
    queries = prompty.execute("product.prompty", inputs={"context": context})
    qs = json.loads(queries)
    items = generate_embeddings(qs["queries"])
    products = retrieve_products(items, AZURE_AI_SEARCH_INDEX)
    return products


if __name__ == "__main__":
    context = "Can you use a selection of tents and backpacks as context?"
    answer = find_products(context)
    print(json.dumps(answer, indent=2))
