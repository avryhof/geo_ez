try:
    from urllib.parse import quote  # Python 3+
    from urllib.request import urlretrieve

except ImportError:
    from urllib import quote, urlretrieve  # Python 2.X


def compatible_quote(value, *args, **kwargs):
    return quote(value, *args, **kwargs)


def compatible_urlretrieve(url, *args, **kwargs):
    return urlretrieve(url, *args, **kwargs)


def python3_cmp(a, b):
    return (a > b) - (a < b)
