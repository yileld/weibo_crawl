# coding=utf-8

"""  
Created on 2016-04-28 
@author: xuzhiyuan

功能: 爬取新浪微博的搜索结果,支持高级搜索中对搜索时间的限定
网址：http://s.weibo.com/
实现：采取selenium测试工具，模拟微博登录，结合PhantomJS/Firefox，分析DOM节点后，采用Xpath对节点信息进行获取，实现重要信息的抓取

"""
import requests
import pdb
import time
import datetime
import re            
import os    
import sys  
import codecs  
import shutil
import urllib 
from selenium import webdriver        
from selenium.webdriver.common.keys import Keys        
import selenium.webdriver.support.ui as ui        
from selenium.webdriver.common.action_chains import ActionChains
import xlwt
from functools import reduce
import random

#先调用无界面浏览器PhantomJS或Firefox    
#driver = webdriver.PhantomJS()
driver = webdriver.Firefox()
# driver = webdriver.Firefox(executable_path='C:\Program Files\Mozilla Firefox\geckodriver')


#********************************************************************************
#                            第一步: 登陆login.sina.com
#                     这是一种很好的登陆方式，有可能有输入验证码
#                          登陆之后即可以登陆方式打开网页
#********************************************************************************

def LoginWeibo(username, password):
    try:
        #输入用户名/密码登录
        print(u'准备登陆Weibo.cn网站...')
        driver.get("http://login.sina.com.cn/")
        elem_user = driver.find_element_by_name("username")
        elem_user.send_keys(username) #用户名
        elem_pwd = driver.find_element_by_name("password")
        elem_pwd.send_keys(password)  #密码
        elem_sub = driver.find_element_by_xpath("//input[@class='W_btn_a btn_34px']")
        elem_sub.click()              #点击登陆 因无name属性

        try:
            #输入验证码
            time.sleep(10)
            elem_sub.click() 
        except:
            #不用输入验证码
            pass

        #获取Coockie 推荐资料：http://www.cnblogs.com/fnng/p/3269450.html
        print('Crawl in ', driver.current_url)
        # print(u'输出Cookie键值对信息:')
        # for cookie in driver.get_cookies(): 
        #     print(cookie)
        #     for key in cookie:
        #         print(key, cookie[key])
        print(u'登陆成功...')
    except Exception as e:      
        print("Error: ",e)
    finally:    
        print(u'End LoginWeibo!\n')

#********************************************************************************
#                  第二步: 访问http://s.weibo.com/页面搜索结果
#               输入关键词、时间范围，得到所有微博信息、博主信息等
#                     考虑没有搜索结果、翻页效果的情况
#********************************************************************************    

def GetSearchContent(ori_key):
    global key
    key = ori_key
    driver.get("http://s.weibo.com/")
    print('搜索热点主题：', key)

    #输入关键词并点击搜索
    # item_inp = driver.find_element_by_xpath("//input[@class='searchInp_form']")
    item_inp = driver.find_element_by_xpath("//input[@node-type='text']")
    item_inp.send_keys(key)
    elem_sub = driver.find_element_by_xpath("//button[@class='s-btn-b']")
    elem_sub.click() 
    # item_inp.send_keys(Keys.RETURN)    #采用点击回车直接搜索

    #获取搜索词的URL，用于后期按时间查询的URL拼接
    current_url = driver.current_url
    current_url = current_url.split('&')[0] #http://s.weibo.com/weibo/%25E7%258E%2589%25E6%25A0%2591%25E5%259C%25B0%25E9%259C%2587

    global start_stamp
    global page

    #需要抓取的开始和结束日期
    # start_date = datetime.datetime(2019,5,10,0)
    # end_date = datetime.datetime(2019,5,11,0)
    delta_date = datetime.timedelta(days=1)
    func = lambda x,y:x if y in x else x + [y]

    #每次抓取一天的数据
    start_stamp = start_date
    end_stamp = start_date + delta_date

    global outfile
    global sheet

    # outfile = xlwt.Workbook(encoding = 'utf-8')
    # sheet = outfile.add_sheet(str(key))
    days = 0
    global link_list

    while end_stamp <= end_date:

        page = 1

        #每一天使用一个sheet存储数据
        # sheet = outfile.add_sheet(str(start_stamp.strftime("%Y-%m-%d-%H")))
        # initXLS(key)

        #通过构建URL实现每一天的查询
        url = current_url + '&typeall=1&suball=1&timescope=custom:' + str(start_stamp.strftime("%Y-%m-%d-%H")) + ':' + str(end_stamp.strftime("%Y-%m-%d-%H")) + '&Refer=g'

        # for j in range(3):
        driver.get(url)
    
        handlePage()  #处理当前页面内容

        start_stamp = end_stamp
        end_stamp = end_stamp + delta_date
        days += 1
        # if days % 30 ==0:
        #     print('days:',days)
        #     link_set = reduce(func, [[], ] + link_list)
        #     video_num = len(link_set)
        #     for i in range(video_num):
        #         print('downloading{}{}/{}'.format('.'*75,i, video_num))
        #         video_name = get_video_name(key)
        #         print(video_name)
        #         print(link_set[i])
        #         download_video(link_set[i], video_name)
        #     link_list = []

    # content_set = reduce(func, [[], ] + content_list)
    link_set = reduce(func, [[], ] + link_list)
    # print(content_set)
    # print(link_set)
    # writeInOneSheet(content_set, link_set)
    video_num = len(link_set)
    for i in range(video_num):
        print('downloading{}{}/{}'.format('.'*75,i+1, video_num))
        video_name = get_video_name(key)
        print(video_name)
        print(link_set[i])
        download_video(link_set[i], video_name)

#********************************************************************************
#                  辅助函数，考虑页面加载完成后得到页面所需要的内容
#********************************************************************************   

#页面加载完成后，对页面内容进行处理
def handlePage():
    while True:
        #之前认为可能需要sleep等待页面加载，后来发现程序执行会等待页面加载完毕
        #sleep的原因是对付微博的反爬虫机制，抓取太快可能会判定为机器人，需要输入验证码
        time.sleep(random.randint(1 , 5))
        #先行判定是否有内容
        if checkContent():
            # for i in range(0, 2):
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            #     time.sleep(1)
            print("getContent")
            getContent()
            #先行判定是否有下一页按钮
            # if checkNext():
            if checkNext() and page <= 50:
                #拿到下一页按钮
                next_page_btn = driver.find_element_by_xpath("//a[@class='next']")
                next_page_btn.click()
            else:
                print("no Next")
                break
        else:
            print("no Content")
            break

def get_video_name(key):
    video_folder = './{}'.format(key)
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)
    exists_videos = sorted([int(f.split('.')[0]) for f in os.listdir(video_folder)])
    if len(exists_videos) == 0:
        video_name = os.path.join(video_folder, '0.mp4')
    else:
        num = int(exists_videos[-1])
        video_name = os.path.join(video_folder, '{}.mp4'.format(str(num+1)))
    return video_name

def download_video(url, file_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.3.2.1000 Chrome/30.0.1599.101 Safari/537.36"}
        pre_content_length = 0
        # 循环接收视频数据
        while True:# 若文件已经存在，则断点续传，设置接收来需接收数据的位置    
            if os.path.exists(file_path):
                headers['Range'] = 'bytes=%d-' % os.path.getsize(file_path)
            res = requests.get(url, stream=True, headers=headers)
            content_length = int(res.headers['content-length'])
            # 若当前报文长度小于前次报文长度，或者已接收文件等于当前报文长度，则可以认为视频接收完成
            if content_length < pre_content_length or (os.path.exists(file_path) and os.path.getsize(file_path) >= content_length):
                break
            pre_content_length = content_length
            # 写入收到的视频数据
            with open(file_path, 'ab') as file:
                file.write(res.content)
                file.flush()
                print('receive data，file size : %d   total size:%d' % (os.path.getsize(file_path), content_length))
    except Exception as e:
        dic = {'url':url, 'file_path':file_path}
        print("下载失败:", dic)


#判断页面加载完成后是否有内容
def checkContent():
    #有内容的前提是有“导航条”？错！只有一页内容的也没有导航条
    #但没有内容的前提是有“pl_noresult”
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag

#判断是否有下一页按钮
def checkNext():
    try:
        driver.find_element_by_xpath("//a[@class='next']")
        flag = True
    except:
        flag = False
    return flag

#在添加每一个sheet之后，初始化字段
def initXLS(key):
    # name = ['博主昵称', '博主主页', '微博认证', '微博达人', '微博内容', '发布时间', '微博地址', '微博来源', '转发', '评论', '赞']
    name = ['微博内容', '视频地址']
    
    global row
    global outfile
    global sheet

    row  = 0
    for i in range(len(name)):
        sheet.write(row, i, name[i])
    row = row + 1
    outfile.save("./{}.xls".format(key))

#将dic中的内容写入excel
def writeXLS(dic):
    global row
    global outfile
    global sheet

    for k in dic:
        if len(dic[k]) == 0:
            continue
        for i in range(len(dic[k])):
            sheet.write(row, i, dic[k][i])
        row = row + 1
    outfile.save("./{}.xls".format(key))

def writeInOneSheet(content_set, link_set):
    global row
    global outfile
    global sheet

    row  = 0

    for k in range(len(link_set)):
        try:
            sheet.write(row, 0, content_set[k])
        except:
            pass
        sheet.write(row, 1, link_set[k])
        row = row + 1
    outfile.save("./{}.xls".format(key))

#在页面有内容的前提下，获取内容
def getContent():

    #寻找到每一条微博的class
    nodes = driver.find_elements_by_xpath("//div[@class='card-feed']")

    #在运行过程中微博数==0的情况，可能是微博反爬机制，需要输入验证码
    if len(nodes) == 0:
        # input("请在微博页面输入验证码！")
        # url = driver.current_url
        # driver.get(url)
        # getContent()
        return

    # pdb.set_trace()
    dic = {}

    global page
    print(str(start_stamp.strftime("%Y-%m-%d-%H")))
    print(u'页数:', page)
    page = page + 1
    print(u'微博数量', len(nodes))

    for i in range(len(nodes)):
        dic[i] = []
        forward_flag = False
        # try:
        #     BZNC = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").text
        # except:
        #     BZNC = ''
        # print(u'博主昵称:', BZNC)
        # dic[i].append(BZNC)

        # try:
        #     BZZY = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").get_attribute("href")
        # except:
        #     BZZY = ''
        # print(u'博主主页:', BZZY)
        # dic[i].append(BZZY)

        # try:
        #     WBRZ = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='approve_co']").get_attribute('title')#若没有认证则不存在节点
        # except:
        #     WBRZ = ''
        # print('微博认证:', WBRZ)
        # dic[i].append(WBRZ)

        # try:
        #     WBDR = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='ico_club']").get_attribute('title')#若非达人则不存在节点
        # except:
        #     WBDR = ''
        # print('微博达人:', WBDR)
        # dic[i].append(WBDR)

        # try:
        #     WBNR = nodes[i].find_element_by_xpath(".//div[@node-type='feed_list_forwardContent']").text.replace('\n', ' ')
        #     forward_flag = True
        # except:
        #     WBNR = ''
        # print('微博内容:', WBNR)
        # dic[i].append(WBNR)

        # try:
        #     FBSJ = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']").text
        # except:
        #     FBSJ = ''
        # print(u'发布时间:', FBSJ)
        # dic[i].append(FBSJ)

        # try:
        #     WBDZ = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']").get_attribute("href")
        # except:
        #     WBDZ = ''
        # print('微博地址:', WBDZ)
        # dic[i].append(WBDZ)

        try:
            short_links = nodes[i].find_elements_by_xpath(".//div[@node-type='feed_list_forwardContent']/p/a")
            WBLY = nodes[i].find_element_by_xpath(".//*[@class='wbv-tech']").get_attribute('src')
            forward_flag = True
            # for k in range(len(WBLY)):
            #     if 'huati' not in WBLY:
            #         print('微博内容:', WBNR)
            #         dic[i].append(WBNR)
            #         print('视频地址:', WBLY)
            #         dic[i].append(WBLY)
            #         flag = True
            #         break
        except:
            WBLY = ''


        # try:
        #     ZF_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_forward']//em").text
        #     if ZF_TEXT == '':
        #         ZF = 0
        #     else:
        #         ZF = int(ZF_TEXT)
        # except:
        #     ZF = 0
        # print('转发:', ZF)
        # dic[i].append(str(ZF))

        # try:
        #     PL_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_comment']//em").text#可能没有em元素
        #     if PL_TEXT == '':
        #         PL = 0
        #     else:
        #         PL = int(PL_TEXT)
        # except:
        #     PL = 0
        # print('评论:', PL)
        # dic[i].append(str(PL))

        # try:
        #     ZAN_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_like']//em").text #可为空
        #     if ZAN_TEXT == '':
        #         ZAN = 0
        #     else:
        #         ZAN = int(ZAN_TEXT)
        # except:
        #     ZAN = 0
        # print('赞:', ZAN)
        # dic[i].append(str(ZAN))

        if not forward_flag:
            try:
                # WBNR = nodes[i].find_element_by_xpath(".//p[@node-type='feed_list_content']").text.replace('\n', ' ')
                short_links = nodes[i].find_elements_by_xpath(".//p[@node-type='feed_list_content']/a")
                WBLY = nodes[i].find_element_by_xpath(".//*[@class='wbv-tech']").get_attribute('src')
                # if 'huati' not in WBLY:
                #     print('微博内容:', WBNR)
                #     dic[i].append(WBNR)
                #     print('视频地址:', WBLY)
                #     dic[i].append(WBLY)
                #     flag = True
            except:
                WBLY = ''

        # print('\n')
        # if '此微博已被作者删除' not in WBNR and WBLY != '':
            # for k in range(len(short_links)):
            #     try:
            #         short_link = short_links[k].get_attribute('href')
            #         if 'weibo' not in short_link and short_link not in short_link_list:
            #             # dic[i].append(WBNR)
            #             # dic[i].append(link)
            #             content_list.append(WBNR)
            #             link_list.append(WBLY)
            #             short_link_list.append(short_link)
            #             print('微博内容:', WBNR)
            #             print('视频地址:', link)
            #             break
            #     except:
            #         continue
        if  WBLY != '':
            for k in range(len(short_links)):
                try:
                    short_link = short_links[k].get_attribute('href')
                    if 'weibo' not in short_link and short_link not in short_link_list:
                        short_link_list.append(short_link)
                        # content_list.append(WBNR)
                        link_list.append(WBLY)
                        # print('微博内容:', WBNR)
                        # print('视频地址:', WBLY)
                except:
                    continue

    #写入Excel
    # writeXLS(dic)

#*******************************************************************************
#                                程序入口
#*******************************************************************************
if __name__ == '__main__':

    #定义变量
    username = ''             #输入你的用户名
    password = ''               #输入你的密码

    #操作函数
    LoginWeibo(username, password)       #登陆微博

    #搜索热点微博 爬取评论
    # global content_list
    global link_list
    global short_link_list
    # content_list = []
    link_list = []
    short_link_list = []

    global key
    global page
    global start_date
    global end_date
    global days

    key = '殴打'
    start_date = datetime.datetime(2018,6,1,0)
    end_date = datetime.datetime(2019,1,1,0)

    GetSearchContent(key)
