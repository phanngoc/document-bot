import pandas as pd
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from uuid import uuid4
from langchain_core.documents import Document


# Đọc dữ liệu từ file CSV
data = pd.read_csv('data_temp/rss_data/cleaned_data.csv')

# Khởi tạo embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# Khởi tạo Chroma vector store
vector_store = Chroma(
    collection_name="rss_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)

# Tạo danh sách tài liệu từ dữ liệu CSV và thêm vào vector store theo batch 300 record
documents = []
batch_size = 300
batch_count = 0

for index, row in data.iterrows():
    document = Document(
        page_content=row['title'] + row['description'],  # Lấy nội dung từ cột 'description'
        metadata={
            "title": row['title'],          # Lấy tiêu đề từ cột 'title'
            "pubDate": row['pubDate'],      # Lấy ngày xuất bản từ cột 'pubDate'
            "url": row['url'],              # Lấy URL từ cột 'url
        },
        id=index + 1,  # ID duy nhất cho mỗi tài liệu
    )
    documents.append(document)

    # Kiểm tra xem đã đủ số lượng tài liệu cho một batch chưa
    if len(documents) == batch_size:
        batch_count += 1
        print(f"Batch {batch_count}: Đang thêm {batch_size} tài liệu vào vector store...")
        vector_store.add_documents(documents=documents, ids=[str(uuid4()) for _ in range(len(documents))])
        documents = []  # Reset danh sách tài liệu cho batch tiếp theo

# Thêm tài liệu còn lại vào vector store nếu có
if documents:
    batch_count += 1
    print(f"Batch {batch_count}: Đang thêm {len(documents)} tài liệu vào vector store...")
    vector_store.add_documents(documents=documents, ids=[str(uuid4()) for _ in range(len(documents))])
uuids = [str(uuid4()) for _ in range(len(documents))]
vector_store.add_documents(documents=documents, ids=uuids)

print("Dữ liệu đã được thêm vào Chroma DB thành công.")
