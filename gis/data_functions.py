import json
import re
from collections import OrderedDict

import bleach
from future.backports.urllib.parse import quote


def clean_api_dict(input_value):
    if isinstance(input_value, OrderedDict):
        input_value = to_dict(input_value)

    return convert_keys(clean_api_results(input_value))


def clean_api_results(api_result, **kwargs):
    """
    This function will accept, a list, dictionary, or string.
    If a list or dictionary is provided, it will recursively traverse through it, and run bleach on all string values.
    If a string is provided, it will bleach that string.
    Any other data type is simply returned as-is.

    :param input_dict:
    :return:
    """
    retn = None

    if isinstance(api_result, str):

        retn = bleach.clean(api_result)

    elif isinstance(api_result, dict):
        retn = {}

        for k, v in api_result.items():

            if isinstance(v, str):
                retn[k] = bleach.clean(v)

            else:
                retn[k] = clean_api_results(v)

    elif isinstance(api_result, list):
        retn = []

        for list_item in api_result:
            if isinstance(list_item, str):

                retn.append(bleach.clean(list_item))

            elif isinstance(list_item, dict) or isinstance(list_item, list):

                retn.append(clean_api_results(list_item))

            else:
                retn.append(list_item)

    else:
        retn = api_result

    return retn


def convert_keys(input_value):
    """
    Convert all of the keys in a dict recursively from CamelCase to snake_case.
    Also strips leading and trailing whitespace from string values.
    :param input_value:
    :return:
    """
    retn = None

    if isinstance(input_value, list):
        retn = []
        for list_item in input_value:
            if isinstance(list_item, (dict, list)):
                retn.append(convert_keys(list_item))
            else:
                if isinstance(list_item, str):
                    retn.append(list_item.strip())

                else:
                    retn.append(list_item)

    elif isinstance(input_value, dict):
        retn = dict()
        for k, v in input_value.items():
            new_key_s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", k)
            new_key = re.sub("([a-z0-9])([A-Z])", r"\1_\2", new_key_s).lower()
            if isinstance(v, (dict, list)):
                retn[new_key] = convert_keys(v)

            else:
                if isinstance(v, str):
                    retn[new_key] = v.strip()
                else:
                    retn[new_key] = v

    return retn


def filter_query_characters(value):
    # Convert to a string, and filter anything that has no business being in a URL

    return quote(str(value))


def http_build_query(query_dict):
    """
    Build HTTP Query parameters without urlencoding them further.
    :param query_dict:
    :return:
    """
    query_vals = []
    for key, val in query_dict.items():
        query_vals.append("%s=%s" % (filter_query_characters(key), filter_query_characters(val)))

    return "&".join(query_vals)

def snake_to_camel(value, **kwargs):
    """
    Converts a snake_case key name to a camelCase key name, or vice versa.
    :param value: A string that you want to convert to another string type.
    :param kwargs:
        reverse - Convert from camelCase to snake_case
    :return: a converted string
    """
    do_reverse = kwargs.get("reverse", False)

    parts_ex = "([A-Z])" if do_reverse else "(_[A-Za-z])"
    parts = re.findall(parts_ex, value)

    for part in parts:
        if do_reverse:
            value = value.replace(part, "_%s" % part.lower())

            if value[0] == "_":
                value = value[1:]

        else:
            value = value.replace(part, part.upper().replace("_", ""))

    return value


def to_dict(input_ordered_dict):
    return json.loads(json.dumps(input_ordered_dict))