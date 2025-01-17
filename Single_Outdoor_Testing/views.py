from config import config
from Response_Builder.Outdoor_response_builder import Transaction_Processing
from django.shortcuts import render
import json
import dict2xml
import re


class Single_Outdoor_Testing:

    def __init__(self):
        self.transaction_processor = Transaction_Processing()
        self.RequestFormat = config.Outdoor_request_format()
        self.API_SEQUENCE = config.API_SEQUENCE().split(",")
        self.result = {}

    def Single_Outdoor_Testing(self, request):
        if request.method == 'POST':
            Iteration = 1
            TrackData = request.POST.get("TrackData", "")
            EmvDetailsData = request.POST.get("EmvData", "")
            PinBlockMode = request.POST.get("pin")
            pinblock = request.POST.get("PinBlock", "")
            ksnblock = request.POST.get("KsnBlock", "")
            TransactionType = request.POST.get("Transaction_Type", "")
            cardDataSource = request.POST.get('cds', "")
            product_count = "01"
            Transaction_total, PartialAuthAmountIndicator = ("", "0") if request.POST['Trn_amt'].upper() == "RANDOM" else (request.POST['Trn_amt'], "1")
            EncryptionMode = "00"
            PinBlockMode = "01" if PinBlockMode == "01" else ""
            PARENTTRANSREQUEST = ""
            CHILDTRANSREQUEST = ""
            Parent_TransactionType = "Sale" if TransactionType in ("01", "02", "03") else "Pre_auth" if TransactionType in ("04", "05", "06", "07", "09") else "GCB" if TransactionType == "00" else None
            Child_TransactionType = "Refund" if TransactionType in ("02", "07") else "Void" if TransactionType in ("03", "06") else "Post_auth" if TransactionType == "05" else "Reversal" if TransactionType == "09" else None

            print(f'Performing # {Iteration} Transaction of {Child_TransactionType + " of" if Child_TransactionType is not None else ""} {Parent_TransactionType}')

            if Parent_TransactionType is not None :
                PARENTTRANSREQUEST = lambda : self.transaction_processor.ParentTransactionProcessing(TransactionType, TrackData, EncryptionMode,
                                                                                                     cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode,
                                                                                                     Transaction_total, PartialAuthAmountIndicator, product_count,
                                                                                                     TransactionSeqNum=Iteration)
            if Child_TransactionType is not None :
                CHILDTRANSREQUEST = lambda : self.transaction_processor.ChildTransactionProcessing(TransactionType, TrackData, EncryptionMode,
                                                                                                   cardDataSource, EmvDetailsData, pinblock, ksnblock, PinBlockMode,
                                                                                                   Transaction_total, PartialAuthAmountIndicator, product_count, Iteration)

            if Parent_TransactionType or Child_TransactionType:
                method_mapping = {
                    'GCB': lambda: self.transaction_processor.GCBTransaction(lookUpFlag, TrackData, EncryptionMode, cardDataSource, EmvDetailsData, pinblock, ksnblock,
                                                                             PinBlockMode) if Parent_TransactionType else None,
                    'TRANSREQUEST': [PARENTTRANSREQUEST, CHILDTRANSREQUEST] if TransactionType != "00" else None
                }
                for method_name in self.API_SEQUENCE:
                    method_name = method_name.upper().strip()
                    lookUpFlag = re.search(r'GCB(\d+)', method_name).group(1) if re.search(r'GCB(\d+)', method_name) else "4"
                    method_name = "GCB" if re.match(r'^GCB\d+', method_name) else method_name
                    method = method_mapping.get(method_name.upper().strip())
                    if method is not None:
                        if isinstance(method, list):
                            for sub_method in method:
                                if sub_method is not None:
                                    sub_method()  # Assuming each item in the list is callable
                        elif callable(method):
                            method()  # Call the function
                        else:
                            print(f"Method {method_name} not found or is not callable.")

            result = {
                "gcb_request": dict2xml.dict2xml(self.transaction_processor.Gcb_Transaction_Request) if self.RequestFormat == "XML" else json.dumps(self.transaction_processor.Gcb_Transaction_Request, sort_keys=False, indent=2),
                "Parent_request": dict2xml.dict2xml(self.transaction_processor.Parent_Transaction_request) if self.RequestFormat == "XML" else json.dumps(self.transaction_processor.Parent_Transaction_request, sort_keys=False, indent=2),
                "Child_request": dict2xml.dict2xml(self.transaction_processor.Child_Transaction_request) if self.RequestFormat == "XML" else json.dumps(self.transaction_processor.Child_Transaction_request, sort_keys=False, indent=2),
                "gcb_response": dict2xml.dict2xml(self.transaction_processor.Gcb_Transaction_Response) if self.RequestFormat == "XML" else json.loads(json.dumps(self.transaction_processor.Gcb_Transaction_Response, sort_keys=False, indent=2)),
                "Parent_response": dict2xml.dict2xml(self.transaction_processor.Parent_Transaction_response) if self.RequestFormat == "XML" else json.dumps(self.transaction_processor.Parent_Transaction_response, sort_keys=False, indent=2),
                "Child_response": dict2xml.dict2xml(self.transaction_processor.Child_Transaction_response) if self.RequestFormat == "XML" else json.dumps(self.transaction_processor.Child_Transaction_response, sort_keys=False, indent=2),
                "Parent_tranasction": str(Parent_TransactionType) + " Transaction",
                "Child_transaction": str(Child_TransactionType) + " Transaction",
                "gcb": "GCB Transaction",
                "RequestFormat": self.RequestFormat
            }
            return render(request, "Single_Outdoor_Testing.html", context=result)
        else:
            return render(request, "Single_Outdoor_Testing.html")