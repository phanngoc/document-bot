ITEM_PIPELINES = {
    'spiders.pipelines.ValidatePipeline': 100,
    'spiders.pipelines.TransformPipeline': 200,
    'spiders.pipelines.SavePipeline': 300,
}

OUTPUT_FILE = '../data_temp/rss_data/output.csv'  # Đường dẫn đến file CSV
ELASTICSEARCH_HOST = 'http://localhost:9200'  # Địa chỉ Elasticsearch