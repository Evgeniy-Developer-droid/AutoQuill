from typing import TypedDict, Dict, Any

from elasticsearch import Elasticsearch
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings

from app import config
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph


embedding_model = HuggingFaceEmbeddings(
    model_name=config.HUGGINGFACE_EMBEDDING_MODEL,
    model_kwargs={"device": config.MODEL_DEVICE}
)

model = ChatOpenAI(
    temperature=0,
    model=config.GPT_MODEL,
    api_key=config.OPENAI_API_KEY,
    max_tokens=config.MAX_TOKEN_LIMIT,
)

es = Elasticsearch(config.ELASTICSEARCH_HOST)

vectorstore = ElasticsearchStore(
    index_name="documents",
    es_connection=es,
    embedding=embedding_model,
    vector_query_field="embedding",
)

tools = []


class State(TypedDict):
    additional_kwargs: Dict[str, Any]


def retriever_node(state):
    topic = state["additional_kwargs"].get("topic", "No topic")
    channel_id = state["additional_kwargs"]["channel_id"]
    company_id = state["additional_kwargs"]["company_id"]
    if "random" in state["additional_kwargs"] and state["additional_kwargs"]["random"]:
        docs = es.search(
            index="documents",
            body={
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"channel_id": channel_id}},
                                    {"term": {"company_id": company_id}},
                                ]
                            }
                        },
                        "random_score": {},
                    }
                },
                "size": 3,
            },
        )
        docs = [doc["_source"] for doc in docs["hits"]["hits"]]
        print(f"{len(docs)} random documents found for topic '{topic}' in channel '{channel_id}' and company '{company_id}'")
        print(docs)
        context = "\n\n".join([doc["text"] for doc in docs])
    else:
        docs = vectorstore.similarity_search(
            query=topic,
            k=3,
            filter=[{"term": {"channel_id": channel_id}}, {"term": {"company_id": company_id}}],
        )
        print(f"Found {len(docs)} documents for topic '{topic}' in channel '{channel_id}' and company '{company_id}'")
        print(docs)
        context = "\n\n".join([doc.page_content for doc in docs])
    state["additional_kwargs"]["context"] = context
    return state


def prompt_builder(state):
    prompt = state["additional_kwargs"]["prompt"]
    topic = state["additional_kwargs"].get("topic", None)
    context = state["additional_kwargs"].get("context", None)

    if topic:
        prompt = f"{prompt}\n\nTopic: {topic}"
    if context:
        prompt = f"{prompt}\n\nUse relevant insights from the following content:\n{context}"
    state["additional_kwargs"]["prompt"] = prompt
    return state

def llm_generator(state):
    prompt = state["additional_kwargs"]["prompt"]
    response = model([SystemMessage(content="You are a helpful assistant."), HumanMessage(content=prompt)])
    state["additional_kwargs"]["response"] = response.content
    return state

def post_editor(state):
    return state


class PostGraph:

    def __init__(self):
        self.builder = StateGraph(State)
        self.builder.add_node("Retriever", retriever_node)
        self.builder.add_node("PromptBuilder", prompt_builder)
        self.builder.add_node("LLMGenerator", llm_generator)
        self.builder.add_node("PostEditor", post_editor)

        self.builder.set_entry_point("Retriever")
        self.builder.add_edge("Retriever", "PromptBuilder")
        self.builder.add_edge("PromptBuilder", "LLMGenerator")
        self.builder.add_edge("LLMGenerator", "PostEditor")
        self.builder.set_finish_point("PostEditor")
        self.graph = self.builder.compile()

    def get_compiled_graph(self):
        return self.graph





