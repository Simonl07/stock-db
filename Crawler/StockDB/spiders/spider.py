# -*- coding:UTF-8 -*-
import scrapy
import hashlib
import re
import csv
from StockDB import *
import StatsUtils
from StatsUtils import *
from StockDB.items import Stock


class Spider(scrapy.Spider):
    handle_httpstatus_list = [200, 404, ]

    name = 'spider'
    allowed_domains = ['https://finance.yahoo.com']
    stockList = []
    start_urls = url_generator(stockList)

    #start_urls = ['https://finance.yahoo.com/quote/?p=AAPL']
    def parse(self, response):

        stockName = re.search('(?<=\=).+?$', response.url).group()
        recordStatus(stockName, response.status)

        item = Stock()

        name_full = response.xpath('//*[@id="quote-header-info"]/div[2]/div[1]/div[1]/h1/text()').extract_first()

        if '-' in name_full:
            item['name_full'] = re.search('(?<=- ).+?$', name_full).group()
            item['name_short'] = re.search('.+?(?= \-)', name_full).group()
        else:
            item['name_full'] = re.search('.+?(?=\()', name_full).group()
            item['name_short'] = re.search('(?<=\().+?(?=\))', name_full).group()



        item['price_close'] = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[1]/td[2]/span/text()').extract_first()
        item['price_open'] = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[2]/td[2]/span/text()').extract_first()
        item['range_day'] = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[5]/td[2]/text()').extract_first()
        item['range_day_low'] = re.search('[\d.]+?(?=\s)', item['range_day']).group()
        item['range_day_high'] = re.search('(?<=\s)[\d.]+', item['range_day']).group()
        item['range_52w'] = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[6]/td[2]/text()').extract_first()
        item['range_52w_low'] = re.search('[\d.]+?(?=\s)', item['range_52w']).group()
        item['range_52w_high'] = re.search('(?<=\s)[\d.]+', item['range_52w']).group()
        volumn = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[7]/td[2]/span/text()').extract_first().replace(",", "")
        if volumn == "N/A":
            item["volumn"] = "-1"
        item["volume"] = volumn

        item['volume_avg'] = response.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[8]/td[2]/span/text()').extract_first().replace(",", "")
        market_cap = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[1]/td[2]/span/text()').extract_first()
        item['market_cap'] = str(convertValue(market_cap))
        beta = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[2]/td[2]/span/text()').extract_first()
        if beta == "N/A":
            beta = -1
        item['beta'] = str(beta)
        item['pe_ratio'] = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[3]/td[2]/span/text()').extract_first().replace(",", "")
        eps = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[4]/td[2]/span/text()').extract_first()
        if eps == "N/A":
            eps = "-1"
        item['eps'] = eps
        first = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[5]/td[2]/span/text()').extract_first()
        second = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[5]/td[2]/span[2]/text()').extract_first()

        final = ""
        if first is None and second is None:
            final = "N/A"
        elif first is None:
            final = second
        elif second is None:
            final = first
        else:
            final = first + " - " + second

        item['earnings_date'] = final
        print('finallll: ' , final, item['name_short'])
        item['earnings_date_begin'], item['earnings_date_end'] = formatDate(item['earnings_date'])
        dividend_String = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[6]/td[2]/text()').extract_first()
        if 'N/A' in dividend_String:
            item['dividend'] = '-1'
            item['dividend_yield'] = '-1'
        else:
            item['dividend'] = re.search('.*(?=\s)', dividend_String).group()
            item['dividend_yield'] = str(round(float(str(re.search('(?<=\().*(?=\%)', dividend_String).group())) / 100, 4))
        ex_div_date = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[7]/td[2]/span/text()').extract_first()
        if ex_div_date == "N/A":
            ex_div_date = "1900-01-01"
        item['ex_dividend_date'] = ex_div_date
        target_est_1Y = response.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[8]/td[2]/span/text()').extract_first().replace(",", "")
        if target_est_1Y == "N/A":
            target_est_1Y = "-1"
        item['target_est_1Y'] = target_est_1Y
        #test
        print(item)
        yield item


def formatDate(date):
    print('date!!!!!!!: ', date)
    if date == "N/A":
        return "1900-01-01", "1900-01-01"
    if '-' in date:
        first = re.search('.*(?= -) ', date).group().strip()
        second = re.search('(?<=- ).*', date).group().strip()
        return formatHelper1(first), formatHelper1(second)


    return formatHelper1(date), formatHelper1(date)


def formatHelper1(date):
    print("DATE: ", date)
    year = re.search('\d{4}', date).group()
    day = re.search('\d+(?=,)', date).group()
    month = re.search('[a-zA-Z]+', date).group()
    return formatHelper2(year, month, day)

def formatHelper2(year, month, day):
    months = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
    }

    return year + "-" + months[month] + "-" + day



def convertValue(capital):
    value = 0
    if (capital.endswith("B")):
        value = int(float(capital[:-1])*1000000000)
    else:
        value = int(float(capital[:-1])*100000)
    return value
