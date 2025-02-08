import json
from elasticsearch import *
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1536)
# Khởi tạo LLM

llm_s = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

client = Elasticsearch("http://localhost:9200",
                       headers={"x-elastic-product-required": "false"},
                       meta_header=True)

print(client.info())

# Lấy danh sách tất cả các indices
indices = client.indices.get_alias(index="*")

total_docs = client.count(index="rss_feeds")['count']
print(f"Tổng số tài liệu trong index 'rss_feeds': {total_docs}")

# Xóa index
def delete_index(client, index):
    client.indices.delete(index=index, ignore=[400, 404])

prompt_template_query = ChatPromptTemplate.from_messages([
    ("system", """Bạn là một developer. Nhiệm vụ của bạn là:
    1. Phân tích câu hỏi thành các truy vấn nhỏ có thể giải quyết được
    2. Viết query elasticsearch dùng must, should, must_not, filter để tìm kiếm từng truy vấn.
    3. Có thể dùng dấu "+" để tạo query must, dấu "-" để tạo query must_not
    3. Trả về kết quả dưới dạng JSON với format:
    {{
        "query": {{
        "bool": {{
            "must": [],
            "should": [],
            "must_not": [],
            "filter": []
        }}
        }}
    }}
    
    Ví dụ:
    - "tin tức bất động sản và tài chính, có dự án cụ thể, không liên quan tới covid" -> {{"query": {{"bool": {{"must": [{{"match": {{"title": "tin tức bất động sản và tài chính"}}}}, {{"match": {{"title": "dự án cụ thể"}}}}], "must_not": [{{"match": {{"title": "covid"}}}}]}}}}}}
    - "tin tức bất động sản và tài chính, có dự án cụ thể, không liên quan tới covid, từ tháng 1/2024" -> {{"query": {{"bool": {{"must": [{{"match": {{"title": "tin tức bất động sản và tài chính"}}}}, {{"match": {{"title": "dự án cụ thể"}}}}], "must_not": [{{"match": {{"title": "covid"}}}}], "filter": [{{"range": {{"pubDate": {{"gte": "2024-01-01"}}}}}}]}}}}}}
    - "tin tức bất động sản và tài chính, có dự án cụ thể, không liên quan tới covid, từ tháng 1/2024 đến tháng 12/2024" -> {{"query": {{"bool": {{"must": [{{"match": {{"title": "tin tức bất động sản và tài chính"}}}}, {{"match": {{"title": "dự án cụ thể"}}}}], "must_not": [{{"match": {{"title": "covid"}}}}], "filter": [{{"range": {{"pubDate": {{"gte": "2024-01-01", "lte": "2024-12-31"}}}}}}]}}}}}}
    - "tin tức +dự án cụ thể -covid" -> {{"query": {{"bool": {{"must": [{{"match": {{"title": "dự án cụ thể"}}}}], "must_not": [{{"match": {{"title": "covid"}}}}]}}}}}}
    """),
    ("human", "{query}")
])



def search_indices_and_print_results(client, index, query, embeddings):
    # Tạo PromptTemplate
    chain = prompt_template_query | llm_s
    result = chain.invoke({"query": query})
    print("result", result)
    result = result.content
    # Loại bỏ phần bọc JSON
    if result.startswith("```json"):
        result = result[7:]  # Loại bỏ phần đầu "```json"
    if result.endswith("```"):
        result = result[:-3]  # Loại bỏ phần cuối "```"

    # Đảm bảo đầu ra là JSON
    base_query = []
    try:
        base_query = json.loads(result)
        print('Answer (JSON):', json.dumps(base_query, indent=4))
    except json.JSONDecodeError:
        print('Error: Output is not valid JSON')
        print('Raw Answer:', answer)

    # Thêm tìm kiếm mờ vào các truy vấn `match`
    for clause in base_query["query"]["bool"]["must"]:
        if "match" in clause:
            for field, value in clause["match"].items():
                # Tạo một đối tượng match mới với fuzziness
                clause["match"] = {field: {"query": value, "fuzziness": "AUTO"}}
    
    print("base_query:", base_query)

    print("\Bắt đầu search:")
  
    query_embedding = embeddings.embed_query(query)

    # Thêm vector search vào bool query
    base_query["query"]["bool"]["must"].append(
        {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 2.0",
                    "params": {"query_vector": query_embedding}
                }
            }
        }
    )

    # Điều chỉnh trọng số giữa text search và vector search
    base_query["query"]["bool"]["minimum_should_match"] = 0
    # print("base_query", base_query)
    # Khởi tạo ElasticsearchRetriever
    vector_retriever = ElasticsearchRetriever.from_es_params(
        index_name="rss_feeds",
        body_func=lambda query: base_query,
        content_field="title",
        url="http://localhost:9200",
    )

    # Sử dụng ElasticsearchRetriever để tìm kiếm
    search_result = vector_retriever.invoke(query)

    print("\nKết quả tìm kiếm:")
    for hit in search_result:
        print(hit.page_content)

    prompt = ChatPromptTemplate.from_template(
        """Answer the question based only on the context provided.
        Context: {context}
        Question: {question}"""
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": vector_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke(query)
    print('answer', answer)



query = "tin tài chính doanh nghiệp, liên quan ngân hàng, tháng 8 năm 2024"  # Thay đổi từ khóa tìm kiếm tại đây
index = "rss_feeds"  # Thay đổi index tại đây

# phân tich query, thấy có dấu "-" thì thành truy vấn phủ định, + : thành truy vấn khẳng định
# dùng ChatPromptTemplate.from_messages([ của langchain để phân tích query
search_indices_and_print_results(client, index, query, embeddings)
