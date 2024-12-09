## Document Bot

### Introduction
- Trong nhiều trường hợp, các chatbot như chatGPT bị outdate dữ liệu kiến câu lời thiếu chính xác hoặc dùng version code cũ.

- Mục đích của dự án này là tạo ra một bot có khả năng thu thập thông tin từ các trang web tài liệu cụ thể kết hợp RAG để tạo BOT trả lời chính xác câu hỏi người dùng.

- Dự án sử dụng Scrapy để thu thập dữ liệu và Streamlit để hiển thị dữ liệu.

---
ENGLISH:
- In many cases, chatbots like ChatGPT have outdated data, resulting in inaccurate answers or using old code versions.

- The purpose of this project is to create a bot capable of gathering information from specific documentation websites, combined with RAG, to create a BOT that accurately answers user questions.

- The project uses Scrapy to collect data and Streamlit to display the data.

![alt text](<screenshot.png>)

### Prerequisites
- Python 3.x
- Virtual environment

### Setup

1. Create a virtual environment:
    ```sh
    python3 -m venv .venv
    ```

2. Activate the virtual environment:
    ```sh
    source .venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```


### Usage

- Run the Streamlit app:
```
streamlit run app.py
```

### Configuration

You can configure the crawler by modifying the `config.json` file. The file contains various settings such as the target URL, crawling depth, and output directory.

### Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request.

### License

This project is licensed under the MIT License.

