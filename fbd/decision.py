import json
import pandas as pd
import os
from ticker import Ticker, Buy, Sell
from datetime import datetime, timedelta

global finalDataFrame

def initiate(fileName):

    #region variables
    row_Ticker = None
    columns = ['Alert','Row Index','Timestamp','High Price','Low Price','Lowest Price','Significant Low Price','Units Bought','Entry Point','Stop Loss','Units Sold','Units Left']
    finalDataFrame = pd.DataFrame(columns=columns)
    intYear = 2024
    intMonth = 1
    intDay = 1
    intHour=20
    intMin=0
    #endregion
    

    try:
        row_Ticker = Ticker('parameters-1min.json')
    except Exception as e:
        printError()
        return

   
    
    dataFrame = loadFile(fileName)
    
    if dataFrame is None:
        printError()
        return

    
    #datetime(2024, 1, 1, 20, 0) # year, month, day, hour, minute, second
    # 1. Passing date dimensions along with raw data frame --> Get a data frame that has only 2 hours in the past rows
    trimmedDataFrame = trimDataFrame(dataFrame, intYear,intMonth,intDay,intHour,intMin)
    
    if trimmedDataFrame is None:
        printError()
        return

    # 2. Using the trimmed data frame that has only last 2 hours records, find the lowest price
    row_Ticker.lowestPrice = findLowestPriceInPast(trimmedDataFrame, None)
    
    if row_Ticker.lowestPrice is None:
        printError()
        return    

    # 3. Remove the records that were extracted ONLY for finding lowest price
    filtered_indices = trimmedDataFrame.index
    
    # 4. Pass the [raw - 2 hours] data frame to extract method --> 2 is being sent to keep data records within 2 hours only
    toProcessDataFrame = extractToProcessDataFrame(dataFrame.drop(filtered_indices),2)
    process(toProcessDataFrame,row_Ticker)

    

def extractToProcessDataFrame(raw,lookForwardPeriod):
    
    dfReturn = None
    
    try:
        dt = raw.iloc[0,0]
        
        dt_plus_lookForwardPeriod = dt + timedelta(hours=2)  # Adds 5 hours
        
        dfReturn = raw[(raw.iloc[:,0] >= dt) & (raw.iloc[:,0] < dt_plus_lookForwardPeriod)]
    
    except Exception as e:
        print('Error finding lowest price. Reason : ',e)    
    
    return dfReturn
    

def process(dataFrame,row_Ticker):
    
    for idx, row in dataFrame.iterrows():
        
        tmpTimeStamp = row.iloc[0]  # The current timestamp      
        tmpCurrentHighPrice = float(row.iloc[1]) # The High Price
        tmpCurrentLowPrice = float(row.iloc[2]) # The Low Price
        idxExcel = idx + 1
        
        row_Ticker.currentHighPrice = tmpCurrentHighPrice
        row_Ticker.currentLowPrice = tmpCurrentLowPrice
        row_Ticker.idExcel = idxExcel
        row_Ticker.timeStamp = tmpTimeStamp
        
        if row_Ticker.SignificantLow.Known == False or row_Ticker.SignificantLow.Known is None:
            
            if tmpCurrentLowPrice <= row_Ticker.lowestPrice:
                
                row_Ticker.lowestPrice = tmpCurrentLowPrice
                row_Ticker.comments = '[ALERT] Low Price Found/Confirmed'
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord() 
                continue
            
            if tmpCurrentLowPrice > row_Ticker.lowestPrice and tmpCurrentLowPrice-row_Ticker.lowestPrice >= row_Ticker.SignificantLow.Marker:
                
                row_Ticker.comments = '[ALERT] Significant Low Found'  
                row_Ticker.SignificantLow.Known = True
                row_Ticker.SignificantLow.Price = row_Ticker.lowestPrice
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
                continue  

        if row_Ticker.SignificantLow.Known == True:
            
            if tmpCurrentLowPrice < row_Ticker.SignificantLow.Price and tmpCurrentLowPrice - row_Ticker.SignificantLow.Price 
                        




def findLowestPriceInPast(before_time, prevLowestPrice):

    price = None
    tmpPrevLowestPrice = prevLowestPrice
    
    try:
        for idx,row in before_time.iterrows():
            
            tmpLowPrice = float(row.iloc[2])
            
            if tmpPrevLowestPrice is None:
                price = tmpLowPrice
                tmpPrevLowestPrice = price
            else:
                if tmpLowPrice < price:
                    price = tmpLowPrice
                    
    except Exception as e:
        print('Error finding lowest price. Reason : ',e)
    
    return price

def trimDataFrame(raw, intYear,intMonth,intDay,intHour,intMin):

    trimmedDataFrame = None
    
    try:
        comparison_date = datetime(intYear,intMonth,intDay,intHour,intMin)
        raw.iloc[:, 0] = pd.to_datetime(raw.iloc[:, 0])
        trimmedDataFrame = raw[raw.iloc[:, 0] < comparison_date]
    
    except Exception as e:
        print ('Error trimming data set. Reason: ', e)
    #print(trimmedDataFrame)
    return trimmedDataFrame      

def saveFinalDataFrame(finalDataFrame):
    try:
    # Try to remove the file if it exists
        os.remove('test.csv')
        print('test.csv was deleted')
    except FileNotFoundError:
        # File doesn't exist, which is fine
        print('test.csv did not exist')

    # Create new file
    with open('test.csv', 'w') as f:
        finalDataFrame.to_csv('test.csv')
    print('Created test.csv') 
  
def findLowestPriceInPast(before_time, prevLowestPrice):

    price = None
    tmpPrevLowestPrice = prevLowestPrice
    
    try:
        for idx,row in before_time.iterrows():
            
            tmpLowPrice = float(row.iloc[2])
            
            if tmpPrevLowestPrice is None:
                price = tmpLowPrice
                tmpPrevLowestPrice = price
            else:
                if tmpLowPrice < price:
                    price = tmpLowPrice
                    
    except Exception as e:
        print('Error finding lowest price. Reason : ',e)
    
    return price

def printError():
    print('Terminating due to error mentioned above') 

def loadFile(fileName):
    
    dataFrame = None
    
    try:
        dataFrame = pd.read_csv(fileName,usecols=[0,2,3], header=None) # 0 = timestamp, 2 = High Price, 3 = Low Price
    
    except Exception as e:
        print('Error trying to load file. Reason: ', e) 
    
    return dataFrame

if __name__ == "__main__":
    
    fileName='2024-01.csv'
    #fileName = 'dummydata.csv'
    initiate(fileName)