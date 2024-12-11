import scrapy

class QuotesSpider(scrapy.Spider):
    name = 'idoni'
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        for quote in response.xpath('//div[@class="quote"]'):
            yield {
                'text': quote.xpath('span[@class="text"]/text()').get(),
                'author': quote.xpath('span/small[@class="author"]/text()').get(),
                'tags': quote.xpath('div[@class="tags"]/a[@class="tag"]/text()').getall(),
            }

        # Переход к следующей странице, если она существует
        next_page = response.xpath('//li[@class="next"]/a/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse)
