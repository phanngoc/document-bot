# pipelines.py
import scrapy

class ValidatePipeline:
    def process_item(self, item, spider):
        # Perform validation
        if 'url' not in item:
            raise scrapy.exceptions.DropItem("Missing URL in %s" % item)
        return item

class TransformPipeline:
    def process_item(self, item, spider):
        # Transform the item (e.g., clean or modify fields)
        item['url'] = item['url'].lower()
        return item

class SavePipeline:
    def process_item(self, item, spider):
        # Save the item (e.g., write to a database or file)
        spider.logger.info(f"Saving item: {item}")
        return item
