import datetime
import json
import time

import xmltodict
from API.Excel_operations import Excel_Operations
from API.Fleet_Processor import fleet_processor, fleet_data_appender
from API.Gift_Processor import Gift_processor
from API.Product_data_mapping import Product_data_mapping
from config import config


class Outdoor_Request_Builder :

    def __init__(self) :
        self.Request = None
        self.RequestFormat = config.Outdoor_request_format().upper()
        self.Product_Total_Amount = "10.00"
        self.TodaysDate = datetime.datetime.now().strftime('%m/%d/%Y').replace("/", "")
        self.dateYMD = datetime.datetime.now().strftime("%y%m%d")
        self.currentTime = time.strftime("%H:%M:%S:%MS", time.localtime()).replace(":", "")[:-3]
        self.RandomNumber = 123456
        self.POSID = config.POSID()
        self.CCTID = config.CCTID()
        self.APPID = "01"
        self.SessionId = config.SessionId()
        self.ADSDKSpecVer = config.ADSDKSpecVer()
        self.isXml = config.Outdoor_request_format().upper() == "XML"
        self.ParentTransactionTypeMapping = {
            "01" : "01", "02" : "01", "03" : "01", "15" : "01", "16" : "01", "20" : "01",       #for sale
            "04" : "04", "05" : "04", "06" : "04", "07" : "04", "09" : "04",                    #for pre-auth
        }
        self.ChildTransactionTypeMapping = {
            "02" : "02", "07" : "02",                                                           #for refund
            "03" : "06", "06" : "06",                                                           #for void
            "05" : "05",                                                                        #for post-auth
            "09" : "09"                                                                         #for reversal
        }

    def gcb(self, lookUpFlag, TrackData, EncryptionMode, CardDataSource, EMVDetailsData, PINBlock, KSNBlock, PinBlockMode) :
        data = xmltodict.parse(Excel_Operations.Read_Outdoor_File(self.isXml, "GetCardBINRequest.xml")) if self.isXml else json.load(
            Excel_Operations.Read_Outdoor_File(self.isXml, "GetCardBINRequest.json"))
        if data :
            data["GetCardBINRequest"].update({
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "APPID" : self.APPID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "LookUpFlag" : "16", #lookUpFlag,
                "CardDataInfo" : {
                    "CardDataSource" : CardDataSource,
                    "EncryptionMode" : EncryptionMode,
                    "TrackData" : TrackData,
                    "EMVDetailsData" : EMVDetailsData,
                    "PINBlock" : PINBlock,
                    "KSNBlock" : KSNBlock,
                    "PinBlockMode" : PinBlockMode,
                }
            })
            self.Request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.Request

    def Parent_Transaction(self, TransactionSeqNum, TransactionTypeID, TrackData, EncryptionMode, CardDataSource, EMVDetailsData, PINBlock, KSNBlock, PinBlockMode, CardType, TransAmount, PartialAuthAmountIndicator, productCount) :
        data = xmltodict.parse(Excel_Operations.Read_Outdoor_File(self.isXml, "parentTransRequest.xml")) if self.isXml else json.load(
            Excel_Operations.Read_Outdoor_File(self.isXml, "parentTransRequest.json"))
        if data :
            TransactionTypeToRequest = self.ParentTransactionTypeMapping.get(TransactionTypeID)
            self.Product_Total_Amount = TransAmount if PartialAuthAmountIndicator == "1" else self.Product_Total_Amount
            productCount = 0 if TransactionTypeToRequest.upper() == "09" else int(productCount)
            Parent = data["TransRequest"]
            TransAmountDetails = Parent["TransAmountDetails"]
            Parent.update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TransactionType" : TransactionTypeToRequest,
                "TransactionSequenceNumber" : str(TransactionSeqNum).zfill(6),
                **(
                    {"SubTransType" : "04" if TransactionTypeToRequest in ("16", "11") else "",
                     "BlackHawkUpc" : Gift_processor.BlackHawkUpc_finder(fleet_processor.cardnumber_finder(TrackData, CardDataSource)),
                     "ProgramId" : "11" if CardType.upper().endswith("P") else "",
                     } if CardType.upper().startswith("GC") else {}
                ),
                "CardType" : CardType,
                "CardDataInfo" : {
                    "CardDataSource" : CardDataSource,
                    "EncryptionMode" : EncryptionMode,
                    "TrackData" : TrackData,
                    "EMVDetailsData" : EMVDetailsData,
                    "PINBlock" : PINBlock,
                    "KSNBlock" : KSNBlock,
                    "PinBlockMode" : PinBlockMode,
                },
                "ReferenceNumber" : f"{self.TodaysDate}{self.currentTime}{self.RandomNumber}" if CardType.upper() != "EPP" else f"{self.TodaysDate}1234",
                "InvoiceNumber" : f"{self.TodaysDate}{self.currentTime}{self.RandomNumber + 1}",
                "TransactionDate" : self.TodaysDate,
                "TransactionTime" : self.currentTime,
            })
            TransAmountDetails.update({
                "TransactionTotal" : self.Product_Total_Amount,
                "TenderAmount" : self.Product_Total_Amount,
            })
            if productCount != 0 and not CardType.upper().endswith("S") :
                if config.processor().upper() == "CHASE" and CardType.endswith("D") or CardType.endswith("C") :
                    products = Product_data_mapping.ProductData_Mapping(self.Product_Total_Amount, "", TransactionTypeToRequest, "l3productdata", productCount)
                    Parent.update({
                        "Level3ProductsData" :
                            {"Level3ProductCount" : products['Product_count'],
                             "Level3Products" :
                                 {"Level3Product" : products['Product_list']}
                             }
                    })
                if config.processor().upper() == "FD" or (CardType.endswith("F") and CardType.upper() != "EBF") :
                    products = Product_data_mapping.ProductData_Mapping(self.Product_Total_Amount, "", TransactionTypeToRequest, "fleetproductdata", productCount)
                    Parent.update({
                        "FleetData" :
                            {"FleetProductCount" : products['Product_count'],
                             "FleetProducts" :
                                 {"FleetProduct" : products['Product_list']}}})
            if CardType.endswith('F') and TransactionTypeToRequest.upper() not in ["09", "02"] :
                prompts = fleet_processor.Track_data_prompt_finder(TrackData, CardDataSource, CardType)
                cnumber = fleet_processor.cardnumber_finder(TrackData, CardDataSource)
                prompts_appender = fleet_data_appender.Prompt_finder_by_value(prompts, CardType, cnumber)
                Parent.update({
                    "FleetPromptsData" : {
                        prompts_appender
                    }
                })
            self.Request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.Request

    def Child_Transaction(self, productCount, TransactionSeqNum, Transaction_Type, CardType, Parent_TransactionID, Parent_AurusPayTicketNum, TransAmount) :
        data = xmltodict.parse(Excel_Operations.Read_Outdoor_File(self.isXml, "childTransRequest.xml")) if self.isXml else json.load(Excel_Operations.Read_Outdoor_File(self.isXml, "childTransRequest.json"))
        if data:
            TransactionTypeToRequest = self.ParentTransactionTypeMapping.get(Transaction_Type)
            productCount = 0 if TransactionTypeToRequest.upper() == "06" else int(productCount)
            self.Product_Total_Amount = TransAmount if TransactionTypeToRequest.upper() == "06" else self.Product_Total_Amount
            Parent = data["TransRequest"]
            TransAmountDetails = Parent["TransAmountDetails"]
            Parent.update({
                "APPID" : self.APPID,
                "POSID" : self.POSID,
                "CCTID" : self.CCTID,
                "SessionId" : self.SessionId,
                "ADSDKSpecVer" : self.ADSDKSpecVer,
                "TransactionType" : TransactionTypeToRequest,
                "TransactionSequenceNumber" : str(TransactionSeqNum).zfill(6),
                "ReferenceNumber" : f"{self.TodaysDate}{self.RandomNumber}{self.currentTime}" if CardType.upper() != "EPP" else f"{self.TodaysDate}1234",
                "InvoiceNumber" : f"{self.TodaysDate}{self.RandomNumber}{self.currentTime}",
                "TransactionDate" : self.TodaysDate,
                "TransactionTime" : self.currentTime,
                "OrigTransactionIdentifier" : Parent_TransactionID,
                "OrigAurusPayTicketNum" : Parent_AurusPayTicketNum,
                "DuplicateTransCheck" : "",
                "OfflineTicketNumber" : "",
            })
            TransAmountDetails.update({
                "TransactionTotal" : self.Product_Total_Amount,
                "TenderAmount" : self.Product_Total_Amount,
            })
            if productCount != 0 and not CardType.upper().endswith("S") :
                if config.processor().upper() == "CHASE" and (CardType.endswith("D") or CardType.endswith("C")) :
                    products = Product_data_mapping.ProductData_Mapping(TransAmount, "", TransactionTypeToRequest, "l3productdata", productCount)
                    Parent.update({
                        "Level3ProductsData" :
                            {"Level3ProductCount" : products['Product_count'],
                             "Level3Products" :
                                 {"Level3Product" : products['Product_list']}
                             }
                    })
                if config.processor().upper() == "FD" or (CardType.endswith("F") and CardType.upper() != "EBF") :
                    products = Product_data_mapping.ProductData_Mapping(TransAmount, "", TransactionTypeToRequest, "fleetproductdata", productCount)
                    Parent.update({
                        "FleetData" :
                            {"FleetProductCount" : products['Product_count'],
                             "FleetProducts" :
                                 {"FleetProduct" : products['Product_list']}
                             }
                    })
            self.Request = xmltodict.unparse(data, pretty=True) if self.isXml else json.dumps(data)
        return self.Request