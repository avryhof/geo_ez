import datetime
import json
import logging
import os
import pprint

import requests
from future.standard_library import install_aliases

from geo_ez.data_functions import convert_keys

install_aliases()

logger = logging.getLogger(__name__)


class USCensus:
    is_debug = False
    is_logging = False

    today = None

    endpoint = "https://geocoding.geo.census.gov/geocoder"

    def __init__(self, **kwargs):
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

    def geocode(self, **kwargs):
        return_address = None

        """
        - locations (to get just geocoding response)
        - geographies (to get geocoding response as well as geoLookup)
        """
        returntype = kwargs.get("returntype", "locations")

        # onelineaddress OR address OR coordinates
        searchtype = kwargs.get("searchtype", "address")

        """
         A numerical ID or name that references what version of the locator should be searched.
         - This generally corresponds to MTDB data which is benchmarked twice yearly.
         - A full list of options can be accessed at https://geocoding.geo.census.gov/geocoder/benchmarks.
         - The general format of the name is DatasetType_SpatialBenchmark.
         - The valid values for these include:
            - DatasetType
                - Public_AR
            - SpatialBenchmark
                - Current
                - ACS2018
                - Census2010

        So a resulting benchmark name could be 
            - Public_AR_Current
            - Public_AR_Census2010
            
        Over time, there will always be a 'Current' benchmark.
        It will change as the underlying dataset changes.
        """
        benchmark = kwargs.get("benchmark", "Public_AR_Current")

        """
        A numerical ID or name that references what vintage of geography is desired for the geoLookup. 
        (only needed when returntype = geographies)
        
        A full list of options for a given benchmark can be accessed at 
        https://geocoding.geo.census.gov/geocoder/vintages?benchmark=benchmarkId. 
        
        The general format of the name is GeographyVintage_SpatialBenchmark.
        - The SpatialBenchmark variable should always match the same named variable in what was chosen for 
          the benchmark parameter.
        - The GeographyVintage can be Current, ACS2018, etc.
        - So a resulting vintage name could be 'ACS2018_Current', 'Current_Census2010', etc.
        - Over time, there will always be a 'Current' vintage.
          It will change as the underlying dataset changes.
        """
        vintage = kwargs.get("vintage", "Current_Current")

        query = kwargs.get("query", False)

        if isinstance(query, dict):
            request_url_base = "%s/%s/%s" % (self.endpoint, returntype, searchtype)

            param_dict = dict(benchmark=benchmark, format="json")

            if returntype == "geographies":
                param_dict.update(dict(vintage=vintage))

            if searchtype == "onelineaddress":
                param_dict.update(dict(address=query))

            if searchtype == "coordinates":
                param_dict.update(dict(x=query.get("longitude"), y=query.get("latitude")))

            if searchtype == "address":
                param_dict.update(
                    dict(
                        street=query.get("address1"),
                        city=query.get("city"),
                        state=query.get("state"),
                        zip=query.get("zip_code"),
                    )
                )

            resp = requests.get(request_url_base, params=param_dict)

            if resp.status_code == 200:
                result = json.loads(resp.text).get("result")

                if isinstance(result, dict):
                    address_matches = result.get("addressMatches")
                    if len(address_matches) > 0:
                        address_match = address_matches[0]

                        return_address = convert_keys(address_match.get("addressComponents"))
                        return_address["latitude"] = address_match.get("coordinates").get("y")
                        return_address["longitude"] = address_match.get("coordinates").get("x")

        return return_address
