import json
import random
from Request_Builder.Outdoor_request_builder import Outdoor_Request_Builder
from config import config
from API.Socket_API import Adsdk_Socket as socket
from API.Excel_operations import Excel_Operations
import traceback


class Transaction_Processing:

    def __init__(self):
        self.Gcb_Transaction_Request = {}
        self.Gcb_Transaction_Response = {}
        self.Parent_Transaction_request = {}
        self.Parent_Transaction_response = {}
        self.Child_Transaction_response = {}
        self.Child_Transaction_request = {}

        self.Gcb_Transaction_ResponseCode = None
        self.Gcb_Transaction_CardType = None
        self.Parent_Transaction_ResponseCode = None
        self.Parent_Transaction_TransactionIdentifier = None
        self.Parent_Transaction_TransactionAmount = None
        self.Parent_Transaction_AurusPayTicketNum = None
        self.Parent_Transaction_TransactionSequenceNumber = None

        self.Outdoor_Request_Builder = Outdoor_Request_Builder()
        self.port = config.Config_Outdoor_port()
        self.isXml = config.Outdoor_request_format().upper() == "XML"
        self.ip = config.Config_machine_ip()
        self.urlExtention = ""
        self.APIurl = ""
        self.isHttps = config.commProtocol() != "9"
        self.url = rf"https://{self.ip}:{self.port}{self.urlExtention}{self.APIurl}"

    def handleSocketRequest(self, request_data, use_socket=True) :
        if use_socket :
            socket.openSocket(port=self.port)
            socket.sendRequest(request_data)
            response = socket.receiveResponseFromSocket()
        else:
            response = socket.httpsRequest(self.url, request_data)
        return response


    def GCBTransaction(self, lookUpFlag, TrackData, EncryptionMode, cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode):

        try:
            Gcb_Transaction_Req = self.Outdoor_Request_Builder.gcb(lookUpFlag, TrackData, EncryptionMode, cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode)
            GCB_Transaction_res = self.handleSocketRequest(Gcb_Transaction_Req, use_socket=self.isHttps)
            data = Excel_Operations.ConvertRequest(Gcb_Transaction_Req, GCB_Transaction_res, self.isXml)
            self.Gcb_Transaction_Request = dict(data[0])
            self.Gcb_Transaction_Response = dict(data[1])
            self.Gcb_Transaction_ResponseCode = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("ResponseCode", "")
            self.Gcb_Transaction_CardType = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("CardType", "")
        except Exception as e:
            print(f"Error in GCBTransaction: {e}")

    def ParentTransactionProcessing(self, TransactionType,TrackData, EncryptionMode, cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode, Transaction_total, PartialAuthAmountIndicator, product_count, TransactionSeqNum):
        try:
            if self.Gcb_Transaction_ResponseCode is not None and self.Gcb_Transaction_ResponseCode.startswith("0"):
                Parent_Transaction_req = self.Outdoor_Request_Builder.Parent_Transaction(TransactionSeqNum, TransactionType, TrackData, EncryptionMode, cardDataSource,
                                                                                         EmvDetailsData, pinblock, ksnblock, PinBlockMode, self.Gcb_Transaction_CardType,
                                                                                         Transaction_total, PartialAuthAmountIndicator, product_count)
                Parent_Transaction_res = self.handleSocketRequest(Parent_Transaction_req, use_socket=self.isHttps)
                data = Excel_Operations.ConvertRequest(Parent_Transaction_req, Parent_Transaction_res, self.isXml)
                self.Parent_Transaction_request = dict(data[0])
                self.Parent_Transaction_response = dict(data[1])
                trans_detail = self.Parent_Transaction_response.get("TransResponse", {}).get("TransDetailsData", {}).get("TransDetailData", {})
                if isinstance(trans_detail, list) and len(trans_detail) > 0: trans_detail = trans_detail[0]
                self.Parent_Transaction_ResponseCode = trans_detail.get("ResponseCode", "")
                self.Parent_Transaction_TransactionIdentifier = trans_detail.get('TransactionIdentifier', "")
                self.Parent_Transaction_TransactionSequenceNumber = trans_detail.get('TransactionSequenceNumber', "")
                self.Parent_Transaction_TransactionAmount = trans_detail.get('TotalApprovedAmount', " ")
                self.Parent_Transaction_AurusPayTicketNum = self.Parent_Transaction_response.get("TransResponse", {}).get("AurusPayTicketNum", "")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error in TransactionProcessing: {e}\nTraceback:\n{tb}")

    def ChildTransactionProcessing(self, TransactionType, TrackData, EncryptionMode, cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode, Transaction_total, PartialAuthAmountIndicator, product_count, TransactionSeqNum):
        try:
            if self.Parent_Transaction_ResponseCode is not None and self.Parent_Transaction_ResponseCode.startswith("0", 0, 1):
                if TransactionType.upper() in ("03","06") : Transaction_total = self.Parent_Transaction_TransactionAmount
                if TransactionType.upper() == "09":
                    Child_Transaction_req = self.Outdoor_Request_Builder.Parent_Transaction(self.Parent_Transaction_TransactionSequenceNumber, TransactionType, TrackData, EncryptionMode, cardDataSource,
                                                                                            EmvDetailsData, pinblock, ksnblock, PinBlockMode, self.Gcb_Transaction_CardType,
                                                                                            Transaction_total, PartialAuthAmountIndicator, product_count)
                else:
                    Child_Transaction_req = self.Outdoor_Request_Builder.Child_Transaction(
                        productCount=product_count, TransactionSeqNum=TransactionSeqNum,
                        Transaction_Type=TransactionType, CardType=self.Gcb_Transaction_CardType, Parent_TransactionID=self.Parent_Transaction_TransactionIdentifier,
                        Parent_AurusPayTicketNum=self.Parent_Transaction_AurusPayTicketNum,
                        TransAmount=Transaction_total)
                Child_Transaction_res = self.handleSocketRequest(Child_Transaction_req, use_socket=self.isHttps)
                data = Excel_Operations.ConvertRequest(Child_Transaction_req, Child_Transaction_res, self.isXml)
                self.Child_Transaction_request = dict(data[0])
                self.Child_Transaction_response = dict(data[1])
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error in child TransactionProcessing: {e}\nTraceback:\n{tb}")