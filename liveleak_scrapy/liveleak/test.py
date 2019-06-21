# -*- coding: utf-8 -*-
import scrapy
key_word = 'fight'
url = 'https://www.liveleak.com/browse?q={}&page=1'.format(key_word)
results = scrapy.Request(url, meta={'dont_obey_robotstxt ': True})
links = scrapy.Response.xpath('/html/body/main/section[2]/div/div/div/div[1]/div[1]/div[2]')
print(links)