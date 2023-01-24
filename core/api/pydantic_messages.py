from django.utils.translation import gettext as _

msgs = {
    'field required': _('field required'),
    'extra fields not permitted': _('extra fields not permitted'),
    'none is not an allowed value': _('none is not an allowed value'),
    'value is not none': _('value is not none'),
    'value is not None': _('value is not None'),
    'value could not be parsed to a boolean': _(
        'value could not be parsed to a boolean'
    ),
    'byte type expected': _('byte type expected'),
    'value is not a valid dict': _('value is not a valid dict'),
    'value is not a valid email address': _('value is not a valid email address'),
    'invalid or missing URL scheme': _('invalid or missing URL scheme'),
    'URL scheme not permitted': _('URL scheme not permitted'),
    'userinfo required in URL but missing': _('userinfo required in URL but missing'),
    'URL host invalid': _('URL host invalid'),
    'URL host invalid, top level domain required': _(
        'URL host invalid, top level domain required'
    ),
    'URL port invalid, port cannot exceed 65535': _(
        'URL port invalid, port cannot exceed 65535'
    ),
    'URL invalid, extra characters found after valid URL: {}': _(
        'URL invalid, extra characters found after valid URL: {}'
    ),
    '{} is not a valid Enum instance': _('{} is not a valid Enum instance'),
    '{} is not a valid IntEnum instance': _('{} is not a valid IntEnum instance'),
    'value is not a valid integer': _('value is not a valid integer'),
    'value is not a valid float': _('value is not a valid float'),
    'value is not a valid path': _('value is not a valid path'),
    'file or directory at path \"{}\" does not exist': _(
        'file or directory at path \"{}\" does not exist'
    ),
    'path \"{}\" does not point to a file': _('path \"{}\" does not point to a file'),
    'path \"{}\" does not point to a directory': _(
        'path \"{}\" does not point to a directory'
    ),
    'ensure this value contains valid import path or valid callable: {}': _(
        'ensure this value contains valid import path or valid callable: {}'
    ),
    'value is not a valid sequence': _('value is not a valid sequence'),
    'value is not a valid list': _('value is not a valid list'),
    'value is not a valid set': _('value is not a valid set'),
    'value is not a valid frozenset': _('value is not a valid frozenset'),
    'value is not a valid tuple': _('value is not a valid tuple'),
    'wrong tuple length {}': _('wrong tuple length {}'),
    'ensure this value has at least {} items': _(
        'ensure this value has at least {} items'
    ),
    'ensure this value has at most {} items': _(
        'ensure this value has at most {} items'
    ),
    'the list has duplicated items': _('the list has duplicated items'),
    'ensure this value has at least {} characters': _(
        'ensure this value has at least {} characters'
    ),
    'ensure this value has at most {} characters': _(
        'ensure this value has at most {} characters'
    ),
    'str type expected': _('str type expected'),
    'string does not match regex \"{}\"': _('string does not match regex \"{}\"'),
    'ensure this value is greater than {}': _('ensure this value is greater than {}'),
    'ensure this value is greater than or equal to {}': _(
        'ensure this value is greater than or equal to {}'
    ),
    'ensure this value is less than {}': _('ensure this value is less than {}'),
    'ensure this value is less than or equal to {}': _(
        'ensure this value is less than or equal to {}'
    ),
    'ensure this value is a multiple of {}': _('ensure this value is a multiple of {}'),
    'value is not a valid decimal': _('value is not a valid decimal'),
    'ensure that there are no more than {} digits in total': _(
        'ensure that there are no more than {} digits in total'
    ),
    'ensure that there are no more than {} decimal places': _(
        'ensure that there are no more than {} decimal places'
    ),
    'ensure that there are no more than {} digits before the decimal point': _(
        'ensure that there are no more than {} digits before the decimal point'
    ),
    'invalid datetime format': _('invalid datetime format'),
    'invalid date format': _('invalid date format'),
    'date is not in the past': _('date is not in the past'),
    'date is not in the future': _('date is not in the future'),
    'invalid time format': _('invalid time format'),
    'invalid duration format': _('invalid duration format'),
    'value is not a valid hashable': _('value is not a valid hashable'),
    'value is not a valid uuid': _('value is not a valid uuid'),
    'uuid version {} expected': _('uuid version {} expected'),
    'instance of {} expected': _('instance of {} expected'),
    'a class is expected': _('a class is expected'),
    'subclass of {} expected': _('subclass of {} expected'),
    'Invalid JSON': _('Invalid JSON'),
    'JSON object must be str, bytes or bytearray': _(
        'JSON object must be str, bytes or bytearray'
    ),
    'Invalid regular expression': _('Invalid regular expression'),
    'instance of {}, tuple or dict expected': _(
        'instance of {}, tuple or dict expected'
    ),
    '{} is not callable': _('{} is not callable'),
    'value is not a valid IPv4 or IPv6 address': _(
        'value is not a valid IPv4 or IPv6 address'
    ),
    'value is not a valid IPv4 or IPv6 interface': _(
        'value is not a valid IPv4 or IPv6 interface'
    ),
    'value is not a valid IPv4 or IPv6 network': _(
        'value is not a valid IPv4 or IPv6 network'
    ),
    'value is not a valid IPv4 address': _('value is not a valid IPv4 address'),
    'value is not a valid IPv6 address': _('value is not a valid IPv6 address'),
    'value is not a valid IPv4 network': _('value is not a valid IPv4 network'),
    'value is not a valid IPv6 network': _('value is not a valid IPv6 network'),
    'value is not a valid IPv4 interface': _('value is not a valid IPv4 interface'),
    'value is not a valid IPv6 interface': _('value is not a valid IPv6 interface'),
    'value is not a valid color: {}': _('value is not a valid color: {}'),
    'value is not a valid boolean': _('value is not a valid boolean'),
    'card number is not all digits': _('card number is not all digits'),
    'card number is not luhn valid': _('card number is not luhn valid'),
    'Length for a {}': _('Length for a {}'),
    'could not parse value and unit from byte string': _(
        'could not parse value and unit from byte string'
    ),
    'could not interpret byte unit: {}': _('could not interpret byte unit: {}'),
    'Discriminator {} is missing in value': _('Discriminator {} is missing in value'),
    'No match for discriminator {}': _('No match for discriminator {}'),
}
