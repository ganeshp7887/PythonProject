from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import re
from Miejer_Petro.settings import BASE_DIR
from config import config
from datetime import datetime
from API.models import API_PARSER
from itertools import zip_longest

class LogComparor:

    def __init__(self):
        self.RequestFormat = config.request_format()
        self.APIPARSER = API_PARSER()
        self.DateTimeNow = datetime.now().strftime("%H-%M-%S_%f")  # Use '-' and '_' to avoid invalid characters
        self.logTextification = []
        self.progress_storage = {}
        self.RequestResponsePattern = ""
        self.timepattern = "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+INFO\s+.*?\]\s+"
        self.xmlRequestpattern = "Final Received Request is in XML Format ::\s*(\<.*\>)"
        self.jsonRequestpattern = "Final Received Request is in JSON Format ::\s*(\{.*\})"
        self.xmlResponsepattern = "sendResponsePOS response send to POS ::\s*(\<.*\>)"
        self.jsonResponsepattern = "sendResponsePOS response send to POS ::\s*(\{.*\})"
        self.pedrequestpattern = "PED REQUEST\s*:\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"
        self.pedresponsepattern = "Alert : Received response from PED for encryption\s*:\s*(.*?)(?=\s*\d{4}-\d{2}-\d{2}|\Z)"
        self.allAPIKeys = []

    def CompareLog(self, request):
        if request.method == 'POST' and (request.FILES.get('file1') and request.FILES.get('file2')):
            print("finally here are we")
            requestType = request.POST.get('requestType', "1").upper().strip()
            getDataAs = "2"
            uploadedFileName = default_storage.save(
                os.path.join(BASE_DIR, "Log", f"{os.path.splitext(request.FILES['file1'].name)[0]}_{self.DateTimeNow}{os.path.splitext(request.FILES['file1'].name)[1]}"),
                ContentFile(request.FILES['file1'].read())
            )
            uploadedFileName2 = default_storage.save(
                os.path.join(BASE_DIR, "Log", f"{os.path.splitext(request.FILES['file2'].name)[0]}_{self.DateTimeNow}{os.path.splitext(request.FILES['file2'].name)[1]}"),
                ContentFile(request.FILES['file2'].read())
            )
            patterns = {
                "1": fr'{self.timepattern}(?:{self.xmlRequestpattern if requestType.upper() == "XML" else self.jsonRequestpattern})',
                "2": fr'{self.timepattern}(?:(?:{self.xmlRequestpattern if requestType.upper() == "XML" else self.jsonRequestpattern})|{self.xmlResponsepattern if requestType.upper() == "XML" else self.jsonResponsepattern})',
                "3": fr'{self.timepattern}(?:(?:(?:(?:{self.xmlRequestpattern if requestType.upper() == "XML" else self.jsonRequestpattern})|{self.xmlResponsepattern if requestType.upper() == "XML" else self.jsonResponsepattern})|{self.pedrequestpattern})|{self.pedresponsepattern})'
            }
            if getDataAs in patterns: self.RequestResponsePattern = re.compile(patterns[getDataAs])
            logsValidation = self.APIPARSER.parse_log_file(uploadedFileName, self.RequestResponsePattern, getDataAs)
            File1LogRequestandResponses = logsValidation[1]
            File1Loggers = logsValidation[3]
            logsValidationForFILE2 = self.APIPARSER.parse_log_file(uploadedFileName2, self.RequestResponsePattern, getDataAs)
            File2LogRequestandResponses = logsValidationForFILE2[1]
            File2Loggers = logsValidationForFILE2[3]
            print(File2Loggers)
            data = zip_longest(File1Loggers, File2Loggers,File1LogRequestandResponses, File2LogRequestandResponses, fillvalue=None)
            datalist = [{'File1Loggers': File1Loggers, "File2Loggers": File2Loggers, "file1sequence" : File1LogRequestandResponses, "file2sequence": File2LogRequestandResponses} for File1Loggers, File2Loggers, File1LogRequestandResponses, File2LogRequestandResponses in data]
            return render(request, 'Log_Comparor.html', {
                'data': datalist,
                'RequestType': requestType,
                'message': 'File uploaded successfully',
            })
        else:
            return render(request, 'Log_Comparor.html')
