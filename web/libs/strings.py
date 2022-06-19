import json


default_locale = "en-us"
cached_strings = {}


""" If language changes, set libs.strings.default_locale and run libs.strings.refresh() """


def refresh_locale():
    """ Load default locale """
    global cached_strings
    with open(f"strings/{default_locale}.json") as f:
        cached_strings = json.load(f)


def get_text(key):
    """ Return JSON value """
    return cached_strings[key]


refresh_locale()
