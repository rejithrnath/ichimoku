# -*- coding: utf-8 -*-
"""
Created on Sat Jul 31 03:28:11 2021

@author: Rejith Reghunathan 
@email: rejithrnath@gmail.com
"""
import pandas as pd
import numpy as np
from pandas_datareader import data, wb
import datetime
import matplotlib.pyplot as plt
import yfinance as yf
import os, pandas
import shutil
import time
import email, smtplib, ssl
import schedule
import temp.config
import requests
from bs4 import BeautifulSoup



if not os.path.exists('results'):
        os.makedirs('results')

if not os.path.exists('datasets'):
        os.makedirs('datasets')
        
if not os.path.exists('DD'):
        os.makedirs('DD')
        
save_path = 'results/'
filename_results = datetime.datetime.now().strftime("%Y%m%d")
completeName = os.path.join(save_path, filename_results+".txt")

delta_time=60

def createdirectory():
    shutil.rmtree('datasets')
    os.makedirs('datasets') 
    
    
def delete_results():
    shutil.rmtree('results')
    shutil.rmtree('DD')
    os.makedirs('results')
    os.makedirs('DD') 
    save_path = 'results/'
    filename_results = datetime.datetime.now().strftime("%Y%m%d")
    completeName = os.path.join(save_path, filename_results+".txt") 
      
    

def yfinancedownload(csv_file_name, interval_time):
       start = datetime.datetime.today() - datetime.timedelta(delta_time)
       end = datetime.datetime.today()
       # end ='2021-7-20'
       with open(csv_file_name) as f:
            lines = f.read().splitlines()
            for symbol in lines:
                try:
                    data=yf.download(symbol,start,end, interval=interval_time, progress = True)
                    data.to_csv("datasets/{}.csv".format(symbol))
                except Exception:
                    pass





def ichimoku():

     gain_day = " "
     dataframes = {}
     # start = datetime.datetime.today() - datetime.timedelta(delta_time)
     # # end = datetime.datetime.today()
     # end ='2021-04-16'
     for filename in os.listdir('datasets'):
            symbol = filename.split(".")[0]
            
            d = pandas.read_csv('datasets/{}'.format(filename))
            if d.empty: 
                continue           
            
            
            # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
            nine_period_high = d['High'].rolling(window= 9).max()
            nine_period_low = d['Low'].rolling(window= 9).min()
            d['tenkan_sen'] = (nine_period_high + nine_period_low) /2
            
            # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
            period26_high = d['High'].rolling(window=26).max()
            period26_low = d['Low'].rolling(window=26).min()
            d['kijun_sen'] = (period26_high + period26_low) / 2
            
            # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
            d['senkou_span_a'] = ((d['tenkan_sen'] + d['kijun_sen']) / 2).shift(26)
            
            # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
            period52_high = d['High'].rolling(window=52).max()
            period52_low = d['Low'].rolling(window=52).min()
            d['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(52)
            
            # The most current closing price plotted 26 time periods behind (optional)
            d['chikou_span'] = d['Close'].shift(-26)
            
            # d.dropna(inplace=True)
            d['above_cloud'] = 0
            d['above_cloud'] = np.where((d['Low'] > d['senkou_span_a'])  & (d['Low'] > d['senkou_span_b'] ), 1, d['above_cloud'])
            d['above_cloud'] = np.where((d['High'] < d['senkou_span_a']) & (d['High'] < d['senkou_span_b']), -1, d['above_cloud'])
            d['A_above_B'] = np.where((d['senkou_span_a'] > d['senkou_span_b']), 1, -1)
            d['tenkan_kiju_cross'] = np.NaN
            d['tenkan_kiju_cross'] = np.where((d['tenkan_sen'].shift(1) <= d['kijun_sen'].shift(1)) & (d['tenkan_sen'] > d['kijun_sen']), 1, d['tenkan_kiju_cross'])
            d['tenkan_kiju_cross'] = np.where((d['tenkan_sen'].shift(1) >= d['kijun_sen'].shift(1)) & (d['tenkan_sen'] < d['kijun_sen']), -1, d['tenkan_kiju_cross'])
            d['price_tenkan_cross'] = np.NaN
            d['price_tenkan_cross'] = np.where((d['Open'].shift(1) <= d['tenkan_sen'].shift(1)) & (d['Open'] > d['tenkan_sen']), 1, d['price_tenkan_cross'])
            d['price_tenkan_cross'] = np.where((d['Open'].shift(1) >= d['tenkan_sen'].shift(1)) & (d['Open'] < d['tenkan_sen']), -1, d['price_tenkan_cross'])
            d['buy'] = np.NaN
            d['buy'] = np.where((d['above_cloud'].shift(1) == 1) & (d['A_above_B'].shift(1) == 1) & ((d['tenkan_kiju_cross'].shift(1) == 1) | (d['price_tenkan_cross'].shift(1) == 1)), 1, d['buy'])
            d['buy'] = np.where(d['tenkan_kiju_cross'].shift(1) == -1, 0, d['buy'])
            d['buy'].ffill(inplace=True)
            
            d['Long_Position'] = d['buy'].diff()
            d['Long_Buy'] = d['Long_Position'].apply(lambda x: 'Buy' if x == 1 else 'Sell')
            
            
            
            d['sell'] = np.NaN
            d['sell'] = np.where((d['above_cloud'].shift(1) == -1) & (d['A_above_B'].shift(1) == -1) & ((d['tenkan_kiju_cross'].shift(1) == -1) | (d['price_tenkan_cross'].shift(1) == -1)), -1, d['sell'])
            d['sell'] = np.where(d['tenkan_kiju_cross'].shift(1) == 1, 0, d['sell'])
            d['sell'].ffill(inplace=True)
            
            d['Short_Position'] = d['sell'].diff()
            d['Short_Buy'] = d['Short_Position'].apply(lambda x: 'Sell' if x == 1 else 'Buy')
            
            # print (d)
            d.to_csv("DD/DD_{}.csv".format(symbol))
             #Webscrapping
            try:
                temp_dir = {}
                url = 'https://finance.yahoo.com/quote/'+symbol+'/financials?p='+symbol
                headers={'User-Agent': "Mozilla/5.0"}
                page = requests.get(url, headers=headers)
                page_content = page.content
                soup = BeautifulSoup(page_content,'html.parser')
                tabl = soup.find_all("div", {"class" : "D(ib) Va(m) Maw(65%) Ov(h)"})
                for t in tabl:
                    rows = t.find_all("span", {"data-reactid" : "32"})
                    for row in rows:
                        temp_dir[row.get_text(separator=' ').split(" ")[1]]=row.get_text(separator=' ').split(" ")[1]
                
              
                gain_day =list(temp_dir.keys())[0]
                
                
            except Exception:
                    pass
 
           
           
            
            f = open(completeName, "a")
            if d.iloc[-1]['Long_Position'] == 1 or d.iloc[-1]['Long_Position'] == -1 :
                print("{0} is Detected in ICHIMOKU  Long Position. Close = {1:.2f}, Result = {2}, Volume = {3:.2f},  Daily Gain ={4}\n".format(symbol,d.iloc[-1]['Close'],d.iloc[-1]['Long_Buy'],d.iloc[-1]['Volume'], gain_day ), file=f)
                print("{0} is Detected in ICHIMOKU  Long Position. Close = {1:.2f}, Result = {2}, Volume = {3:.2f},  Daily Gain ={4}\n".format(symbol,d.iloc[-1]['Close'],d.iloc[-1]['Long_Buy'],d.iloc[-1]['Volume'], gain_day ))
                
            if d.iloc[-1]['Short_Position'] == 1 or d.iloc[-1]['Short_Position'] == -1 :
                    print("{0} is Detected in ICHIMOKU  Short Position. Close = {1:.2f}, Result = {2}, Volume = {3:.2f},  Daily Gain ={4}\n".format(symbol,d.iloc[-1]['Close'],d.iloc[-1]['Short_Buy'],d.iloc[-1]['Volume'], gain_day ), file=f)
                    print("{0} is Detected in ICHIMOKU  Short Position. Close = {1:.2f}, Result = {2}, Volume = {3:.2f},  Daily Gain ={4}\n".format(symbol,d.iloc[-1]['Close'],d.iloc[-1]['Short_Buy'],d.iloc[-1]['Volume'], gain_day ))
        
                    
            f.close()
                            
def email_export():
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    subject = "Ichimoku Kinko Hyo OSL Results "+ str(datetime.datetime.now())
    body = "Email with attachment "
    
    sender_email = temp.config.sender_email
    receiver_email = temp.config.receiver_email
    password = temp.config.password

        
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = sender_email
    message["Subject"] = subject
    message["Bcc"] = ", ".join(receiver_email)  # Recommended for mass emails
    
    # Add body to email
    message.attach(MIMEText(body, "plain"))
    
    
    # Open PDF file in binary mode
    with open(completeName, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)
    
    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {completeName}",
    )
    
    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()
    
    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
        print("Emailed!")
        delete_results()
            

def download_and_email():
    
    createdirectory()
    f = open(completeName, "a")
    print ("Start ICHIMOKU TRADING STRATEGY -> %s \n" % time.ctime(), file=f) 
    print ("*******************************************************************" , file=f)
    f.close()
    yfinancedownload('input.csv','1h')
    ichimoku()
    f = open(completeName, "a")
    print ("*******************************************************************" , file=f)
    f.close()
    email_export()    
    
def main():
    
    print("RUNNING ICHIMOKU TRADING STRATEGY !!")
    download_and_email()
    trading_time = ["09","10","11","12","13","14","15","16","17"]
    for x in trading_time:
        schedule.every().monday.at(str(x)+":16").do(download_and_email)
        schedule.every().tuesday.at(str(x)+":16").do(download_and_email)
        schedule.every().wednesday.at(str(x)+":16").do(download_and_email)
        schedule.every().thursday.at(str(x)+":16").do(download_and_email)
        schedule.every().friday.at(str(x)+":16").do(download_and_email)
 
    while True:
        schedule.run_pending()
        time.sleep(1)    
    
if __name__ == "__main__":
    main()