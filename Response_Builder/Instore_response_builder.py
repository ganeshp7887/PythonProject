import json
import time
import threading
from Request_Builder.Instore_request_builder import Transaction_Request_Builder
from API.Socket_API import Adsdk_Socket as socket
from config import config
from API.Excel_operations import Excel_Operations
import random
import traceback


class Transaction_Processing :

    def __init__(self):

        self.Gcb_Transaction_Request = {}
        self.Gcb_Transaction_Response = {}
        self.Parent_Transaction_request = {}
        self.Parent_Transaction_response = {}
        self.Child_Transaction_response = {}
        self.Child_Transaction_request = {}
        self.GETUSERINPUT_Request = {}
        self.GETUSERINPUT_Response = {}

        self.Gcb_Transaction_CardType = None
        self.Gcb_Transaction_ResponseCode = None
        self.Gcb_Transaction_ResponseText = None
        self.Gcb_Transaction_CardToken = None
        self.Gcb_Transaction_CIToken = None
        self.Gcb_Transaction_CRMToken = None
        self.Gcb_Transaction_CashbackAmount = None

        self.GetUserInput_inputText = None

        self.Parent_Transaction_ResponseCode = None
        self.Parent_Transaction_ResponseText = None
        self.Parent_Transaction_TransactionAmount = None
        self.Parent_Transaction_TransactionIdentifier = None
        self.Parent_Transaction_AurusPayTicketNum = None

        self.Child_Transaction_ResponseText = None
        self.Child_Transaction_TransactionIdentifier = None

        self.RandomNumberForInvoice = random.randint(100000, 999999)
        self.port = config.Config_Indoor_port()
        self.OutdoorPort = config.Config_Outdoor_port()
        self.Transaction_Request_Builder = Transaction_Request_Builder()
        self.ip = config.Config_machine_ip()
        self.urlExtension = ""
        self.APIurl = ""
        self.url = rf"https://{self.ip}:{self.port}{self.urlExtension}{self.APIurl}"
        self.isHttps = config.commProtocol() != "5"
        self.isXml = config.request_format().upper() == "XML"
        self.isSignatureEnabled = "0"
        self.ParentTransactionType = ""
        self.ChildTransactionType = ""

    def InitAESDKRequest(self):
        self.handleSocketRequest(self.Transaction_Request_Builder.InitAESDKRequest(), False, "", use_socket=self.isHttps)

    def handleSocketRequest(self, request_data, bypassEnabled, bypassOption, use_socket=True) :
        if use_socket :
            socket.openSocket(port=self.port)
            socket.sendRequest(request_data)
            response = socket.receiveResponseFromSocket()
        else :
            threads = []
            response_list = []
            if bypassEnabled :
                bypassData = self.Transaction_Request_Builder.ByPassScreenRequest(bypassOption)
                data = [request_data, bypassData]

                def send_request(url, request_data) :
                    response = socket.httpsRequest(url, request_data)
                    if '{"ByPassScreenResponse":' not in response : response_list.append(response)

                for i in data :
                    thread = threading.Thread(target=send_request, args=(self.url, i))
                    threads.append(thread)
                    thread.start()
                    time.sleep(3)
                for thread in threads : thread.join()
                response = response_list[0]
            else :
                response = socket.httpsRequest(self.url, request_data)
        print(response)
        return response

    def GetStatusRequest(self, RequestType, bypassEnabled, bypassOption) :
        self.handleSocketRequest(self.Transaction_Request_Builder.GetStatusRequest(RequestType), bypassEnabled, bypassOption, use_socket=self.isHttps)

    def RestartCCTRequestTransaction(self):
        self.handleSocketRequest(self.Transaction_Request_Builder.RestartCCTRequest(), "", "", use_socket=self.isHttps)

    def Signature(self, bypassEnabled, bypassOption) :
        self.handleSocketRequest(self.Transaction_Request_Builder.SignatureRequest(), bypassEnabled, bypassOption, use_socket=self.isHttps)

    def displayTicket(self, productCount, bypassEnabled, bypassOption) :
        self.handleSocketRequest(self.Transaction_Request_Builder.CCTTicketDisplayRequest(productCount), bypassEnabled, bypassOption, use_socket=self.isHttps)

    def GCBTransaction(self, AllowKeyedEntry, EntrySource, LookUpFlag, bypassEnabled, bypassOption) :
        """Handle GCB transaction and parse the response."""
        try :
            Gcb_Transaction_Req = self.Transaction_Request_Builder.GetCardBINRequest(AllowKeyedEntry, EntrySource, LookUpFlag)
            GCB_Transaction_res = self.handleSocketRequest(Gcb_Transaction_Req, bypassEnabled, bypassOption, use_socket=self.isHttps)
            data = Excel_Operations.ConvertRequest(Gcb_Transaction_Req, GCB_Transaction_res, isXML=self.isXml)
            self.Gcb_Transaction_Request = dict(data[0])
            self.Gcb_Transaction_Response = dict(data[1])
            self.Gcb_Transaction_ResponseCode = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("ResponseCode", "")
            self.Gcb_Transaction_ResponseText = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("ResponseText", "")
            self.Gcb_Transaction_CardType = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("CardType", "")
            self.Gcb_Transaction_CashbackAmount = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("CashBackAmount", "")
            if self.Gcb_Transaction_ResponseCode.startswith("0") :
                self.Gcb_Transaction_CardToken = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("CardToken", "")
                if LookUpFlag in ["16", "8"] :
                    self.Gcb_Transaction_CIToken = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("ECOMMInfo", {}).get("CardIdentifier", "")
                    self.Gcb_Transaction_CRMToken = self.Gcb_Transaction_Response.get("GetCardBINResponse").get("CRMToken", "")
            else:
                self.CLOSETransaction()
        except Exception as e :
            print(f"Error in GCBTransaction: {e}\nTraceback:\n{traceback.format_exc()}")

    def SHOWLIST(self, OptionsType, bypassEnabled, bypassOption) :
        try : self.handleSocketRequest(self.Transaction_Request_Builder.ShowListRequest(OptionsType), bypassEnabled, bypassOption, use_socket=self.isHttps)
        except Exception as e : print(f"Error in SHOWLIST: {e}\nTraceback:\n{traceback.format_exc()}")

    def BYPASSTransaction(self, bypassoption) :
        try : self.handleSocketRequest(self.Transaction_Request_Builder.ByPassScreenRequest(bypassoption), False, "", use_socket=self.isHttps)
        except Exception as e : print(f"Error in BYPASSTransaction: {e}\nTraceback:\n{traceback.format_exc()}")

    def SHOWSCREEN(self, message, flag, bypassEnabled, bypassOption) :
        try :
            message2 = self.GetUserInput_inputText if self.GetUserInput_inputText else ""
            showscrn = self.Transaction_Request_Builder.ShowScreenRequest(str(message), str(message2), flag)
            self.handleSocketRequest(showscrn, bypassEnabled, bypassOption, use_socket=self.isHttps)
        except Exception as e :
            print(f"Error in SHOWSCREEN: {e}\nTraceback:\n{traceback.format_exc()}")

    def GETUSERINPUT(self, message, option, bypassEnabled, bypassOption) :
        """Get user input."""
        try :
            gui = self.Transaction_Request_Builder.GetUserInputRequest(message, option)
            guiResponse = self.handleSocketRequest(gui, bypassEnabled, bypassOption, use_socket=self.isHttps)
            data = Excel_Operations.ConvertRequest(gui, guiResponse, isXML=self.isXml)
            self.GETUSERINPUT_Request = dict(data[0])
            self.GETUSERINPUT_Response = dict(data[1])
            self.GetUserInput_inputText = self.GETUSERINPUT_Response.get("GetUserInputResponse").get("InputData")
        except Exception as e :
            print(f"Error in GETUSERINPUT: {e}\nTraceback:\n{traceback.format_exc()}")

    def ParentTransactionProcessing(self,AllowKeyedEntry, productCount, Token_type, TransactionType, TransAmount) :
        """Process the transaction and handle parent and child transactions."""
        try :
            if self.Gcb_Transaction_ResponseCode is None or self.Gcb_Transaction_ResponseCode.startswith("0") :
                Token = {"01" : self.Gcb_Transaction_CardToken, "02" : self.Gcb_Transaction_CIToken, "03" : self.Gcb_Transaction_CRMToken}.get(Token_type, None)
                Parent_Transaction_req = self.Transaction_Request_Builder.Parent_Transaction(AllowKeyedEntry=AllowKeyedEntry,
                    RandomNumber=self.RandomNumberForInvoice,
                    productCount=productCount,
                    Token_type=Token_type, Token=Token,
                    TransactionTypeID=TransactionType, CardType=self.Gcb_Transaction_CardType,
                    TransAmount=TransAmount, cashbackAmount=self.Gcb_Transaction_CashbackAmount
                )
                Parent_Transaction_res = self.handleSocketRequest(Parent_Transaction_req, False, "", use_socket=self.isHttps)
                data = Excel_Operations.ConvertRequest(Parent_Transaction_req, Parent_Transaction_res, isXML=self.isXml)
                self.Parent_Transaction_request = dict(data[0])
                self.Parent_Transaction_response = dict(data[1])
                TransType = self.Parent_Transaction_request.get("TransRequest").get("TransactionType")
                trans_detail = self.Parent_Transaction_response.get("TransResponse", {}).get("TransDetailsData", {}).get("TransDetailData", {})
                if isinstance(trans_detail, list) and len(trans_detail) > 0 : trans_detail = trans_detail[0]
                self.Parent_Transaction_ResponseCode = trans_detail.get("ResponseCode", "")
                self.Parent_Transaction_ResponseText = trans_detail.get("ResponseText", "")
                self.Parent_Transaction_TransactionIdentifier = trans_detail.get('TransactionIdentifier', "")
                self.Parent_Transaction_TransactionAmount = trans_detail.get('TotalApprovedAmount', " ")
                self.isSignatureEnabled = trans_detail.get("SignatureReceiptFlag", "") if trans_detail.get("SignatureReceiptFlag", "") is not None else self.isSignatureEnabled
                self.Parent_Transaction_AurusPayTicketNum = self.Parent_Transaction_response.get("TransResponse", {}).get("AurusPayTicketNum", "")
                self.ParentTransactionType = "Sale" if TransType == "01" else "Pre-auth" if TransType == "04" else "Refund w/o Sale" if TransType == "02" else "Gift Transactions"
                if TransactionType == "20" : time.sleep(1)
                if self.isSignatureEnabled in ("1", "3") : time.sleep(1); self.Signature(False, "")
            if TransactionType != "20" : self.CLOSETransaction()
        except Exception as e :
            print(f"Error in TransactionProcessing: {e}\nTraceback:\n{traceback.format_exc()}")

    def ChildTransactionProcessing(self, childData, productCount, Child_TransactionType) :
        default_values = {
            'Parent_Transaction_ResponseCode' : self.Parent_Transaction_ResponseCode,
            'Parent_Transaction_TransactionIdentifier' : self.Parent_Transaction_TransactionIdentifier,
            'Parent_Transaction_AurusPayTicketNum' : self.Parent_Transaction_AurusPayTicketNum,
            'Gcb_Transaction_CardType' : self.Gcb_Transaction_CardType,
            'Parent_Transaction_TransactionAmount' : self.Parent_Transaction_TransactionAmount
        }

        if childData is not None :
            childData = json.loads(childData)
            default_values.update({
                'Parent_Transaction_ResponseCode' : childData.get('Parent_Transaction_ResponseCode'),
                'Parent_Transaction_TransactionIdentifier' : childData.get('Parent_Transaction_TransactionIdentifier'),
                'Parent_Transaction_AurusPayTicketNum' : childData.get('Parent_Transaction_AurusPayTicketNum'),
                'Gcb_Transaction_CardType' : childData.get('Parent_Transaction_CardType'),
                'Parent_Transaction_TransactionAmount' : childData.get('Parent_Transaction_TransactionAmount')
            })
        Parent_Transaction_ResponseCode = default_values['Parent_Transaction_ResponseCode']
        Parent_Transaction_TransactionIdentifier = default_values['Parent_Transaction_TransactionIdentifier']
        Parent_Transaction_AurusPayTicketNum = default_values['Parent_Transaction_AurusPayTicketNum']
        Gcb_Transaction_CardType = default_values['Gcb_Transaction_CardType']
        Parent_Transaction_TransactionAmount = default_values['Parent_Transaction_TransactionAmount']
        if Parent_Transaction_ResponseCode is not None and Parent_Transaction_ResponseCode.startswith("0") :
            if Child_TransactionType in {"02", "03", "05", "06", "08", "20"} :
                Child_Transaction = self.Transaction_Request_Builder.Child_Transaction(
                    RandomNumber=self.RandomNumberForInvoice,
                    productCount=productCount,
                    Parent_TransactionID=Parent_Transaction_TransactionIdentifier,
                    Parent_AurusPayTicketNum=Parent_Transaction_AurusPayTicketNum,
                    CardType=Gcb_Transaction_CardType,
                    Transaction_total=Parent_Transaction_TransactionAmount,
                    TransactionTypeID=Child_TransactionType
                )
                child_Transaction_res = self.handleSocketRequest(Child_Transaction, False, "", use_socket=self.isHttps)
                data = Excel_Operations.ConvertRequest(Child_Transaction, child_Transaction_res, isXML=self.isXml)
                self.Child_Transaction_request = dict(data[0])
                self.Child_Transaction_response = dict(data[1])
                RequestTop_node = next(iter(self.Child_Transaction_request))
                ResponseTopNode = next(iter(self.Child_Transaction_response))
                TransType = self.Child_Transaction_request.get(RequestTop_node).get("TransactionType")
                trans_detail = self.Child_Transaction_response.get(ResponseTopNode, {}).get("TransDetailsData", {}).get("TransDetailData", {})
                if isinstance(trans_detail, list) and len(trans_detail) > 0 : trans_detail = trans_detail[0]
                self.Child_Transaction_ResponseText = trans_detail.get("ResponseText", "")
                self.Child_Transaction_TransactionIdentifier = trans_detail.get("TransactionIdentifier", "")
                self.ChildTransactionType = "Refund" if TransType == "02" else "Void" if TransType == "06" else "Post-auth" if TransType == "05" else "CancelLast" if TransType == "76" else None
                self.CLOSETransaction()

    def CLOSETransaction(self) :
        """Close the transaction."""
        try :
            time.sleep(2)
            self.handleSocketRequest(self.Transaction_Request_Builder.CloseTransactionRequest(), False, "", use_socket=self.isHttps)
            time.sleep(0.5)
        except Exception as e :
            print(f"Error in CLOSETransaction: {e}")