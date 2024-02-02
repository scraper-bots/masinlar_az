import scrapy

class MainSpider(scrapy.Spider):
    name = "turbo_az"
    allowed_domains = ["turbo.az"]
    start_urls = ["https://turbo.az/autos?page=1"]

    def parse(self, response):
        hrefs = response.css('.products-i__link::attr(href)').getall()
        for href in hrefs:
            yield scrapy.Request(
                url=response.urljoin(href),
                callback=self.parse_car_details,
                meta={"href": href}
            )

        next_button = response.css('a[rel="next"]::attr(href)').get()
        if next_button:
            yield scrapy.Request(
                url=response.urljoin(next_button),
                callback=self.parse
            )
    def parse_car_details(self, response):
        yield {
            'link'          : response.url,
            'title'         : response.css('h1.product-title::text').get(),
            'update'        : response.css('span.product-statistics__i-text::text').get(),
            'views'         : response.css('ul.product-statistics li:nth-child(2) span::text').get(),
            'city'          : response.css('label.product-properties__i-name:contains("Şəhər") + span.product-properties__i-value::text').get(),
            'make'          : response.css('label.product-properties__i-name:contains("Marka") + span.product-properties__i-value a::text').get(),
            'model'         : response.css('label.product-properties__i-name:contains("Model") + span.product-properties__i-value a::text').get(),
            'year'          : response.css('label.product-properties__i-name:contains("Buraxılış ili") + span.product-properties__i-value a::text').get(),
            'ban_type'      : response.css('label.product-properties__i-name:contains("Ban növü") + span.product-properties__i-value::text').get(),
            'colour'        : response.css('label.product-properties__i-name:contains("Rəng") + span.product-properties__i-value::text').get(),
            'engine'        : response.css('label.product-properties__i-name:contains("Mühərrik") + span.product-properties__i-value::text').get(),
            'ride'          : response.css('label.product-properties__i-name:contains("Yürüş") + span.product-properties__i-value::text').get(),
            'transmission'  : response.css('label.product-properties__i-name:contains("Sürətlər qutusu") + span.product-properties__i-value::text').get(),
            'gear'          : response.css('label.product-properties__i-name:contains("Ötürücü") + span.product-properties__i-value::text').get(),
            'is_new'        : response.css('label.product-properties__i-name:contains("Yeni") + span.product-properties__i-value::text').get(),
            'price'         : response.css('div.product-price__i--bold::text').get(),
        }

