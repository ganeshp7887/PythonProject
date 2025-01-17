import json
from config import config
import pandas as pd
import xmltodict
from lxml import etree


class Excel_Operations :

    @staticmethod
    def open_excel_file() :
        try :
            open(config.xls_file_path())
            return True
        except (BaseException, FileNotFoundError) as e :
            return False

    @staticmethod
    def read_sheet(carddatasource) :
        of = Excel_Operations.open_excel_file()
        if not of :
            try :
                pd.read_excel(config.xls_file_path(), sheet_name=carddatasource)
            except (KeyError, FileNotFoundError, BaseException) as e :
                return False
            else :
                return True

    @staticmethod
    def read_from_xls(carddatasource) :
        workbook = pd.read_excel(config.xls_file_path(), sheet_name=carddatasource)
        workbook.fillna("", inplace=True)
        return workbook

    @staticmethod
    def Read_Outdoor_File(requestFormat, filename) :
        if requestFormat:
            try :
                aa = etree.parse(rf"{config.Full_Outdoor_file_path()+'XML'}\{filename}", etree.XMLParser(remove_blank_text=True))
                xml_str = etree.tostring(aa, pretty_print=True, encoding='unicode')
                return xml_str
            except :
                return False
        else:
            try :
                return open(rf"{config.Full_Outdoor_file_path()+'JSON'}\{filename}")
            except:
                return False

    @staticmethod
    def readFile(requestFormat, filename):
        file_path = rf"{config.Full_Indoor_file_path()}{filename}"
        aa = etree.parse(file_path, etree.XMLParser(remove_blank_text=True))
        request = etree.tostring(aa, pretty_print=True, encoding='unicode')
        if not requestFormat :
            request = xmltodict.parse(request)
        return request

    @staticmethod
    def Read_Indoor_File(requestFormat, filename) :
        if requestFormat:
            try :
                aa = etree.parse(rf"{config.Full_Indoor_file_path()+'XML'}\{filename}", etree.XMLParser(remove_blank_text=True))
                xml_str = etree.tostring(aa, pretty_print=True, encoding='unicode')
                return xml_str
            except :
                return False
        else:
            try:
                return open(rf"{config.Full_Indoor_file_path()+'JSON'}\{filename}")
            except:
                return False

    @staticmethod
    def Read_indoor_Transrequest(format, filename) :
        if format.upper() == "XML" :
            try :
                parser = etree.XMLParser(remove_blank_text=True)
                x = etree.parse(config.Indoor_xml_request_path() + filename, parser)
                return x
            except :
                return False
        if format.upper() == "JSON" :
            try :
                x = open(config.Indoor_json_request_path() + filename)
                return x
            except :
                return False

    @staticmethod
    def Read_outdoor_Transrequest(format, filename) :
        if format.upper() == "XML" :
            try :
                parser = etree.XMLParser(remove_blank_text=True)
                x = etree.parse(config.Outdoor_xml_request_path() + filename, parser)
                return x
            except :
                return False
        if format.upper() == "JSON" :
            try :
                x = open(config.Outdoor_json_request_path() + filename)
                return x
            except :
                return False

    @staticmethod
    def parseXmlToJson(xml) :
        xpars = xmltodict.parse(xml)
        data = json.dumps(xpars)
        return data

    @staticmethod
    def ConvertRequest(req, res, isXML=True) :
        """Convert XML or JSON request and response to dictionaries."""
        request, response = "", ""
        try :
            if isXML :
                request = xmltodict.parse(etree.tostring(etree.fromstring(req), encoding=str))
                response = xmltodict.parse(etree.tostring(etree.fromstring(res), encoding=str))
            else :
                request = json.loads(req)
                response = json.loads(res)
        except Exception as e :
            print(f"Error converting request/response: {e}")
        return request, response
