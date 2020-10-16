import json
import os

import scrapy
import logging

logger = logging.getLogger(__name__)


class AcerSpider(scrapy.Spider):
    name = 'acer'
    start_urls = ['http://store.acer.com/en-ph/']

    def __init__(self):
        self.categories = {}
        self.products = {}

    def get_categories(self, response):
        navbar = response.xpath('//*[@id="store.menu"]/div/ul')
        for li in navbar.css('li'):
            cat_name = li.css('a.level-top span::text').get()
            if cat_name:
                self.categories[cat_name] = {
                    'url': li.css('a.level-top::attr(href)').get(),
                    'sub-categories': {}
                }
                for subcat in li.css('ul li'):
                    self.categories[cat_name]['sub-categories'][subcat.css('a span::text').get()] = {
                        'url': subcat.css('a::attr(href)').get()
                    }
        with open('c.json', 'w') as f:
            f.write(json.dumps(self.categories))
        os.system('python -m json.tool c.json categories.json')
        os.system('rm c.json')

    def get_detailed_specs(self, response):
        detailed_specs = {}
        cat = response.meta.get('cat')
        subcat = response.meta.get('subcat')
        table = response.xpath('//*[@id="product-attribute-specs-table"]/tbody')
        for row in table.css('tr'):
            print(row.get())
            label = row.css('th.label::text').get()
            data = row.css('td.data::text').get()
            if None in [label, data]:
                pass
            else:
                detailed_specs[label] = data
        name = response.xpath('//*[@id="maincontent"]/div[2]/div/div[1]/div/div[1]/div[2]/div/div[1]/div[1]/div[1]/h1/span//text()')[0].extract()
        if '|' in name:
            name = name.split('|')[0]
        if subcat:
            items = self.products[cat]['sub-categories'][subcat]['items']
            for item in items:
                print('item name', item['name'])
                print('name', name)
                if item['name'] == name:
                    item['detailed_specs'] = detailed_specs
        else:
            items = self.products[cat]['items']
            for item in items:
                print('item name', item['name'])
                print('name', name)
                if item['name'] == name:
                    item['detailed_specs'] = detailed_specs
        with open('a.json', 'w') as f:
            f.write(json.dumps(self.products))
        os.system('python -m json.tool a.json products.json')
        os.system('rm a.json')
        yield self.products



    def parse_categories(self, response):
        cat = response.meta.get('cat')
        subcat = response.meta.get('subcat')
        print('parsing categories...')
        self.products[cat] = self.categories[cat]
        product_items = response.xpath('//*[@id="maincontent"]/div[2]/div[1]/div[4]/ol')
        if subcat:
            self.products[cat]['sub-categories'][subcat]['items'] = []
        else:
            self.products[cat]['items'] = []
        for item in product_items.css('li'):
            link = item.css('div div div a::attr(href)').get()
            image = item.css('div div div a span span img::attr(src)').get()
            details = item.css('div.product-item-details div.products-textlink h2 a::text').get()
            price = item.css('div.product-item-details div.product-item-inner div.price-box span.price::text').get()
            if details:
                print('category...', cat)
                print('sub-category...', subcat)
                print('details...', details)
                details = details.replace('\n', '').strip()
                if '|' in details:
                    name = details.split('|')[0]
                    name_specs = details.split('|')[1]
                else:
                    name = details
                    name_specs = ''
            quickspecs = item.css('div.product-item-details div.product-item-description ul.quickspecs li::text').getall()
            detailed_specs_link = item.css('div.product-item-details div.product-item-description a::attr(href)').get()
            if None in [link, image, details, quickspecs, price]:
                pass
            else:
                logger.debug('link %s', link)
                logger.debug('image %s', image)
                logger.debug('name %s', name)
                logger.debug('name specs %s', name_specs)
                logger.debug('quickspecs %s', quickspecs)
                logger.debug('price %s', price)
                logger.debug('detailed_specs_link %s', detailed_specs_link)
                if subcat:
                    self.products[cat]['sub-categories'][subcat]['items'].append({
                        'link': link,
                        'image': image,
                        'name': name,
                        'name_specs': name_specs,
                        'quickspecs': quickspecs,
                        'detailed_specs_link': detailed_specs_link,
                        'price': price
                    })
                else:
                    self.products[cat]['items'].append({
                        'link': link,
                        'image': image,
                        'name': name,
                        'name_specs': name_specs,
                        'quickspecs': quickspecs,
                        'detailed_specs_link': detailed_specs_link,
                        'price': price
                    })
        # yield self.products
        with open('a.json', 'w') as f:
            f.write(json.dumps(self.products))
        os.system('python -m json.tool a.json products.json')
        os.system('rm a.json')
        for k, v in self.products.items():
            if v['sub-categories']:
                for a, b in v['sub-categories'].items():
                    # yield self.test_parse(k, a)
                    if 'items' in b:
                        for x in b['items']:
                            if 'detailed_specs_link' in x:
                                next_page = response.urljoin(x['detailed_specs_link'])
                                yield scrapy.Request(next_page, callback=self.get_detailed_specs, dont_filter=False, meta={'cat': k, 'subcat': a})
            else:
                # no sub-category found... using root link instead
                if k in ['Accesories', 'Business']:
                    pass
                else:
                    # yield self.test_parse(k)
                    if 'items' in v:
                        for x in v['items']:
                            if 'detailed_specs_link' in x:
                                next_page = response.urljoin(x['detailed_specs_link'])
                                yield scrapy.Request(next_page, callback=self.get_detailed_specs, dont_filter=False, meta={'cat': k})

    def parse(self, response):
        self.get_categories(response)
        for k, v in self.categories.items():
            if v['sub-categories']:
                for a, b in v['sub-categories'].items():
                    # yield self.test_parse(k, a)
                    next_page = response.urljoin(b['url'])
                    yield scrapy.Request(next_page, callback=self.parse_categories, dont_filter=False, meta={'cat': k, 'subcat': a})
            else:
                # no sub-category found... using root link instead
                if k == 'Accesories':
                    pass
                else:
                    # yield self.test_parse(k)
                    next_page = response.urljoin(v['url'])
                    yield scrapy.Request(next_page, callback=self.parse_categories, dont_filter=False, meta={'cat': k})