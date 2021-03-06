from datetime import datetime
from urllib.parse import quote
import requests
import traceback
from bs4 import BeautifulSoup
import pymysql
from sys import argv  # 命令行参数argv[1] 开始 len（argv） 个数
import time
import os


conn = None
city_dict = {"成都": "090200", "重庆": "060000", "武汉": "180200", "北京": "010000", "上海": "020000", "广州": "030200",
             "深圳": "040000", "杭州": "080200"}
keys = ["php", "java", "python", "c++", "c#", "c语言", ".net"]
year = str(datetime.now())[0:5]
today = str(datetime.now())[5:10]
db_path = os.path.dirname(__file__)

if len(argv) == 3:
    city_code = argv[1]

    keys = argv[2].split(",")


def job_get_contents(page, city_code, keyword):
    keyword = quote(keyword)
    url = "http://search.51job.com/list/" + city_code + ",000000,0000,00,9,99," + keyword + ",2," + str(

        page) + ".html?lang=c&stype=1&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&lonlat=0%2C0&radius=-1&ord_field=0&confirmdate=9&fromType=&dibiaoid=0&address=&line=&specialarea=00&from=&welfare="

    r = requests.get(url, headers={

        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'})

    r.encoding = 'gbk'

    return r.text


def store_data(*data):
    global conn
    if not conn:
        conn = pymysql.connect('localhost', 'root', '123456', 'python', charset='UTF8')
    cur = conn.cursor()
    try:
        cur.execute(
            "insert into job_info (city,keyword,job_title,job_url,company_title,company_url,area,salary,date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            data)
        conn.commit()
    except:
        traceback.print_exc()
        print(data[2], data[4], "储存失败")
        conn.rollback()
    finally:
        cur.close()


for city in city_dict.keys():
    city_code = city_dict[city]
    for keyword in keys:

        page = 1

        end_flag = 0

        while page > 0:

            print("采集%s-%s第%d页" % (city, keyword, page))

            for x in range(1, 5):

                try:

                    res = job_get_contents(page, city_code, keyword)

                    break  # 成功就不循环了，失败后循环5次

                except:

                    print("第%d次打开网址失败" % x)

                    time.sleep(3)

            try:
                obj = BeautifulSoup(res, 'lxml')
                data_list = obj.find(id="resultList").findAll(class_="el")
                data_list.pop(0)  # 剔除第一个title
            except:
                print("采集这一页时失败，采集下一页")
                page = page + 1
                continue

            for info in data_list:

                # job

                job = info.find(class_="t1").a

                job_title = job.get_text().strip()

                job_url = job.attrs['href']

                # company
                company = info.find(class_="t2").a
                company_title = company.get_text().strip()
                company_url = company.attrs['href']
                # area
                area = info.find(class_="t3").get_text().strip()
                # salary
                salary = info.find(class_="t4").get_text().strip()
                # date
                date = info.find(class_="t5").get_text().strip()
                if date != today:
                    # 有些前几天发的广告会在第一条所以要处理下
                    end_flag = 1
                else:
                    end_flag = 0
                    try:
                        store_data(city, keyword, job_title, job_url, company_title, company_url, area, salary,
                                   year + date)
                        # print(keyword, job_title, job_url, company_title, company_url, area, salary, date)
                    except:
                        pass

            if end_flag == 0:

                page += 1  # 下一页

            elif end_flag == 1:

                page = -100

##分割线

if "__main__" == __name__:
    print("采集完毕")

# CREATE TABLE `job_info` (
#   `city` varchar(15) NOT NULL,
#   `keyword` varchar(15) NOT NULL,
#   `job_title` varchar(255) DEFAULT NULL,
#   `job_url` varchar(255) NOT NULL,
#   `company_title` varchar(255) DEFAULT NULL,
#   `company_url` varchar(255) NOT NULL,
#   `area` varchar(255) DEFAULT NULL,
#   `salary` varchar(255) DEFAULT NULL,
#   `date` date NOT NULL,
#   PRIMARY KEY (`city`,`keyword`,`date`,`job_url`,`company_url`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
