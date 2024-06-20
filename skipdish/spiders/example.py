import scrapy
from scrapy import Request
import json
from .cities import cities
import time
from pprint import pprint
from datetime import datetime
import json
from scrapy.shell import inspect_response


class skipTDSpider(scrapy.Spider):
    name = 'rest_opt'
    start_urls = ['https://www.skipthedishes.com/']
    forbidden_url_list = []
    
    def __init__(self, range_='1-172', *args, **kwargs):
        super(skipTDSpider, self).__init__(*args, **kwargs)
        list_range = range_.split('-')
        # self.start_index = int(list_range[0])-1
        self.start_index = 1
        # self.end_index = int(list_range[1])
        self.end_index = 2

    def parse(self, response):
        url = "https://api.skipthedishes.com/customer/v1/graphql"
        headers = {
          'authority': 'api.skipthedishes.com',
          'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
          'parameters': 'isCuisineSearch=false&isSorted=false&search=',
          'accept-language': 'en',
          'sec-ch-ua-mobile': '?0',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
          'app-token': 'd7033722-4d2e-4263-9d67-d83854deb0fc',
          'content-type': 'application/json',
          'accept': '*/*',
          'sec-ch-ua-platform': '"macOS"',
          'origin': 'https://www.skipthedishes.com',
          'sec-fetch-site': 'same-site',
          'sec-fetch-mode': 'cors',
          'sec-fetch-dest': 'empty',
          'referer': 'https://www.skipthedishes.com/',
          # 'Cookie': 'incap_ses_1364_1682717=ZpXfA5TdVEBg19sgDuftEv9CcmEAAAAA0OuqeOMvr/+exd6sUzMndQ==; nlbi_1682717=L+6XY4oEFAlaYum59S3QRQAAAAB6GWB4zDpHq66EDwurTrSD; visid_incap_1682717=I3dnnNPjSWiWcHTzjn+rPe9CcmEAAAAAQUIPAAAAAAA56A+0Ygm9LIr/jL/D4wN0'
        }
        for city in cities[self.start_index:self.end_index]:
            pr = city['provinceCode']
            ct = city['name']
            ct = 'brandon'
            pr = 'MB'
            payload = json.dumps({
              "operationName": "QueryRestaurantsCuisinesList",
              "variables": {
                "city": ct,
                "province": pr,
                "latitude": 0,
                "longitude": 0,
                "isDelivery": True,
                "dateTime": 0,
                "search": "",
                "language": "en"
              },
              "extensions": {
                "persistedQuery": {
                  "version": 1,
                  "sha256Hash": "db6673834fe29b38eafc77331b9aaeefec487d79079835ffb53866a7e0b129c1"
                }
              }
            })
            yield scrapy.Request(url, method='POST', 
                        headers=headers, 
                        body=payload, 
                        dont_filter=True,
                        callback=self.parse_restaurant_list)
            break


    def parse_restaurant_list(self, response):
        inspect_response(response,self)
        resp = json.loads(response.body)
        restaurants = resp['data']['restaurantsList']['openRestaurants']
        restaurants.extend(resp['data']['restaurantsList']['closedRestaurants'])
        headers = {
            'authority': 'api-skipthedishes.skipthedishes.com',
            'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
            'accept-language': 'en',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'app-token': 'd7033722-4d2e-4263-9d67-d83854deb0fc',
            'content-type': 'application/json',
            'accept': 'application/json',
            'sec-ch-ua-platform': '"macOS"',
            'origin': 'https://www.skipthedishes.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.skipthedishes.com/',
        }
        for rest in restaurants:
            url_slug = rest['cleanUrl']
            url = f'https://api-skipthedishes.skipthedishes.com/v1/restaurants/clean-url/{url_slug}?fullMenu=true&language=en'
            yield scrapy.Request(url, headers=headers, callback=self.parse_restaurant)
            break

    
    def parse_restaurant(self, response):
        inspect_response(response,self)
        data = json.loads(response.body)

        id = data['id']
        name = data['name']
        _loc = data['location']
        address = _loc['address']
        city = _loc['city']
        province = _loc['province']
        country = _loc['country']
        postal_code = _loc['postalCode']
        latitude = _loc['latitude']
        longitude = _loc['longitude']
        skipscore = data['skipScore']
        cuisines = ', '.join(data['cuisines'])
        _info = data['contactInfo']
        email = _info['email']
        phone = _info['phoneNumber']
        _cleanUrl = data['cleanUrl']
        pageurl = f'https://www.skipthedishes.com/{_cleanUrl}'
        image_urls = [v for k,v in data['imageUrls'].items()]
        image_urls = ', '.join([i for i in image_urls]) if image_urls else None
        try:
            delivery_cost = data['fees'][0]['feeCents']
            print("Delivery Cost is: ", delivery_cost)
            delivery_cost = delivery_cost / 100 if delivery_cost else delivery_cost
            min_order_amount = data['fees'][0]['orderMinimumCents']
            print("Minimum Order Amount is: ", min_order_amount)
            min_order_amount = min_order_amount / 100 if min_order_amount else min_order_amount
        except Exception as e:
            print(e)
            delivery_cost = None
            min_order_amount = None
        rating = data['skipScore'] / 10

        # restaurant_resp_item = {
        #     'restaurant_id' : id,
        #     'restaurant_resp' : response.body
        # }
        # yield restaurant_resp_item

        hours = json.dumps(data['hours'], indent=4)
        rest_item = {
            'name' : name,
            'address' : address,
            'city' : city,
            'province' : province,
            'country' : country,
            'postal_code' : postal_code,
            'latitude' : latitude,
            'longitude' : longitude,
            'skipscore' : skipscore,
            'cuisines' : cuisines,
            'email' : email,
            'phone' : phone,
            'restaurant_url' : pageurl,
            'restaurant_id' : id,
            'restaurant_images' : image_urls,
            'restaurant_hours' : hours,
            # 'restaurant_json' : None,
            'delivery_cost' : delivery_cost,
            'min_order_amount' : min_order_amount,
            'rating' : rating,
        }
        
        yield rest_item
        currency = data['currency']['currencyCode']
        
        mitem = {
            'source' : []
        }
        menu_ids = []
        for group in data['menu']['menuGroups']:
            meal_category = group['name']
            for item in group['menuItems']:
                meal_id = item['id']
                meal_name = item['name']
                meal_category = meal_category
                meal_price = str(item['centsPrice'] / 100)
                meal_description = item['description']

                menu_item = {
                    'restaurant_name' : name,
                    'restaurant_url' : pageurl,
                    'restaurant_id' : id,
                    'meal_id' : meal_id,
                    'meal_name' : meal_name,
                    'meal_category' : meal_category,
                    'meal_price' : meal_price,
                    'meal_description' : meal_description,
                    'currency' : currency
                }
                mitem['source'].append(menu_item)
                menu_ids.append(meal_id)

        yield mitem

        if not menu_ids:
            json_response_item = {
            'restaurant_id' : id,
            'restaurant_resp' : json.dumps(data, indent=4)
            }
            yield json_response_item
        else:
            menu_id = menu_ids.pop()
            timestamp = round(datetime.utcnow().timestamp())
            url = f'https://api-skipthedishes.skipthedishes.com/v1/restaurants/{id}/menuitems/{menu_id}?order_type=DELIVERY&order_time={timestamp}'
            
            headers = {
                'authority': 'api-skipthedishes.skipthedishes.com',
                'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
                'accept-language': 'en',
                'sec-ch-ua-mobile': '?0',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
                'app-token': 'd7033722-4d2e-4263-9d67-d83854deb0fc',
                'content-type': 'application/json',
                'accept': 'application/json',
                'sec-ch-ua-platform': '"macOS"',
                'origin': 'https://www.skipthedishes.com',
                'sec-fetch-site': 'same-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.skipthedishes.com/',
            }

            yield scrapy.Request(url,
                                headers=headers, 
                                meta={'menu_id':menu_id,
                                    'json_resp':data,
                                    'restaurant_id':id,
                                    'menu_ids':menu_ids,
                                    },
                                callback=self.option_data
            )

    def option_data(self,response):
        menu_id = response.meta.get('menu_id')
        json_resp = response.meta.get('json_resp')
        restaurant_id = response.meta.get('restaurant_id')
        menu_ids = response.meta.get('menu_ids')

        data = json.loads(response.body)
        option_items = {
            'options' : []
        }
        for group in json_resp['menu']['menuGroups']:
            for item in group['menuItems']:
                if item.get('id')==menu_id:
                    print('\n\nadding option data to restaurant json',menu_id,'\n\n\n')
                    item['options'] = data
                    pprint(f'\n {item}\n')
        
        for option_group in data['options']:
            option_group_name = option_group['name']
            for option in option_group['options']:
                option_id = option['id']
                option_name = option['name']
                option_price = option.get('centsPriceModifier')
                if option_price:
                    option_price = str(option_price / 100)
                item = {
                    'restaurant_id': restaurant_id,
                    'meal_id' : response.meta.get('meal_id'),
                    'meal_name' : response.meta.get('meal_name'),
                    'option_group' : option_group_name,
                    'option_id' : option_id,
                    'option_name' : option_name,
                    'option_price' : option_price,
                }
                option_items['options'].append(item)
        yield option_items

        
        headers = {
            'authority': 'api-skipthedishes.skipthedishes.com',
            'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
            'accept-language': 'en',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'app-token': 'd7033722-4d2e-4263-9d67-d83854deb0fc',
            'content-type': 'application/json',
            'accept': 'application/json',
            'sec-ch-ua-platform': '"macOS"',
            'origin': 'https://www.skipthedishes.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.skipthedishes.com/',
        }

        if menu_ids:
            menu_id=menu_ids.pop()
            timestamp = round(datetime.utcnow().timestamp())
            url = f'https://api-skipthedishes.skipthedishes.com/v1/restaurants/{restaurant_id}/menuitems/{menu_id}?order_type=DELIVERY&order_time={timestamp}'
            yield scrapy.Request(url,
                                headers=headers, 
                                meta={'menu_id':menu_id,
                                    'json_resp':json_resp,
                                    'menu_ids':menu_ids,
                                    'restaurant_id':restaurant_id,
                                    },
                                callback=self.option_data
            )
        
        else:
            json_response_item = {
            'restaurant_id' : restaurant_id,
            'restaurant_resp' : json.dumps(json_resp, indent=4)
            }
            yield json_response_item