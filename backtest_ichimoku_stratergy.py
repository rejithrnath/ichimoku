# -*- coding: utf-8 -*-
"""
Created on Sat Jul 31 13:48:10 2021

@author: Rejith Reghunathan 
@email: rejithrnath@gmail.com
"""

import os, pandas
import numpy as np

if not os.path.exists('back_test_results'):
        os.makedirs('back_test_results')


Full_total =0
count_positive=0
count_negative=0
for filename in os.listdir('DD'):
            symbol = (filename.split( "_")[1]).split(".")[0]
            d = pandas.read_csv('DD/{}'.format(filename))
            if d.empty: 
                continue
                        
            d.drop(d[d['Long_Position'] == 0].index, inplace = True)
            d.dropna(subset=['Long_Position'], inplace = True)
            
            try:
                if d.iloc[-1]['Long_Buy'] == 'Buy':
                    d.drop(d.tail(1).index,inplace=True) # drop last n rows
                if d.iloc[0]['Long_Buy'] == 'Sell':
                    d.drop(d.head(1).index,inplace=True) # drop last n rows
            except Exception:
                    pass
            d['Close_Buy'] = np.where((d['Long_Buy'] == 'Buy') , -1*d['Close'], 0)
            d['Close_Sell'] = np.where((d['Long_Buy'] == 'Sell') , d['Close'], 0)
            d.to_csv("back_test_results/Buy_Sell_{}.csv".format(symbol))    
            Total = d['Close_Buy'].sum() + d['Close_Sell'].sum()
            if Total >= 0 :
                count_positive += 1
            else:
                count_negative+=1
            Full_total=Total+Full_total
            
            f = open('backtestresult.txt', "a")
            print (str(symbol) + " ->" + str(Total), file=f)
            print (str(symbol) + " ->" + str(Total))
            f.close()
f = open('backtestresult.txt', "a")
print ("Count Positive or Zero" + " ->" + str(count_positive) + " Count Negative " + " ->" + str(count_negative) +" Total" + " ->" + str(Full_total), file=f)
print ("Count Positive or Zero" + " ->" + str(count_positive) + " Count Negative" + " ->" + str(count_negative) +" Total" + " ->" + str(Full_total))
f.close()