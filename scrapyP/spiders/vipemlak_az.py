import scrapy
from urllib.parse import urljoin


class CombinedSpider(scrapy.Spider):
    name = "vipemlak_az"
    allowed_domains = ["vipemlak.az"]
    start_urls = ["https://vipemlak.az/yeni-tikili/?start=1",
                  "https://vipemlak.az/kohne-tikili/?start=1",
                  "https://vipemlak.az/heyet-evi-villa/?start=1",
                  "https://vipemlak.az/obyekt-ofis/?start=1",
                  "https://vipemlak.az/torpaq/?start=1"]

    def parse(self, response):
        links = response.css('div.pranto.prodbig a::attr(href)').getall()

        for link in links:
            full_link = urljoin(response.url, link)
            yield scrapy.Request(url=full_link, callback=self.parse_phone_number)

        pagination_links = response.css('div.pagination a::attr(href)').getall()
        for link in pagination_links:
            full_pagination_link = urljoin(response.url, link)
            yield scrapy.Request(url=full_pagination_link, callback=self.parse)

    def parse_phone_number(self, response):
        phone_number = response.css('span#teldivid div#telshow::text').get()

        yield {
            'link': response.url,
            'phone_number': phone_number,
        }
