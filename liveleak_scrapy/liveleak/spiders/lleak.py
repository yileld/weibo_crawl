# -*- coding: utf-8 -*-
import scrapy


class LleakSpider(scrapy.Spider):
    name = 'lleak'
    allowed_domains = ['liveleak.com']
    home_url = 'http://liveleak.com/'
    key_word = 'fight'
    page = 1
    start_urls = ['https://www.liveleak.com/browse?q={}&page=1'.format(key_word)]
    current_link = start_urls[0]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # pass
        try:
            links = response.xpath('//div/h3/a/@href')
            for item in links:
                link = item.extract()
                self.current_link = link
                yield scrapy.Request(url=link, callback=self.get_video_link, dont_filter=True)
        except Exception as e:
            print('#'*100 + 'no result in this page!')

        try:
            page_bar = response.xpath('/html/body/main/section[2]/div/div/div/div[1]/div[2]/nav/ul/*')[-1]
            next_page = response.xpath('//a[@aria-label="Next"]/@href').extract()[0]
            next_link = self.home_url + next_page
            self.current_link = next_link
            yield scrapy.Request(url=next_link, callback=self.parse, dont_filter=True)
        except Exception as e:
            print('#'*100 + 'no next page')
            print(e)

    def get_video_link(self, response):
        flag = 0
        try:
            video_link = response.xpath("//video/source/@src")[0].extract()
            # print('~'*100)
            # print(video_link)
            flag = 1
            filename = '{}.txt'.format(self.key_word)
            with open(filename, 'a+') as f:
                f.write(video_link + '\n')
            yield None
        except Exception as e:
            pass

        if flag == 0:
            try:
                video_link = response.xpath('//video[@class="video-stream html5-main-video"]/@src')[0].extract()[5:]
                flag = 1
                filename = '{}.txt'.format(self.key_word)
                with open(filename, 'a+') as f:
                    f.write(video_link + '\n')
                yield None
            except Exception as e:
                print('#'*100 + 'no video!')
                print(response.url)
                filename = '{}.txt'.format(self.key_word + '_youtube')
                with open(filename, 'a+') as f:
                    f.write(response.url + '\n')

    def download_video(url):
        pass