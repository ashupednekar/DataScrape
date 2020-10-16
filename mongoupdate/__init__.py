import json

import requests


class AcerMongoClient:
    def __init__(self):
        from pymongo import MongoClient
        client = MongoClient(host='training1.bankbuddy.me', port=27017, username='buddy', password='bankbuddy')
        db_name = 'acer_database'
        db = client[db_name]
        self.faq_search_col = db['faq_search']
        self.products_search_col = db['products_search']
        self.images_search_col = db['images_search']

    def get_faq_image(self, name, model_no, price, image_url, client='acer', file_type='jpg', txn_template='product_faq'):
        product_faq_payload = {
            "client": client,
            "file_type": file_type,
            "txn_template": txn_template,
            "data": {
                "name": name,
                "model_no": model_no,
                "price": price,
                "image_url": image_url
            }
        }
        generated_image_url = requests.post(
            url='http://localhost:8989/img_gen',
            data=json.dumps(product_faq_payload),
            headers={'Content-Type': 'application/json'}
        ).text
        return generated_image_url
        # return json.dumps({'path': ''})


    def import_images_search_data(self, file_path='../acerph/products.json'):
        import json
        with open(file_path) as f:
            data = json.loads(f.read())

        for k, v in data.items():
            if k == 'Laptop':
                category = 'notebooks'
            elif k == 'Projector':
                category = 'projectors'
            else:
                category = k.lower()
            if v['sub-categories']:
                for a, b in v['sub-categories'].items():
                    # print(v['sub-categories'])
                    tm = a
                    # print('PPPPPPPP', a)
                    if 'items' in b:
                        for x in b['items']:
                            # print('QQQQQQQQ', a)
                            # print('TTTTTTTT', tm)
                            sub_product = x['name'].lower()
                            if sub_product in ['aopen 24ml1y', 'aopen 24hc1qr pbidpx']:
                                sub_category = 'affordable'
                            elif sub_product in ['ka220hqavbid', 'predator xb241h bmipr', 'aopen 27hc1r pbidpx', 'aopen 32hc1qur pbidpx']:
                                sub_category = 'consumer'
                            elif sub_product in ['helios 300 ph315-53-73rt', 'nitro 5 an515-43-r2wk',
                                                 'nitro 7 an715-51-58x1',
                                                 'predator triton 500 pt515-52-75zy']:
                                sub_category = 'high performance'
                            elif sub_product in ['aspire 3 a315-56-596k', 'aspire 5 a514-52k-39ad']:
                                sub_category = 'best sellers'
                            elif 'nitro 50' in sub_product:
                                sub_category = 'predator'
                            elif sub_product in ['acer x1126h', 'c250i', 'c202i', 'x118h', 'x1126ah', 'p6500', 's1386whn']:
                                sub_category = 'wider displays'
                            else:
                                sub_category = tm.lower()
                            ################################################
                            if sub_product in ['acer x1126h', 'c250i', 'c202i', 'x118h', 'x1126ah', 'p6500', 's1386whn']:
                                product = 'wider displays'
                            elif 'spin' in sub_product:
                                product = 'spin'
                            elif sub_product in ['ka220hqavbid']:
                                product = 'aopen 24'
                            elif sub_product.startswith('aopen'):
                                product = 'aopen 24'
                            elif sub_product.startswith('altos'):
                                product = 'altos'
                            elif sub_product.startswith('aspire c24'):
                                product = 'aspire c24'
                            elif sub_product.startswith('aspire c22'):
                                product = 'aspire c22'
                            elif sub_product.startswith('aspire tc'):
                                product = 'aspire tc'
                            elif sub_product.startswith('predator'):
                                product = 'predator xb'
                            elif 'nitro 50' in sub_product:
                                product = 'predator xb'
                            elif 'helios 300' in sub_product:
                                product = 'Helios 300'
                            elif 'triton 500' in sub_product:
                                product = 'Triton 500'
                            elif len(sub_product.split(' ')) > 1:
                                if len(sub_product.split(' ')[1]) == 1:
                                    # aspire 5 jbvdkjbjkv
                                    product = ' '.join(sub_product.split(' ')[:2])
                                elif '-' in sub_product.split(' ')[1]:
                                    # aspire tc-djdkslvdlk
                                    product = sub_product.split('-')[0]
                                else:
                                    product = sub_product
                            else:
                                product = sub_product
                            buy_now_url = x['link']
                            image_url = json.loads(self.get_faq_image(
                                client='acer',
                                file_type='jpg',
                                txn_template='product_faq',
                                name=' '.join(x['name'].split(' ')[:-1]),
                                model_no= x['name'].split(' ')[-1],
                                price=x['price'].replace('₱', ''),
                                image_url=x['image']
                            )).get('path')
                            print(
                                category + '|' + product + '|' + sub_category + '|' + sub_product + ' | ' + buy_now_url + ' | ' + image_url)
                            if product not in ['altos', 'spin']:
                                query = {
                                    'Category': category,
                                    'Product': product,
                                    'Sub Category': sub_category,
                                    'Sub Product': sub_product
                                }
                                changes = {'$set': {}}
                                changes['$set'] = {
                                    'buy_now_url': buy_now_url,
                                    'image_url': image_url
                                }
                                self.images_search_col.update_one(
                                    filter=query,
                                    update=changes,
                                    upsert=True
                                )
                                detailedspecs = x['detailed_specs']
                                prchanges = {'$set': {}}
                                # print(x['name'])
                                if detailedspecs.get('Maximum Battery Run Time'):
                                    battery_life = detailedspecs.get('Maximum Battery Run Time').lower().replace('hour', 'hr')
                                else:
                                    for a in x['quickspecs']:
                                        if 'battery life' in a:
                                            battery_life = a.replace('hour', 'hr')
                                        else:
                                            battery_life = ''
                                print(detailedspecs)
                                if detailedspecs.get('Graphics Memory Accessibility'):
                                    graphics_type = detailedspecs.get('Graphics Memory Accessibility').lower()
                                else:
                                    graphics_type = ''
                                if detailedspecs.get('Total Hard Drive Capacity'):
                                    hdd_space = detailedspecs.get('Total Hard Drive Capacity').lower()
                                else:
                                    hdd_space = ''
                                if detailedspecs.get('Standard Memory'):
                                    ram = detailedspecs.get('Standard Memory').lower()
                                else:
                                    ram = ''
                                if detailedspecs.get('Processor Type'):
                                    cpu = detailedspecs.get('Processor Type').lower()
                                else:
                                    cpu = ''
                                if detailedspecs.get('Total Solid State Drive Capacity'):
                                    ssd_space = detailedspecs.get('Total Solid State Drive Capacity').lower()
                                else:
                                    ssd_space = ''
                                if detailedspecs.get('Operating System'):
                                    operating_system = detailedspecs.get('Operating System').lower()
                                else:
                                    operating_system = ''
                                if detailedspecs.get('Screen Size'):
                                    screen_size = detailedspecs.get('Screen Size').lower().split(' (')[1].replace(')', '')
                                else:
                                    screen_size = ''
                                query = {
                                    'Category': category,
                                    'Product': product,
                                    'Sub Category': sub_category,
                                    'Sub Product': sub_product
                                }
                                prchanges['$set'] = {
                                    'Battery': battery_life,
                                    'Graphics Memory Accessibility': graphics_type,
                                    'Hard Drive': hdd_space,
                                    'Memory': ram,
                                    'Processor': cpu,
                                    'SSD capacity': ssd_space,
                                    'Screen Size': screen_size,
                                    'operating system': operating_system,
                                    'Price': int(x.get('price').replace(',', '').replace('₱', '').strip()),
                                }
                                self.products_search_col.update_one(
                                    filter=query,
                                    update=prchanges,
                                    upsert=True
                                )
                                query = {
                                    'Category': category,
                                    'Product': product,
                                    'Sub_Category': sub_category,
                                    'Sub_Product': sub_product
                                }
                                product_desc = '|||'.join(x['quickspecs'])
                                with open('standard_answers.json', 'r') as f:
                                    standard_answers = json.loads(f.read())
                                prchanges['$set'] = {
                                    'Default_image': 'https://whatsapp-img.s3.amazonaws.com/ocr-media/notebook-G.png',
                                    'Sub_Product_Description': product_desc,
                                    'Sub_Product_image': json.loads(self.get_faq_image(
                                        client='acer',
                                        file_type='jpg',
                                        txn_template='product_faq',
                                        name=' '.join(x['name'].split(' ')[:-1]),
                                        model_no= x['name'].split(' ')[-1],
                                        price=x['price'].replace('₱', ''),
                                        image_url=x['image']
                                    )).get('path'),
                                    'Sub_Product_buy_now_url': x['link'],
                                    'Price': standard_answers[product.lower()]['Price'],
                                    'Graphics Memory Accessibility': standard_answers[product.lower()]['Graphics Memory Accessibility'],
                                    'Hard Drive': standard_answers[product.lower()]['Hard Drive'],
                                    'SSD capacity': standard_answers[product.lower()]['SSD capacity'],
                                    'Screen Size': standard_answers[product.lower()]['Screen Size'],
                                    'Battery': standard_answers[product.lower()]['Battery'],
                                    'operating system': standard_answers[product.lower()]['operating system'],
                                    'Processor': standard_answers[product.lower()]['Processor'],
                                    'Memory': standard_answers[product.lower()]['Memory'],
                                }
                                self.faq_search_col.update_one(
                                    filter=query,
                                    update=prchanges,
                                    upsert=True
                                )
            else:
                tm = k
                # print('PPPPPPPP', a)
                if 'items' in v:
                    for x in v['items']:
                        # print('QQQQQQQQ', a)
                        # print('TTTTTTTT', tm)
                        sub_product = x['name'].lower()
                        if sub_product in ['aopen 24ml1y', 'aopen 24hc1qr pbidpx']:
                            sub_category = 'affordable'
                        elif sub_product in ['ka220hqavbid', 'predator xb241h bmipr', 'aopen 27hc1r pbidpx', 'aopen 32hc1qur pbidpx']:
                            sub_category = 'consumer'
                        elif sub_product in ['helios 300 ph315-53-73rt', 'nitro 5 an515-43-r2wk',
                                             'nitro 7 an715-51-58x1',
                                             'predator triton 500 pt515-52-75zy']:
                            sub_category = 'high performance'
                        elif sub_product in ['aspire 3 a315-56-596k', 'aspire 5 a514-52k-39ad']:
                            sub_category = 'best sellers'
                        elif 'nitro 50' in sub_product:
                            sub_category = 'predator'
                        elif sub_product in ['acer x1126h', 'c250i', 'c202i', 'x118h', 'x1126ah', 'p6500', 's1386whn']:
                            sub_category = 'wider displays'
                        else:
                            sub_category = tm.lower()
                        ################################################
                        if sub_product in ['acer x1126h', 'c250i', 'c202i', 'x118h', 'x1126ah', 'p6500', 's1386whn']:
                            product = 'wider displays'
                        elif sub_product in ['ka220hqavbid']:
                            product = 'consumer'
                        elif sub_product.startswith('aopen'):
                            product = 'aopen 24'
                        elif sub_product.startswith('altos'):
                            product = 'altos'
                        elif sub_product.startswith('aspire c24'):
                            product = 'aspire c24'
                        elif sub_product.startswith('aspire c22'):
                            product = 'aspire c22'
                        elif sub_product.startswith('aspire tc'):
                            product = 'aspire tc'
                        elif sub_product.startswith('predator'):
                            product = 'predator xb'
                        elif 'nitro 50' in sub_product:
                            product = 'predator xb'
                        elif 'helios 300' in sub_product:
                            product = 'Helios 300'
                        elif 'triton 500' in sub_product:
                            product = 'Triton 500'
                        elif len(sub_product.split(' ')) > 1:
                            if len(sub_product.split(' ')[1]) == 1:
                                # aspire 5 jbvdkjbjkv
                                product = ' '.join(sub_product.split(' ')[:2])
                            elif '-' in sub_product.split(' ')[1]:
                                # aspire tc-djdkslvdlk
                                product = sub_product.split('-')[0]
                            else:
                                product = sub_product
                        else:
                            product = sub_product
                        buy_now_url = x['link']
                        image_url = json.loads(self.get_faq_image(
                            client='acer',
                            file_type='jpg',
                            txn_template='product_faq',
                            name=' '.join(x['name'].split(' ')[:-1]),
                            model_no=x['name'].split(' ')[-1],
                            price=x['price'].replace('₱', ''),
                            image_url=x['image']
                        )).get('path')
                        print(
                            category + '|' + product + '|' + sub_category + '|' + sub_product + ' | ' + buy_now_url + ' | ' + image_url)
                        if product not in ['altos']:
                            query = {
                                'Category': category,
                                'Product': product,
                                'Sub Category': sub_category,
                                'Sub Product': sub_product
                            }
                            changes = {'$set': {}}
                            changes['$set'] = {
                                'buy_now_url': buy_now_url,
                                'image_url': image_url
                            }
                            self.images_search_col.update_one(
                                filter=query,
                                update=changes,
                                upsert=True
                            )
                            detailedspecs = x['detailed_specs']
                            prchanges = {'$set': {}}
                            # print(x['name'])
                            if detailedspecs.get('Maximum Battery Run Time'):
                                battery_life = detailedspecs.get('Maximum Battery Run Time').lower().replace('hour',
                                                                                                             'hr')
                            else:
                                for a in x['quickspecs']:
                                    if 'battery life' in a:
                                        battery_life = a.replace('hour', 'hr')
                                    else:
                                        battery_life = ''
                            print(detailedspecs)
                            if detailedspecs.get('Graphics Memory Accessibility'):
                                graphics_type = detailedspecs.get('Graphics Memory Accessibility').lower()
                            else:
                                graphics_type = ''
                            if detailedspecs.get('Total Hard Drive Capacity'):
                                hdd_space = detailedspecs.get('Total Hard Drive Capacity').lower()
                            else:
                                hdd_space = ''
                            if detailedspecs.get('Standard Memory'):
                                ram = detailedspecs.get('Standard Memory').lower()
                            else:
                                ram = ''
                            if detailedspecs.get('Processor Type'):
                                cpu = detailedspecs.get('Processor Type').lower()
                            else:
                                cpu = ''
                            if detailedspecs.get('Total Solid State Drive Capacity'):
                                ssd_space = detailedspecs.get('Total Solid State Drive Capacity').lower()
                            else:
                                ssd_space = ''
                            if detailedspecs.get('Operating System'):
                                operating_system = detailedspecs.get('Operating System').lower()
                            else:
                                operating_system = ''
                            if detailedspecs.get('Screen Size'):
                                screen_size = detailedspecs.get('Screen Size').lower().split(' (')[1].replace(')', '')
                            else:
                                screen_size = ''
                            query = {
                                'Category': category,
                                'Product': product,
                                'Sub Category': sub_category,
                                'Sub Product': sub_product
                            }
                            prchanges['$set'] = {
                                'Battery': battery_life,
                                'Graphics Memory Accessibility': graphics_type,
                                'Hard Drive': hdd_space,
                                'Memory': ram,
                                'Processor': cpu,
                                'SSD capacity': ssd_space,
                                'Screen Size': screen_size,
                                'operating system': operating_system,
                                'Price': int(x.get('price').replace(',', '').replace('₱', '').strip()),
                            }
                            self.products_search_col.update_one(
                                filter=query,
                                update=prchanges,
                                upsert=True
                            )
                            query = {
                                'Category': category,
                                'Product': product,
                                'Sub_Category': sub_category,
                                'Sub_Product': sub_product
                            }
                            product_desc = '|||'.join(x['quickspecs'])
                            with open('standard_answers.json', 'r') as f:
                                standard_answers = json.loads(f.read())
                            prchanges['$set'] = {
                                'Default_image': 'https://whatsapp-img.s3.amazonaws.com/ocr-media/notebook-G.png',
                                'Sub_Product_Description': product_desc,
                                'Sub_Product_image': json.loads(self.get_faq_image(
                                    client='acer',
                                    file_type='jpg',
                                    txn_template='product_faq',
                                    name=' '.join(x['name'].split(' ')[:-1]),
                                    model_no=x['name'].split(' ')[-1],
                                    price=x['price'].replace('₱', ''),
                                    image_url=x['image']
                                )).get('path'),
                                'Sub_Product_buy_now_url': x['link'],
                                'Price': standard_answers[product.lower()]['Price'],
                                'Graphics Memory Accessibility': standard_answers[product.lower()][
                                    'Graphics Memory Accessibility'],
                                'Hard Drive': standard_answers[product.lower()]['Hard Drive'],
                                'SSD capacity': standard_answers[product.lower()]['SSD capacity'],
                                'Screen Size': standard_answers[product.lower()]['Screen Size'],
                                'Battery': standard_answers[product.lower()]['Battery'],
                                'operating system': standard_answers[product.lower()]['operating system'],
                                'Processor': standard_answers[product.lower()]['Processor'],
                                'Memory': standard_answers[product.lower()]['Memory'],
                            }
                            self.faq_search_col.update_one(
                                filter=query,
                                update=prchanges,
                                upsert=True
                            )


client = AcerMongoClient()
client.import_images_search_data('../acerph/products.json')
