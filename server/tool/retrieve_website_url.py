from langchain_core.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = InMemoryVectorStore(embeddings)

from pydantic import BaseModel, Field


class WebsiteUrl(BaseModel):
    """When site to extract URL from."""

    url: str = Field(description="The URL of the website to extract information from.")
    # class_name: List[str] = Field(description="The class_names css_selector to extract information from.")


llm = ChatOpenAI(model="gpt-4o")
url_extractor = llm.with_structured_output(WebsiteUrl)


@tool(response_format="content_and_artifact")
def retrieve_website_url(query: str):
    """Retrieve information related to a query."""
    websiteUrlValue = url_extractor.invoke(query)
    print('websiteUrlValue:', websiteUrlValue)
    loader = WebBaseLoader(
        web_paths=(websiteUrlValue.url,),
    )
    docs = loader.load()
    print('docs:', docs)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    vector_store.add_documents(documents=all_splits)
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    print('serialized:', serialized)
    return serialized, retrieved_docs 