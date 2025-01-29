from elasticsearch import *

client = Elasticsearch("http://localhost:9200",
                       headers={"x-elastic-product-required": "false"},
                       meta_header=True)

print(client.info())

# Lấy danh sách tất cả các indices
indices = client.indices.get_alias(index="*")

# In ra danh sách indices
print("\nDanh sách các indices:")
for index in indices:
    print(f"- {index}")

    # Tìm kiếm tin tức ngân hàng và tài chính trong khoảng thời gian cụ thể
    search_result = client.search(
        index="rss_feeds",
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "match_all": {}
                        }
                    ],
                    # "filter": {
                    #     "range": {
                    #         "pubDate": {
                    #             "gte": "2024-12-01",
                    #             "lte": "2024-12-31"
                    #         }
                    #     }
                    # }
                }
            }
        }
    )

    print("\nKết quả tìm kiếm:")
    for hit in search_result['hits']['hits']:
        print('hit', hit)
        # In ra thông tin của embedding nếu có
        if 'embedding' in hit['_source']:
            print(f"Embedding: {hit['_source']['embedding'][:100]}")
        else:
            print("Không có thông tin embedding.")
        # print(f"Title: {hit['_source']['title']}")
        # print(f"Description: {hit['_source']['description']}")
        # print(f"URL: {hit['_source']['url']}")
        # print(f"Ngày xuất bản: {hit['_source']['pubDate']}")
        # print("---")


       
# Xóa index
# client.indices.delete(index='rss_feeds', ignore=[400, 404])
