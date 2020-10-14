import json
import os

import scrapy
import logging

logger = logging.getLogger(__name__)


class AcerSpider(scrapy.Spider):
    name = 'acer'
    start_urls = ['http://store.acer.com/en-ph/']

    def get_categories(self, response):
        self.products = {}
        navbar = response.xpath('//*[@id="store.menu"]/div/ul')
        for li in navbar.css('li'):
            cat_name = li.css('a.level-top span::text').get()
            if cat_name:
                self.products[cat_name] = {
                    'url': li.css('a.level-top::attr(href)').get(),
                    'sub-categories': {}
                }
                for subcat in li.css('ul li'):
                    self.products[cat_name]['sub-categories'][subcat.css('a span::text').get()] = {
                        'url': subcat.css('a::attr(href)').get()
                    }

    def parse_categories(self, response, current_cat, current_subcat=None):
        print('parsing rootcategories...')
        product_items = response.xpath('//*[@id="maincontent"]/div[2]/div[1]/div[4]/ol')
        if current_subcat:
            self.products[current_cat]['sub-categories'][current_subcat]['items'] = []
        else:
            self.products[current_cat]['items'] = []
        for item in product_items.css('li'):
            link = item.css('div div div a::attr(href)').get()
            image = item.css('div div div a span span img::attr(src)').get()
            details = item.css('div.product-item-details div.products-textlink h2 a::text').get()
            if details:
                print('details...', details)
                details = details.replace('\n', '').strip()
                if '|' in details:
                    name = details.split('|')[0]
                    name_specs = details.split('|')[1]
                else:
                    name = details
                    name_specs = ''
            listed_specs = item.css('div.product-item-details div.product-item-description ul li::text').getall()
            if None in [link, image, details, listed_specs]:
                pass
            else:
                logger.debug('link %s', link)
                logger.debug('image %s', image)
                logger.debug('name %s', name)
                logger.debug('name specs %s', name_specs)
                logger.debug('listed_specs %s', listed_specs)
                if current_subcat:
                    self.products[current_cat]['sub-categories'][current_subcat]['items'].append({
                        'link': link,
                        'image': image,
                        'name': name,
                        'name_specs': name_specs,
                        'listed_specs': listed_specs
                    })
                else:
                    self.products[current_cat]['items'].append({
                        'link': link,
                        'image': image,
                        'name': name,
                        'name_specs': name_specs,
                        'listed_specs': listed_specs
                    })
        # yield self.products
        with open('a.json', 'w') as f:
            f.write(json.dumps(self.products))
        os.system('python -m json.tool a.json products.json')
        os.system('rm a.json')

    def parse(self, response):
        self.get_categories(response)
        for k, v in self.products.items():
            if v['sub-categories']:
                for a, b in v['sub-categories'].items():
                    # sub-categories exists...
                    next_page = response.urljoin(b['url'])
                    yield scrapy.Request(next_page, callback=self.parse_categories(response, k, a), dont_filter=True)
            else:
                # no sub-category found... using root link instead
                yield scrapy.Request(v['url'], callback=self.parse_categories(response, k), dont_filter=True)
