import json
#from buy import Buy
#from sell import Sell

tickerSettings = dict()
buySettings = dict()
sellSettings = dict()
allSettings = dict()

class Ticker:
    def __init__(self,parametersFile):
        
        allSettings = self.loadParameters(parametersFile)
                
        self.idExcel = None
        self.timeStamp = None
        self.currentLowPrice = None
        self.currentHighPrice = None
        self.lowestPrice = None
        self.comments = None
        self.hasBought = None
        self.Buy = Buy(allSettings)
        self.Sell = Sell(allSettings)
        self.SignificantLow = SignificantLow(allSettings)
        


    def loadParameters(self,parametersFile):
        try:
            with open(parametersFile, 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print('Parameter file not found. Aborting operations.')
            return None
        
    def printTicker(self):
               
        print('Row#:',self.idExcel if self.idExcel != None else 'N/A', '| Timestamp:', self.timeStamp if self.timeStamp != None else 'N/A')
        print ('Comments: ', self.comments if self.comments != None else 'No ALERT')
        print('Current High Price:',self.currentHighPrice if self.currentHighPrice != None else 'N/A', '| Current Low Price:', self.currentLowPrice if self.currentLowPrice != None else 'N/A')
        print('LOWEST PRICE so far:',self.lowestPrice if self.lowestPrice != None else 'N/A')
        print('SIGNIFICANT LOW KNOWN:', self.SignificantLow.Known if self.SignificantLow.Known != None else 'N/A', '| SIGNIFICANT LOW PRICE: $', self.SignificantLow.Price if self.SignificantLow.Price != None else 'N/A' )
        #print ('Comments: ', self.comments if self.comments != None else 'No Comments')
        if(self.hasBought):
            print('Total units owned:', self.Buy.units if self.Buy.units != None else 'N/A' )
            print('Total cost of purchase:', self.Buy.units * self.Buy.entryPoint if self.Buy.units != None and self.Buy.entryPoint != None else 'N/A' ) 
            print('Stop Loss set at:', self.Buy.stopLossPrice if self.Buy.stopLossPrice != None else 'N/A')
        
        if(self.Sell.sellSequence != None):
            print('Units Sold: ', self.Sell.unitsSold)
            print('Selling Price: $', self.Buy.stopLossPrice)
            print('Units Left: $', self.Buy.units - float(self.Sell.unitsSold))     
        print('************************************************************************************')  
        
    def setStopLoss(self,key):
        
        stopLossPrice = self.Buy.stopLoss[key] 
        
        if stopLossPrice == "-1":
            self.Buy.stopLossPrice = self.Buy.entryPoint
        
        else:     
            self.Buy.stopLossPrice =  self.Buy.entryPoint - float(stopLossPrice)
        
        return self.Buy.stopLossPrice
    
    def addRecord(self):
        #columns = ['Alert','Row Index','Timestamp','High Price','Low Price','Lowest Price','Significant Low Price','Units Bought','Entry Point','Stop Loss','Units Sold','Units Left']
        #tempList = []
            
        ##tempList.append(self.comments if self.comments != None else '')
        #tempList.append(self.idExcel if self.idExcel != None else '')
        #tempList.append(self.timeStamp if self.timeStamp != None else '')
        #tempList.append(self.currentHighPrice if self.currentHighPrice != None else '')
        #tempList.append(self.currentLowPrice if self.currentLowPrice != None else '')
        #tempList.append(self.lowestPrice if self.lowestPrice != None else '')
        #tempList.append(self.SignificantLow.Price if self.SignificantLow.Known else '')
        #tempList.append(self.Buy.units if self.hasBought else '')
        #tempList.append(self.Buy.entryPoint if self.hasBought else '')
        #tempList.append(self.Buy.stopLossPrice if self.hasBought else '')
        #tempList.append(self.Sell.unitsSold if self.Sell.sellSequence != None else '')
        #tempList.append(self.Buy.units - float(self.Sell.unitsSold) if self.Sell.sellSequence != None else '')
        
        new_row = {'Alert': self.comments if self.comments != None else 'No Alert',
                   'Row Index': self.idExcel if self.idExcel!= None else '',
                   'Timestamp': self.timeStamp if self.timeStamp != None else '',
                   'High Price': self.currentHighPrice if self.currentHighPrice != None else '',
                   'Low Price': self.currentLowPrice if self.currentLowPrice != None else '',
                   'Lowest Price': self.lowestPrice if self.lowestPrice != None else '',
                   'Significant Low Price': self.SignificantLow.Price if self.SignificantLow.Price != None else '',
                   'Units Bought': self.Buy.units if self.hasBought != None else '',
                   'Entry Point': self.Buy.entryPoint if self.Buy.entryPoint != None else '',
                   'Stop Loss': self.Buy.stopLossPrice if self.Buy.stopLossPrice != None else '',
                   'Units Sold': self.Sell.unitsSold if self.Sell.unitsSold != None else '',
                   'Units Left' : self.Buy.units - float(self.Sell.unitsSold) if self.Sell.sellSequence != None else ''
        }
        
        return new_row

class SignificantLow:
    def __init__(self,allSettings):
        
        self.Known = None
        self.Marker = float(allSettings['ticker']['significantLowMarker'])
        self.lowPoint = float(allSettings['ticker']['lower'])
        self.highPoint = float(allSettings['ticker']['upper'])
        self.Price = None
        self.downwardsBreach = None
        self.upwardsBreach = None

class Buy:
    def __init__(self,allSettings):
                
        self.units = float(allSettings['buy']['units'])
        self.entryPoint = None
        self.stopLoss = allSettings['buy']['stopLoss']
        self.stopLossPrice = None
        
class Sell:
    def __init__(self,allSettings):

        self.perUnitSellingPrice = None        
        self.profitPerUnit = float(allSettings['sell']['profitPerUnit'])
        self.percentageToSell = float(allSettings['sell']['percentageToSell'])
        self.revenueTotal = None
        self.profitTotal = None
        self.unitsSold =  None
        self.sellSequence = None