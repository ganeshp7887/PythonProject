import datetime
import json
import time
import xmltodict

from config import config
from API.Excel_operations import Excel_Operations
from API.Gift_Processor import Gift_processor
from API.Product_data_mapping import Product_data_mapping
from decimal import Decimal, ROUND_HALF_UP


class Transaction_Request_Builder :

    def __init__(self) :
        self.request = None
        self.POSID = config.POSID()
        self.CCTID = config.CCTID()
        self.SessionId = config.SessionId()
        self.ADSDKSpecVer = config.ADSDKSpecVer()
        self.APPID = "01"
        self.TodaysDate = datetime.datetime.now().strftime('%m/%d/%Y').replace("/", "")
        self.currentTime = time.strftime("%H:%M:%S:%MS", time.localtime()).replace(":", "")[:-3]
        self.DefaultAmount = "100.00" #Decimal(Decimal((str(random.randint(0, 99)))).quantize(Decimal('1.00')))
        self.isXml = config.request_format().upper() == "XML"
        self.ParentTransactionTypeMapping = {
            "01" : "01", "02" : "01", "03" : "01", "15" : "01", "16" : "01", "20" : "01",  # for sale
            "04" : "04", "05" : "04", "06" : "04",  # for pre-auth
            "07" : "02", "08" : "02",  # for refund
            "09" : "11", "10" : "16", "11" : "18", "12" : "12", "13" : "11", "14" : "16"  # for gift
        }
        self.ChildTransactionTypeMapping = {
            "02" : "02", "15" : "02", "16" : "02", #refund
            "03" : "06", "06" : "06", "08" : "06", #void
            "05" : "05", #post-auth
            "20" : "76" #cancellast
        }

    def InitAESDKRequest(self):
        data = Excel_Operations.readFile(self.isXml, "InitAESDKRequest.txt")
        if data:
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def CCTTicketDisplayRequest(self, productCount) :
        data = Excel_Operations.readFile(self.isXml, "CCTTicketDisplayRequest.txt")
        if data :
            data["CCTTicketDisplayRequest"].update({
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "APPID" : self.APPID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TransTotalAmount" : str(self.DefaultAmount),
                "HeaderText" : "Please check Products"
            })
            if productCount != 0 :
                products = Product_data_mapping.ProductData_Mapping(str(self.DefaultAmount), "", "TransactionType", "TicketProductData", productCount)
                product_count = products['Product_count']
                product_list = products['Product_list']
                data["CCTTicketDisplayRequest"].update({
                    "TicketProductData" : {
                        "TicketCount" : "1",
                        "Tickets" : {
                            "Ticket" : {
                                "TicketNumber" : "001",
                                "ProductCount" : str(product_count),
                                "Products" : {
                                    "Product" : list(product_list)
                                }
                            }
                        }
                    }
                })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def GetStatusRequest(self, Type) :
        data = Excel_Operations.readFile(self.isXml, "GetStatusRequest.txt")
        if data :
            data["GetStatusRequest"].update({
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "APPID" : self.APPID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "StatusType" : Type
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def SignatureRequest(self) :
        data = Excel_Operations.readFile(self.isXml, "SignatureRequest.txt")
        if data :
            data["SignatureRequest"].update({
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "APPID" : self.APPID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,

            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def RestartCCTRequest(self):
        data = xmltodict.parse(Excel_Operations.Read_Indoor_File(self.isXml, "RestartCCTRequest.xml")) if self.isXml else json.load(
            Excel_Operations.Read_Indoor_File(self.isXml, "RestartCCTRequest.txt"))
        if data:
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def GetCardBINRequest(self, AllowKeyedEntry, EntrySource, LookUpFlag) :
        data = Excel_Operations.readFile(self.isXml, "GetCardBINRequest.txt")
        if data :
            data["GetCardBINRequest"].update({
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "APPID" : self.APPID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TenderAmount" : self.DefaultAmount,
                "AllowKeyedEntry" : AllowKeyedEntry,
                "EntrySource" : EntrySource,
                "LookUpFlag" : LookUpFlag,
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def ShowScreenRequest(self, message, message2, flag) :
        data = Excel_Operations.readFile(self.isXml, "ShowScreenRequest.txt")
        if data :
            data["ShowScreenRequest"].update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "MessageLine1" : message,
                "MessageLine2" : message2,
                "ActivityFlag" : flag
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def ShowListRequest(self, OptionsType) :
        data = Excel_Operations.readFile(self.isXml, "ShowListRequest.txt")
        if data :
            data["ShowListRequest"].update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "OptionsType" : OptionsType
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def GetUserInputRequest(self, message, option) :
        data = Excel_Operations.readFile(self.isXml, "GetUserInputRequest.txt")
        if data :
            data["GetUserInputRequest"].update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "HeaderText" : message,
                "Type" : option
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def ByPassScreenRequest(self, ByPassOptions) :
        data = Excel_Operations.readFile(self.isXml, "ByPassScreenRequest.txt")
        if data :
            data["ByPassScreenRequest"].update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "ByPassOptions" : str(ByPassOptions)
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def Parent_Transaction(self,AllowKeyedEntry, Token_type, TransactionTypeID, Token, CardType, productCount, RandomNumber, TransAmount, cashbackAmount) :
        data = Excel_Operations.readFile(self.isXml, "TransRequest.txt")
        if data :
            def set_default(var, default="") :
                return var if var is not None else default

            Token_type, Token, CardType = map(set_default, [Token_type, Token, CardType])
            TransAmount = str(TransAmount) if TransAmount is not None else str(self.DefaultAmount)
            rounded_value = str((Decimal(TransAmount) / 4).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            TransactionTypeToRequest = self.ParentTransactionTypeMapping.get(TransactionTypeID)
            productCount = 1 if TransactionTypeToRequest == "04" else productCount
            EntrySource = "K" if AllowKeyedEntry.upper() == "Y" else ""
            Parent = data["TransRequest"]

            TransAmountDetails = Parent["TransAmountDetails"]
            Parent.update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TransactionType" : TransactionTypeToRequest,
                "EntrySource" : EntrySource,
                **(
                    {"SubTransType" : "04" if TransactionTypeToRequest in ("14", "11") else "",
                     "BlackHawkUpc" : Gift_processor.BlackHawkUpc_finder(Token),
                     "ProgramId" : "11" if CardType.upper().endswith("P") else "",
                     } if CardType.upper().startswith("GC") else {}
                ),
                **(
                    {"CardToken" : Token} if Token_type == "01" else
                    {"CRMToken" : Token} if Token_type == "03" else
                    {"ECOMMInfo" : {"CardIdentifier" : Token} if Token_type == "02" else {}}
                ),
                "ReferenceNumber" : f"{self.TodaysDate}{RandomNumber}{self.currentTime}" if CardType.upper() != "EPP" else f"{self.TodaysDate}1234",
                "InvoiceNumber" : f"{self.TodaysDate}{RandomNumber}{self.currentTime}",
                "TransactionDate" : self.TodaysDate,
                "TransactionTime" : self.currentTime,
            })
            TransAmountDetails.update({
                "TransactionTotal" : TransAmount,
                "TenderAmount" : TransAmount,
                **({"EbtAmount" : TransAmount} if CardType.upper() == "EBF" else {}),
                **({'PrescriptionAmount' : rounded_value,
                    'CoPaymentAmount' : rounded_value,
                    'DentalAmount' : rounded_value,
                    'VisionOpticalAmount' : rounded_value,
                    'HealthCareAmount' : TransAmount,
                    'FSAAmount' : TransAmount} if CardType.upper().endswith("S") else {})
            })
            if productCount != 0 and not CardType.upper().endswith("S") :
                #if config.processor().upper() == "FD" or (CardType.endswith("F") and CardType.upper() != "EBF") :
                if config.processor().upper() == "CHASE" and CardType.endswith("D") or CardType.endswith("C") :
                    products = Product_data_mapping.ProductData_Mapping(TransAmount, cashbackAmount, TransactionTypeToRequest, "l3productdata", productCount)
                    Parent.update({
                        "Level3ProductsData" :
                            {"Level3ProductCount" : products['Product_count'],
                             "Level3Products" :
                                 {"Level3Product" : products['Product_list']}
                             }
                    })
                if config.processor().upper() == "FD" or (CardType.endswith("F") and CardType.upper() != "EBF") :
                #if config.processor().upper() == "CHASE" and CardType.endswith("D") or CardType.endswith("C") :
                    products = Product_data_mapping.ProductData_Mapping(TransAmount, cashbackAmount, TransactionTypeToRequest, "fleetproductdata", productCount)
                    Parent.update({
                        "FleetData" :
                            {"FleetProductCount" : products['Product_count'],
                             "FleetProducts" :
                                 {"FleetProduct" : products['Product_list']}}})
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def Child_Transaction(self, RandomNumber, TransactionTypeID, Parent_TransactionID, Parent_AurusPayTicketNum, CardType, productCount, Transaction_total) :
        FileName = "CancelLastTransRequest" if TransactionTypeID.upper() == "20" else "ChildTransRequest"
        data = Excel_Operations.readFile(self.isXml, FileName+".txt")
        if data :
            CardType = "XXC" if CardType is None else CardType
            TransactionTypeToRequest = self.ChildTransactionTypeMapping.get(TransactionTypeID)
            Child = data["CancelLastTransRequest"] if TransactionTypeID.upper() == "20" else data["TransRequest"]
            Child.update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TransactionType" : TransactionTypeToRequest,
                **({
                       "ReferenceNumber" : f"{self.TodaysDate}{RandomNumber}{self.currentTime}" if CardType.upper() != "EPP" else f"{self.TodaysDate}1234",
                       "InvoiceNumber" : f"{self.TodaysDate}{RandomNumber}{self.currentTime}",
                       "OrigTransactionIdentifier" : Parent_TransactionID,
                       "OrigAurusPayTicketNum" : Parent_AurusPayTicketNum,
                       "TransactionDate" : self.TodaysDate,
                       "TransactionTime" : self.currentTime,
                       "TransAmountDetails" : {
                           "TransactionTotal" : Transaction_total,
                           "TenderAmount" : Transaction_total,
                       }
                   } if TransactionTypeID.upper() != "20" else
                   {
                       "Date" : self.TodaysDate,
                       "Time" : self.currentTime
                   }), #cancellast check
            })

            if productCount != 0 and TransactionTypeToRequest.upper() in ("02", "05"):
                if config.processor().upper() == "CHASE" and CardType.endswith("D") or CardType.endswith("C") :
                    products = Product_data_mapping.ProductData_Mapping(Transaction_total,"", TransactionTypeToRequest, "l3productdata", productCount)
                    Child.update({
                        "Level3ProductsData" :
                            {"Level3ProductCount" : products['Product_count'],
                             "Level3Products" :
                                 {"Level3Product" : products['Product_list']}
                             }
                    })
                if config.processor().upper() == "FD" or CardType.endswith("F") :
                    products = Product_data_mapping.ProductData_Mapping(Transaction_total,"", TransactionTypeToRequest, "fleetproductdata", productCount)
                    Child.update({
                        "FleetData" :
                            {"FleetProductCount" : products['Product_count'],
                             "FleetProducts" :
                                 {"FleetProduct" : products['Product_list']}
                             }
                })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request

    def CloseTransactionRequest(self) :
        data = Excel_Operations.readFile(self.isXml, "CloseTransactionRequest.txt")
        if data :
            CloseTransactionRequest = data["CloseTransactionRequest"]
            CloseTransactionRequest.update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
            })
            self.request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.request
