import os
from dotenv import load_dotenv
import sqlite3  # Thêm import cho sqlite3

# Tải biến môi trường từ tệp .env
load_dotenv()

# !pip install dsrag

from dsrag.create_kb import create_kb_from_file
from dsrag.knowledge_base import KnowledgeBase

# file_path = "data/cong-ty-nam-mo-dat-hiem-lon-nhat-viet-nam-lan-dau-bao-lai-ng.txt"
# kb_id = "cong_ty_mo_dat_hiem"
# kb = create_kb_from_file(kb_id, file_path)

# kb = KnowledgeBase(kb_id, exists_ok=True)
# search_queries = ["tổng tài sản của Vimico ?"]
# results = kb.query(search_queries)
# for segment in results:
#     print('segment:', segment)

path_csv = "server/data_temp/rss_data/cleaned_data.csv"

# kb_id = "bao_thanh_nien"
# kb = create_kb_from_file(kb_id, path_csv)

# kb = KnowledgeBase(kb_id, exists_ok=True)

# search_queries = ["rừng ngập mặn"]
# results = kb.query(search_queries)
# for segment in results:
#     print('segment:', segment)

# import pandas as pd

# # Đọc tệp CSV
# df = pd.read_csv(path_csv)

# # Tạo knowledge base từ dữ liệu trong DataFrame
# for index, row in df.iterrows():
#     if index >= 200:  # Chỉ lấy 200 records
#         break
#     kb_id = f"record_{index}"
#     create_kb_from_file(kb_id, row['title'] + " " + row['description'])  # Giả sử cột 'content' chứa dữ liệu cần thiết

# Kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect('server/data_temp/rss_data/rss_data.db')
cursor = conn.cursor()

# Truy vấn dữ liệu từ bảng cần thiết
cursor.execute("SELECT title, description FROM your_table_name")  # Thay 'your_table_name' bằng tên bảng của bạn
rows = cursor.fetchall()

# Tạo knowledge base từ dữ liệu trong cơ sở dữ liệu
for index, row in enumerate(rows):
    if index >= 200:  # Chỉ lấy 200 records
        break
    kb_id = f"record_{index}"
    create_kb_from_file(kb_id, row[0] + " " + row[1])  # row[0] là title, row[1] là description

# Đóng kết nối
conn.close()


