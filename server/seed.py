from model import db, Assistant

def seed_assistants():
    assistants = [
        {
            "name": "Q&A bot",
            "url": "http://example.com/assistant1",
            "settings": "[website_url]",
            "tool": "search_chroma_db"
        },
        {
            "name": "SQL query bot",
            "url": "http://example.com/assistant2",
            "settings": "[database_url]",
            "tool": "write_sql_query"
        },
        {
            "name": "RSS bot",
            "url": "http://example.com/assistant3",
            "settings": "[website_url]",
            "tool": "retrieve_website_url, retrieve_rss_link"
        },
        {
            "name": "Transcript bot",
            "url": "http://example.com/assistant4",
            "settings": "[video_url]",
            "tool": "get_transcript"
        }
    ]

    db.connect()
    db.create_tables([Assistant], safe=True)  # Tạo bảng nếu chưa tồn tại

    # Xóa tất cả các trợ lý hiện có trước khi thêm mới
    Assistant.delete().execute()

    for assistant in assistants:
        Assistant.create(
            name=assistant["name"],
            url=assistant["url"],
            settings=assistant["settings"],
            tool=assistant["tool"]
        )
    
    db.close()

if __name__ == "__main__":
    seed_assistants() 