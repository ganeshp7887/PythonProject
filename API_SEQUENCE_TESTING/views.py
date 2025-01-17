import time

from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
import re
import os
from Miejer_Petro.settings import BASE_DIR
from config import config
from datetime import datetime
from API.models import API_PARSER
from API.Socket_API import Adsdk_Socket as socket


class ISSUE_SEQUENCE_TESTING :
    def __init__(self) :
        self.RequestFormat = config.request_format()
        self.APIPARSER = API_PARSER()
        self.DateTimeNow = datetime.now().strftime("%H-%M-%S_%f")
        self.timepattern = {"name" : "timePattern", "pattern" : "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+INFO\s+.*?\]\s+(?:\S+\s+)?"}
        self.xmlRequestpattern = {"name" : "POS REQUEST", "pattern" : "Final Received Request is in XML Format ::\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.jsonRequestpattern = {"name" : "POS REQUEST", "pattern" : "@Final Received Request is in JSON Format ::\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.xmlResponsepattern = {"name" : "POS RESPONSE", "pattern" : "sendResponsePOS response send to POS ::\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.jsonResponsepattern = {"name" : "POS RESPONSE", "pattern" : "sendResponsePOS response send to POS ::\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.pedrequestpattern = {"name" : "PED REQUEST", "pattern" : "Request Written to PED :\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.pedresponsepattern = {"name" : "PED RESPONSE", "pattern" : "Alert : Received response from PED for encryption :\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"}
        self.patterns = {}
        self.allAPIKeys = []
        self.socketConnection = socket()
        self.port = config.Config_Indoor_port()
        self.comm = config.commProtocol()

    def issue_sequence_testing(self, request) :
        if request.method == 'POST' :
            if request.FILES.get('file') :
                return self.handle_file_upload(request)
            return self.handle_api_request(request)
        return render(request, 'API_SEQUENCE_TESTING.html')

    def handle_api_request(self, request) :
        if not request.POST.get("Scenario") : return JsonResponse({'status' : 'error', 'message' : 'Scenario not provided'}, status=400)

        timediff = max(float(request.POST.get("timediffArray", 0)) - 30 / 1000, 0.020)
        apiRequestArray = request.POST.get("apiRequestArray", "")
        currentAPI, nextAPI = request.POST.get("currentAPI", ""), request.POST.get("nextAPI", "")

        if "Request" in currentAPI :
            if self.comm == "5" :
                self.socketConnection.httpsRequest(str(apiRequestArray))
            else :
                self.socketConnection.openSocket(self.port)
                self.socketConnection.sendRequest(str(apiRequestArray))
        if "Response" in nextAPI :
            res = self.socketConnection.receiveResponseFromSocket()
            print(f"Received response: {res}")
        elif "Request" in nextAPI :
            time.sleep(float(timediff))
            print(f"Time delay added : {timediff}")
        return JsonResponse({'status' : 'complete', 'nexttimestampASID' : request.POST.get("nexttimestampASID", "")}, status=200)

    def handle_file_upload(self, request) :
        requestType = request.POST.get('requestType', "1").upper().strip()
        getDataAs = request.POST.get('getDataAs', "1").upper().strip()

        uploadedFileName = default_storage.save(
            os.path.join(BASE_DIR, "Log", f"{os.path.splitext(request.FILES['file'].name)[0]}_{self.DateTimeNow}{os.path.splitext(request.FILES['file'].name)[1]}"),
            ContentFile(request.FILES['file'].read())
        )
        self.patterns = {
            "1" : fr"({self.timepattern['pattern']}(?:{self.xmlRequestpattern['pattern'] if requestType.upper() == 'XML' else self.jsonRequestpattern['pattern']})",
            "2" : fr"({self.timepattern['pattern']}(?:(?:{self.xmlRequestpattern['pattern'] if requestType.upper() == 'XML' else self.jsonRequestpattern['pattern']})|{self.xmlResponsepattern['pattern'] if requestType.upper() == 'XML' else self.jsonResponsepattern['pattern']})",
            "3" : fr"({self.timepattern['pattern']}(?:(?:(?:{self.xmlRequestpattern['pattern'] if requestType.upper() == 'XML' else self.jsonRequestpattern['pattern']})|{self.xmlResponsepattern['pattern'] if requestType.upper() == 'XML' else self.jsonResponsepattern['pattern']})|{self.pedrequestpattern['pattern']})",
            "4" : fr"({self.timepattern['pattern']}(?:(?:(?:(?:{self.xmlRequestpattern['pattern'] if requestType.upper() == 'XML' else self.jsonRequestpattern['pattern']})|{self.xmlResponsepattern['pattern'] if requestType.upper() == 'XML' else self.jsonResponsepattern['pattern']})|{self.pedrequestpattern['pattern']})|{self.pedresponsepattern['pattern']})"
        }
        pattern = self.patterns.get(getDataAs)
        RequestResponsePattern = re.compile(pattern)
        logsValidation = self.APIPARSER.parse_log_file(uploadedFileName, RequestResponsePattern, getDataAs)
        data_list = [{'timestamp' : ts, 'api_request' : req, "allAPIKeys" : keys, "loggers" : log, "timedifferences" : time} for ts, req, log, time, keys in logsValidation]
        context = {'data' : data_list, 'RequestType' : requestType, 'message' : 'File uploaded successfully'}
        return render(request, 'API_SEQUENCE_TESTING.html', context)
