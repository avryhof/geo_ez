import json

from django.http import HttpResponse

from geo_ez.utility_functions import zip_codes_in_radius


def get_zipcodes_in_radius(request, **kwargs):
    """
    Finds ZipCodes within a radius of the specified Zip Code
    :param request:
    :return:
    """
    response = HttpResponse(content_type='application/json')
    response['Cache-Control'] = 'no-cache'

    response.write(json.dumps(dict(zip_codes=zip_codes_in_radius(**kwargs))))

    return response
