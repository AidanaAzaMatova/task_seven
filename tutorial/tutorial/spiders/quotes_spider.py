import scrapy


class MySpider(scrapy.Spider):
    name = "myspider"

    # Настройки для вывода данных в файл
    custom_feed = {
        "/spiders/items.json": {  # Абсолютный путь
            "format": "json",
            "indent": 4,  # Форматировать JSON с отступами
        }
    }

    def __init__(self, category=None, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"http://www.example.com/categories/{category}"]
        # ...

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        # Обновляем настройки FEEDS
        feeds = settings.setdefault("FEEDS", {})
        feeds.update(cls.custom_feed)

    def start_requests(self):
        # Пример запроса
        yield scrapy.Request(url="http://example.com", callback=self.parse)

    def parse(self, response):
        # Пример обработки ответа
        yield {"title": response.xpath("//title/text()").get()}
