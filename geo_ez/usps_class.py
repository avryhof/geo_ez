import datetime
import logging
import os
import pprint
from collections import OrderedDict

import requests
import xmltodict
from future.standard_library import install_aliases

from geo_ez.data_functions import snake_to_camel, http_build_query, clean_api_dict

install_aliases()

logger = logging.getLogger(__name__)


class USPS:
    is_debug = False
    is_logging = False

    today = None

    usps_id = None

    endpoint = "https://secure.shippingapis.com/ShippingAPI.dll"

    def __init__(self, **kwargs):
        self.usps_id = kwargs.get("id", os.environ.get("USPS_ID", False))

        self.is_debug = kwargs.get("debug", os.environ.get("FED_DEBUG", False)) in ["True", True]
        self.is_logging = kwargs.get("logging", os.environ.get("FED_LOGGING", False)) in ["True", True]

        self.today = datetime.datetime.now()

    def debug_msg(self, message, **kwargs):
        pretty = kwargs.get("pretty", False)

        if pretty:
            message = pprint.pformat(message, indent=4)

        if self.is_debug:
            print(message)

        if self.is_logging:
            logger.info(message)

    def usps_call(self, **kwargs):
        api = kwargs.get("api", False)
        data = kwargs.get("data", False)

        resp = {}

        if self.usps_id and api and data:
            api_resp_var = kwargs.get("resp_variable", "%s_response" % snake_to_camel(api, reverse=True))
            self.debug_msg(api_resp_var)

            xml = xmltodict.unparse(OrderedDict(data), full_document=False)
            self.debug_msg(xml)

            endpoint = kwargs.get("endpoint", self.endpoint)

            params = dict(API=api, XML=xml)

            request_url = "%s?%s" % (endpoint, http_build_query(params))

            ret = requests.get(request_url, verify=True)
            self.debug_msg(ret.text)

            # Convert the returned XML to a dict, clean the returned data, and convert all keys to snake case.
            ret_dict = clean_api_dict(xmltodict.parse(ret.text))
            self.debug_msg(ret_dict, pretty=True)

            resp = ret_dict.get(api_resp_var)

        return resp

    def address(self, **kwargs):
        """
        Uses the USPS Address validation API to return a valid address

        NOTE: The USPS API expects Address2 to be the street address, and Address1 to be the suite/apt #,
              so in the code below, we swap the parameters when they are being fed to the API, and when they are
              returned from the API.

        :param kwargs:
            address1, address2, city, state, zip_code, plus_four

        :return:
            A Dict with a valid address:
                {
                    'address1': '',
                    'address2': '',
                    'city': '',
                    'state': 'XX',
                    'zip_code': 'XXXXX',
                    'plus_four': 'XXXX'
                }
        """
        valid_address = None

        address_dict = OrderedDict()
        address_dict["Address1"] = kwargs.get("address1", "")
        address_dict["Address2"] = kwargs.get("address2", "")
        address_dict["City"] = kwargs.get("city", "")
        address_dict["State"] = kwargs.get("state", "")
        address_dict["Zip5"] = kwargs.get("zip_code", "")
        address_dict["Zip4"] = kwargs.get("plus_four", "")

        address_validate_request = OrderedDict()
        address_validate_request["@USERID"] = self.usps_id
        address_validate_request["Address"] = address_dict

        address_validate_dict = {"AddressValidateRequest": address_validate_request}

        resp = self.usps_call(api="Verify", data=address_validate_dict, resp_variable="address_validate_response")

        if "address" in resp:
            ret_address = resp.get("address")
            valid_address = {
                "address1": ret_address.get("address2"),
                "address2": ret_address.get("address1"),
                "city": ret_address.get("city"),
                "state": ret_address.get("state"),
                "zip_code": ret_address.get("zip5"),
                "plus_four": ret_address.get("zip4"),
            }

        return valid_address

    def get_zipcode(self, **kwargs):
        """
        Uses the USPS Zip Code Lookup API to determine a Zip Code based on a partial address.
        :param kwargs:
            address1, address2, city, state, zip_code, plus_four

        :return:
            A Dict with a valid address:
                {
                    'address1': '',
                    'address2': '',
                    'city': '',
                    'state': 'XX',
                    'zip_code': 'XXXXX',
                    'plus_four': 'XXXX'
                }
        """
        valid_address = {"address1": "", "address2": "", "city": "", "state": "XX"}

        address_dict = OrderedDict()
        address_dict["Address1"] = kwargs.get("address2", "")
        address_dict["Address2"] = kwargs.get("address1", "")
        address_dict["City"] = kwargs.get("city", "")
        address_dict["State"] = kwargs.get("state", "")

        address_validate_request = OrderedDict()
        address_validate_request["@USERID"] = self.usps_id
        address_validate_request["Address"] = address_dict

        address_validate_dict = {"ZipCodeLookupRequest": address_validate_request}

        resp = self.usps_call(api="ZipCodeLookup", data=address_validate_dict)

        if "address" in resp:
            ret_address = resp.get("address")
            valid_address = {
                "address1": ret_address.get("address2"),
                "address2": ret_address.get("address1"),
                "city": ret_address.get("city"),
                "state": ret_address.get("state"),
                "zip_code": ret_address.get("zip5"),
                "plus_four": ret_address.get("zip4"),
            }

        return valid_address

    def track(self, tracking_number, **kwargs):
        detailed_response = kwargs.get("details", False)

        if detailed_response:
            req_key = "TrackFieldRequest"

        else:
            req_key = "TrackRequest"

        tracking_dict = OrderedDict(
            {req_key: OrderedDict({"@USERID": self.usps_id, "TrackID": OrderedDict({"@ID": tracking_number})})}
        )

        resp = self.usps_call(api="TrackV2", data=tracking_dict, resp_variable="track_response")

        tracking_info = resp.get("track_info")

        tracking_data = {
            "tracking_number": tracking_info.get("@id"),
            "details": tracking_info.get("track_detail"),
            "summary": tracking_info.get("track_summary"),
        }

        return tracking_data

    def zip_to_city_state(self, zip_code):
        valid_address = {"city": "", "state": "XX", "zip_code": "XXXXX"}

        zip_code_dict = OrderedDict()
        zip_code_dict["@ID"] = "0"
        zip_code_dict["Zip5"] = zip_code

        city_state_request = OrderedDict()
        city_state_request["@USERID"] = self.usps_id
        city_state_request["ZipCode"] = zip_code_dict

        city_state_dict = {"CityStateLookupRequest": city_state_request}

        resp = self.usps_call(api="CityStateLookup", data=city_state_dict)

        if "zip_code" in resp:
            ret_zip = resp.get("zip_code")
            valid_address = {
                "city": ret_zip.get("city"),
                "state": ret_zip.get("state"),
                "zip_code": ret_zip.get("zip5"),
            }

        return valid_address
