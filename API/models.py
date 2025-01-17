import xmltodict
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from lxml import etree
import re
from collections import defaultdict


class API_PARSER:

    def __init__(self):
        self.logTextification = []

    def parse_log_file(self, file_path, pattern, getDataAs):
        """Reads the log file and extracts timestamps and JSON/XML data."""
        timedifferences = ["0.000"]
        with open(file_path, 'r') as file: log_entries = file.read()
        matches = pattern.findall(log_entries)
        timestamps = [match[0] for match in matches]
        aesdk_requests = self.extract_requests(matches, getDataAs)
        Logs = self.Log_simplifier(aesdk_requests)
        processedLogs = Logs[0]
        getAPIKeys = Logs[1]
        datetime_objects = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S,%f") for ts in timestamps]
        timedifferences.extend(self.calculate_time_differences(datetime_objects))
        return zip(timestamps, aesdk_requests, processedLogs, timedifferences, getAPIKeys)

    def extract_requests(self, matches, getDataAs):
        """Extract requests based on the provided criteria."""
        aesdkrequest = ""
        if getDataAs == "1":
            aesdkrequest = [match[1] for match in matches if match[1]]
        if getDataAs == "2":
            aesdkrequest = [match[1] or match[2] for match in matches if match[1] or match[2]]
        if getDataAs == "3":
            aesdkrequest = [match[1] or match[2] or match[3] for match in matches if match[1] or match[2] or match[3]]
        if getDataAs == "4":
            aesdkrequest = [match[1] or match[2] or match[3] or match[4] for match in matches if match[1] or match[2] or match[3] or match[4]]
        return aesdkrequest

    def calculate_time_differences(self, datetime_objects):
        """Calculate time differences between consecutive timestamps."""
        return [(datetime_objects[i] - datetime_objects[i - 1]).total_seconds() for i in range(1, len(datetime_objects))]

    def Log_simplifier(self, aesdk_requests):
        getAPIKeys = []
        processedLogs = []
        for logline in aesdk_requests:
            if logline.startswith("<"):
                parser = etree.XMLParser(resolve_entities=False)
                print(logline)
                request = xmltodict.parse(etree.tostring(etree.fromstring(logline, parser=parser), encoding=str))
                print(request)
                processedLogs = self.process_logs(request)
                getAPIKeys.append(ET.fromstring(logline).tag)
            elif logline.startswith("{"):
                json_log = json.loads(logline)
                processedLogs = self.process_logs(json_log)
                getAPIKeys.extend(json_log.keys())
            else:
                processedLogs = self.process_logs(aesdk_requests)
                getAPIKeys.append("PED REQUEST")
        return processedLogs, getAPIKeys

    def process_logs(self, logs):
        """Process logs and generate human-readable text."""
        output_map = {
            "TimedOutResponse": lambda res: self.logTextification.append("The Timeout response"),
            "GetCardBINRequest": lambda req: self.handle_get_card_bin_request(req),
            "GetUserInputRequest": lambda req: self.handle_get_user_input_request(req),
            "GetUserInputResponse": lambda res: self.handle_get_user_input_response(res),
            "ShowScreenRequest": lambda _: self.logTextification.append("The show screen request is initiated."),
            "ByPassScreenRequest": lambda req: self.handle_by_pass_screen_request(req),
            "ByPassScreenResponse": lambda res: self.handle_by_pass_screen_response(res),
            "TransRequest": lambda req: self.handle_trans_request(req),
            "TransResponse": lambda res: self.handle_trans_response(res),
            "CloseTransactionResponse": lambda res: self.handle_close_transaction_response(res),
            "CloseTransactionRequest": lambda _: self.logTextification.append("Close transaction request is initiated."),
            "GetCardBINResponse": lambda res: self.handle_get_card_bin_response(res),
            "ShowScreenResponse": lambda res: self.handle_show_screen_response(res),
            "ShowListRequest": lambda _: self.logTextification.append("The show list request is initiated."),
            "ShowListResponse": lambda res: self.handle_ShowListResponse(res),
            "EmailOptionRequest": lambda _: self.logTextification.append("The email option request is initiated."),
            "EmailOptionResponse": lambda res: self.handle_EmailOptionResponse(res),
        }

        for log_type, handler in output_map.items():
            if log_type in logs:
                handler(logs[log_type])
                return self.logTextification

        self.logTextification.append("PED REQUEST")
        return self.logTextification

    def handle_get_card_bin_request(self, req):
        Lookupflag = req.get("LookUpFlag")
        AllowKeyedEntry = req.get("AllowKeyedEntry")
        output = f"Get card bin Request is of Lookupflag {Lookupflag if Lookupflag else 'without Lookupflag'}. " \
                 f"{'Must be keyed entry is performed.' if AllowKeyedEntry == 'Y' else 'Must have been inserted/swiped/tapped the card.'}"
        self.logTextification.append(output)

    def handle_EmailOptionResponse(self, res):
        EmailOptionResponseCode = res.get("EmailOptionResponseCode", '')
        ResponseText = res.get("ResponseText", '')
        output = f"The email option response is {ResponseText}. and {EmailOptionResponseCode} button pressed."
        self.logTextification.append(output)

    def handle_ShowListResponse(self, res):
        ResponseText = res.get("ResponseText")
        output = f"The show list response is {ResponseText}."
        self.logTextification.append(output)

    def handle_get_user_input_request(self, req):
        Type = req.get("Type", None)
        output = f"Get user input Request is of type {Type if Type else 'has no type specified'}."
        self.logTextification.append(output)

    def handle_get_user_input_response(self, res):
        ButtonSelection = res.get("ButtonSelection", None)
        inputData = res.get("InputData", None)
        Value = "green" if ButtonSelection == "01" else "red" if ButtonSelection == "02" else ""
        output = f"{'User Entered value ' + inputData + ' and length of text is ' + str(len(inputData)) if inputData else ''}" \
                 f"{' User Pressed ' + Value + ' button' if ButtonSelection else ''}"
        self.logTextification.append(output)

    def handle_by_pass_screen_request(self, req):
        ByPassOptions = req.get("ByPassOptions", None)
        output = f"The bypass request is initiated with ByPASS Option {ByPassOptions if ByPassOptions else ''}"
        self.logTextification.append(output)

    def handle_by_pass_screen_response(self, res):
        ResponseText = res.get("ResponseText", None)
        output = f"The bypass response is {ResponseText if ResponseText else ''}"
        self.logTextification.append(output)

    def handle_trans_request(self, req):
        CardToken = req.get("CardToken", None)
        output = f"The cardtoken in transaction request is {CardToken if CardToken else ''}"
        self.logTextification.append(output)

    def handle_trans_response(self, res):
        ResponseText = res.get("ResponseText", None)
        output = f"The response for transaction request is {ResponseText if ResponseText else ''}"
        self.logTextification.append(output)

    def handle_close_transaction_response(self, res):
        responseText = res.get("ResponseText", "")
        output = "Close transaction response got " + responseText
        self.logTextification.append(output)

    def handle_get_card_bin_response(self, res):
        CardType = res.get("CardType")
        ResponseText = res.get("ResponseText")
        ResponseCode = res.get("ResponseCode")
        CardEntryMode = res.get("CardEntryMode", "")
        output = f"{'The get card bin is approved.' if ResponseCode.startswith('0') else 'The get card bin is declined.'}" \
                 f"{' ResponseText: ' + ResponseText if ResponseText else ''}" \
                 f"{' Card entry mode is ' + self.interpret_card_entry_mode(CardEntryMode)}" \
                 f"{' Card type: ' + CardType if CardType else ''}"
        self.logTextification.append(output)

    def handle_show_screen_response(self, res):
        ButtonSelection = res.get("ButtonSelection", "")
        ButtonReturn = res.get("ButtonReturn", "")
        ResponseCode = res.get("ResponseCode", "")
        ResponseText = res.get("ResponseText", "")
        output = f"{'The Show Screen Response is approved.' if ResponseCode.startswith('0') else 'The Show Screen Response is declined.'}" \
                 f"{' ResponseText: ' + ResponseText if ResponseText else ''}" \
                 f"{self.interpret_show_screen_buttons(ButtonSelection, ButtonReturn)}"
        self.logTextification.append(output)

    def interpret_card_entry_mode(self, mode):
        modes = {
            "I": "inserted",
            "S": "swiped",
            "T": "tapped",
            "K": "keyed",
            "F": "fallback"
        }
        return modes.get(mode, "unknown")

    def interpret_show_screen_buttons(self, ButtonSelection, ButtonReturn):
        if ButtonSelection == "01" or ButtonReturn == "01":
            return " On show screen request user pressed yes button. "
        elif ButtonSelection == "02" or ButtonReturn == "02":
            return " On show screen request user pressed no button. "
        elif ButtonSelection == "-1" or ButtonReturn == "-1":
            return " Showscreen request is timeout on pinpad screen. "
        return " "