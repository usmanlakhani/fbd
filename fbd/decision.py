import json
import pandas as pd
import os
from ticker import Ticker, Buy, Sell
from datetime import datetime, timedelta

finalDataFrame = None

def initiate(fileName):

    #region variables
    row_Ticker = None
    columns = ['Alert','Row Index','Timestamp','High Price','Low Price','Lowest Price','Significant Low Price','Units Bought','Entry Point','Stop Loss','Units Sold','Units Left']
    global finalDataFrame
    finalDataFrame = pd.DataFrame(columns=columns)
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
    
    # Loop through RAW data frame, split it in such a way that each sub-data frame has a 2 hour span
    subDataFrames = createSubDataFrames(dataFrame,120)
    
    i = 0
    while i < len(subDataFrames):
        
        if i == 0: 
            i = i + 1
            continue
        
        tmpLowestPrice = findLowestPriceInPast(subDataFrames[i-1],None)
        row_Ticker.lowestPrice = tmpLowestPrice
        row_Ticker.comments = '[ALERT] 2-Hr Window Expired. Reset Low/Sig Low Prices'
        row_Ticker.currentHighPrice = None
        row_Ticker.currentLowPrice = None
        row_Ticker.timeStamp = None
        # use lowest price found and use it with the data frame at index i
        finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
        row_Ticker = process(subDataFrames[i], row_Ticker) 
        i = i + 1
        
    saveFinalDataFrame(finalDataFrame)

def createSubDataFrames(raw, periodToSplitOverInMinutes):
    
    _row = 0
    column = 0
    listDataFrames = []
    print(raw.index.max())
    
    # Convert the column to datetime if it isn't already
    if not pd.api.types.is_datetime64_any_dtype(raw.iloc[:, 0]):
        raw.iloc[:, 0] = pd.to_datetime(raw.iloc[:, 0])
    
    for idx, row in raw.iterrows():
        
        if (_row < raw.index.max()):
        
            dtStartingTimeStamp = raw.iloc[_row,column]
        
            dtEndingTimeStamp = dtStartingTimeStamp + timedelta(minutes=periodToSplitOverInMinutes)
        
            # Filter the DataFrame
            dfReturn = raw[(raw.iloc[:, 0] >= dtStartingTimeStamp) & (raw.iloc[:, 0] < dtEndingTimeStamp)]
        
            listDataFrames.append(dfReturn)
        
            _row = _row + len(dfReturn)
    
    return listDataFrames

 
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
        
        if row_Ticker.hasBought == True and tmpCurrentHighPrice - row_Ticker.Buy.entryPoint >= row_Ticker.Sell.profitPerUnit:
            row_Ticker.comments = '[ALERT] Sell'
            row_Ticker.hasBought = False
            row_Ticker.Buy.entryPoint = None
            finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
            continue
        
        if row_Ticker.SignificantLow.Known == False or row_Ticker.SignificantLow.Known is None:
            
            if tmpCurrentLowPrice < row_Ticker.lowestPrice:
                
                row_Ticker.lowestPrice = tmpCurrentLowPrice
                row_Ticker.comments = '[ALERT] Low Price Found'
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord() 
                continue
            
            if tmpCurrentLowPrice == row_Ticker.lowestPrice:
                
                row_Ticker.lowestPrice = tmpCurrentLowPrice
                row_Ticker.comments = '[SOFT ALERT] Existing Low Price Verified'
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord() 
                continue
            
            if tmpCurrentLowPrice > row_Ticker.lowestPrice and tmpCurrentLowPrice-row_Ticker.lowestPrice >= row_Ticker.SignificantLow.Marker:
                
                row_Ticker.comments = '[ALERT] Significant Low Found'  
                row_Ticker.SignificantLow.Known = True
                row_Ticker.SignificantLow.Price = row_Ticker.lowestPrice
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
                continue 
            
            else:
                row_Ticker.comments = 'Looking for Sig Low'
                finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
                continue

        if row_Ticker.SignificantLow.Known == True:
            
            # downward breach
            if tmpCurrentLowPrice < row_Ticker.SignificantLow.Price and \
                row_Ticker.SignificantLow.lowPoint <=  row_Ticker.SignificantLow.Price - tmpCurrentLowPrice < row_Ticker.SignificantLow.highPoint:
                    
                    row_Ticker.comments = '[ALERT] Significant Low has been Downwards Breached' 
                    row_Ticker.SignificantLow.downwardsBreach = True
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
            
            # flush
            if tmpCurrentLowPrice < row_Ticker.SignificantLow.Price and \
                row_Ticker.SignificantLow.Price - tmpCurrentLowPrice >= row_Ticker.SignificantLow.highPoint:
                    
                    row_Ticker.comments = '[ALERT] Significant Low has been flushed'   
                    row_Ticker.SignificantLow.Known = False 
                    row_Ticker.lowestPrice = tmpCurrentLowPrice
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
            
            # buy
            if tmpCurrentLowPrice > row_Ticker.SignificantLow.Price and \
                row_Ticker.SignificantLow.downwardsBreach and \
                tmpCurrentLowPrice - row_Ticker.SignificantLow.Price >= row_Ticker.SignificantLow.lowPoint:
                    
                    if row_Ticker.hasBought == False or row_Ticker.hasBought is None:
                        row_Ticker.comments = '[ALERT] Buy'
                        row_Ticker.SignificantLow.Known = False
                        row_Ticker.SignificantLow.Price = None
                        #row_Ticker.lowestPrice = None
                        row_Ticker.hasBought = True
                        row_Ticker.Buy.entryPoint = tmpCurrentLowPrice
                        finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                        continue

    return row_Ticker
                      
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
    
    #fileName='2024-01.csv'
    #fileName = 'Jan1-Jan2-Jan3-Jan4.csv'
    fileName= 'Jan1-10.csv'
    #fileName = 'dummydata.csv'
    initiate(fileName)