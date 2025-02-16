import json
import pandas as pd
import os
from ticker import Ticker, Buy, Sell

def initiate(fileName):
    
    
    #variables
    row_Ticker = None
    columns = ['Alert','Row Index','Timestamp','High Price','Low Price','Lowest Price','Significant Low Price','Units Bought','Entry Point','Stop Loss','Units Sold','Units Left']
    finalDataFrame = pd.DataFrame(columns=columns)

    
    #region Create the Ticker object
    try:
        row_Ticker = Ticker('parameters-wip.json')
    except Exception as e:
        print('Error occured creating row_Ticker driver object.')
        return
    #endregion
   
    #region Load data into Dataframe
    try:        
        dataFrame = pd.read_csv(fileName, usecols=[0,2,3], header=None)  # 0 = timestamp, 2 = High Price, 3 = Low Price  
    except Exception as e:        
        print('Data file cannot be found. Aborting')        
        return
    #endregion
    
    #region Loop through data frame
    for idx,row in dataFrame.iterrows():
         
        tmpTimeStamp = row.iloc[0]        
        tmpCurrentHighPrice = float(row.iloc[1])
        tmpCurrentLowPrice = float(row.iloc[2])
        idxExcel = idx + 1
        
        row_Ticker.currentLowPrice = tmpCurrentLowPrice
        row_Ticker.currentHighPrice = tmpCurrentHighPrice            
        row_Ticker.timeStamp = tmpTimeStamp   

        if row_Ticker.lowestPrice is None:
            row_Ticker.lowestPrice = tmpCurrentLowPrice
            row_Ticker.idExcel = idxExcel
            #row_Ticker.printTicker()
            finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
            #print (finalDataFrame)
            #finalDataFrame.to_csv('test.csv')
            continue
        
        #region If we own anything, we have to always keep an eye out for when low price is at least 10 dollars higher
        if (row_Ticker.hasBought):
            
            if (row_Ticker.Sell.sellSequence is None):
                
                profitMargin = tmpCurrentHighPrice - float(row_Ticker.Buy.entryPoint)
            
                if profitMargin >= row_Ticker.Sell.profitPerUnit:
                
                    tmpComment = '[ALERT:SELL]' 
                    row_Ticker.comments = tmpComment                  
                    row_Ticker.Sell.sellSequence = 1
                    tmpPercentageToSell = row_Ticker.Sell.percentageToSell/100
                    tmpUnitsSold = row_Ticker.Buy.units * tmpPercentageToSell
                    row_Ticker.Sell.unitsSold = tmpUnitsSold
                    tmpUnitsLeft = row_Ticker.Buy.units - tmpUnitsSold
                    
                    # have to set stop loss to a entry price now
                    if tmpUnitsLeft > 0:
                        row_Ticker.Buy.stopLossPrice = row_Ticker.setStopLoss('secondary')
                        row_Ticker.Buy.units = tmpUnitsLeft
                    else:
                        row_Ticker.Buy.units = 0
                        row_Ticker.hasBought = False
                        row_Ticker.SignificantLow.Price = None
                        row_Ticker.SignificantLow.Known = None
                        row_Ticker.SignificantLow.downwardsBreach = None
                        row_Ticker.SignificantLow.upwardsBreach = None

                    finalDataFrame.loc[len(finalDataFrame)]= row_Ticker.addRecord()
                        
                    
        
        #endregion
        
        #region When Significant Low is None or False
        if row_Ticker.SignificantLow.Known is None or row_Ticker.SignificantLow.Known == False:
            
            #region If latest value of low price is less than the lowestPrice, we will set the lowestPrice to the low price
            if tmpCurrentLowPrice < row_Ticker.lowestPrice:
                tmpPreviousLowPrice = row_Ticker.lowestPrice
                row_Ticker.lowestPrice = tmpCurrentLowPrice
                row_Ticker.idExcel = idxExcel
                tmpComment = '[ALERT] NEW LOWEST PRICE'
                row_Ticker.comments = tmpComment
                #row_Ticker.printTicker()
                finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                continue
            #endregion
            
            #region If latest value of low price = lowestPrice, we will set the lowestPrice to the low price
            if tmpCurrentLowPrice == row_Ticker.lowestPrice:
                tmpPreviousLowPrice = row_Ticker.lowestPrice
                row_Ticker.idExcel = idxExcel
                #tmpComment = 'No impact on LOWEST KNOWN PRICE'
                row_Ticker.comments = None
                #row_Ticker.printTicker()
                finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                continue
            #endregion
            
            #region If latest value of low price is higher than the lowestPrice, we check if High-Lowest = Sig Low Marker
            if tmpCurrentLowPrice > row_Ticker.lowestPrice:
                
                tmpPreviousLowPrice = row_Ticker.lowestPrice
                
                # Used Low Price since we are looking for Sig Low
                # Low should always be measured against low
                difference = row_Ticker.currentLowPrice - row_Ticker.lowestPrice
                
                if difference < row_Ticker.SignificantLow.Marker:

                    #tmpComment = 'Searching for SIGNIFICANT LOW'
                    row_Ticker.comments = None              
                    row_Ticker.idExcel = idxExcel 
                    #row_Ticker.printTicker()
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
                
                if difference >= row_Ticker.SignificantLow.Marker:
                    
                    row_Ticker.SignificantLow.Price = row_Ticker.lowestPrice
                    row_Ticker.SignificantLow.Known = True
                    tmpComment = '[ALERT] SIGNIFICANT LOW FOUND'
                    row_Ticker.comments = tmpComment              
                    row_Ticker.idExcel = idxExcel
                    #row_Ticker.printTicker() 
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue            
            #endregion           

            
        #endregion
    
        #region When Significant Low is KNOWN
        if row_Ticker.SignificantLow.Known == True:
            
            #region When price action is downwards biased
            if tmpCurrentLowPrice < row_Ticker.SignificantLow.Price:
                
                difference = row_Ticker.SignificantLow.Price - tmpCurrentLowPrice
                
                if difference < row_Ticker.SignificantLow.lowPoint:
                    tmpComment = '[ALERT: SOFT DOWNWARDS BREACH]'
                    row_Ticker.idExcel = idxExcel
                    row_Ticker.comments = tmpComment
                    #row_Ticker.printTicker()
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
            
                if difference >= row_Ticker.SignificantLow.lowPoint and difference <= row_Ticker.SignificantLow.highPoint:
                    tmpComment = '[ALERT: HARD DOWNWARDS BREACH]'
                    row_Ticker.SignificantLow.downwardsBreach = True
                    row_Ticker.idExcel = idxExcel
                    row_Ticker.comments = tmpComment
                    #row_Ticker.printTicker()
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
                
                if difference > row_Ticker.SignificantLow.highPoint:
                    tmpComment = '[SIGNIFICANT LOW FLUSH]'
                    row_Ticker.SignificantLow.downwardsBreach = None
                    row_Ticker.SignificantLow.Known = False
                    row_Ticker.SignificantLow.Price = None
                    row_Ticker.idExcel = idxExcel
                    row_Ticker.comments = tmpComment
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    #row_Ticker.printTicker()
                    continue
            #endregion

            #region When price action is upwards biased
            if tmpCurrentLowPrice > row_Ticker.SignificantLow.Price: # indicates updwards action and therefore I should look at the high price
                
                difference = tmpCurrentLowPrice - row_Ticker.SignificantLow.Price
                
                # Just upwards price action doesnt mean anything --- it has to come after a downwards breach
                if row_Ticker.SignificantLow.downwardsBreach == False or row_Ticker.SignificantLow.downwardsBreach is None:                    
                    
                    tmpComment = None
                    row_Ticker.idExcel = idxExcel
                    row_Ticker.comment = tmpComment
                    #row_Ticker.printTicker()
                    finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                    continue
                
                if row_Ticker.SignificantLow.downwardsBreach == True:                    
                    
                    if difference < row_Ticker.SignificantLow.lowPoint:
                        row_Ticker.SignificantLow.upwardsBreach = True
                        #tmpComment = ''
                        row_Ticker.idExcel = idxExcel
                        row_Ticker.comment = None
                        #row_Ticker.printTicker()
                        finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                        continue
                
                    if difference >= row_Ticker.SignificantLow.lowPoint:
                        row_Ticker.SignificantLow.upwardsBreach = True
                        
                        # If we buy once in a previous iteration, we dont want to buy again.
                        if (row_Ticker.hasBought == False or row_Ticker.hasBought is None):
                            #tmpComment = 'Current High Price is $ ' + str(difference) + ' higher than SIGNIFICANT LOW PRICE' + '\n'
                            tmpComment = '[ALERT: BUY]'
                            row_Ticker.idExcel = idxExcel
                            row_Ticker.comments = tmpComment
                            row_Ticker.Buy.entryPoint = row_Ticker.currentLowPrice
                            tmpStopLossPrice = float(row_Ticker.setStopLoss('initial'))
                            row_Ticker.Buy.stopLossPrice = float(row_Ticker.Buy.entryPoint) - float(tmpStopLossPrice)
                            row_Ticker.hasBought = True
                            #row_Ticker.comments = 'Looking for atleast $ ' + str(row_Ticker.Sell.profitPerUnit) + ' profit/unit.'
                            #row_Ticker.printTicker()
                            finalDataFrame.loc[len(finalDataFrame)] = row_Ticker.addRecord()
                        continue
                
            #endregion
            
        #endregion
    
    #endregion
    
    #Save data to a csv file
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


if __name__ == "__main__":
    
    fileName='2024-01.csv'
    #fileName = 'dummydata.csv'
    initiate(fileName)