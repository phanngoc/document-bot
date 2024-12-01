## Crawler

### Introduction
This document provides instructions on how to set up and run the crawler for the video-maker project.

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

To run the crawler, use the following command:
```sh
cd crawler && scrapy crawl link_spider
```

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
