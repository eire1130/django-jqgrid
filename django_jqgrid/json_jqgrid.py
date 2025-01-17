'''
Created on Jan 22, 2012

@author: James
'''
import datetime
from decimal import Decimal

from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.db.models import Model
from django.db.models import ImageField, FileField
from django.db.models.query import QuerySet
from django.utils import simplejson as json
from django.utils.functional import Promise
from django.utils.encoding import force_unicode


def json_encode(data):
    """
    The main issues with django's default json serializer is that properties that
    had been added to an object dynamically are being ignored (and it also has 
    problems with some models).
    """

    def _any(data):
        ret = None
        # Opps, we used to check if it is of type list, but that fails 
        # i.e. in the case of django.newforms.utils.ErrorList, which extends
        # the type "list". Oh man, that was a dumb mistake!
        if isinstance(data, list):
            ret = _list(data)
        # Same as for lists above.
        elif isinstance(data, dict):
            ret = _dict(data)
        elif isinstance(data, Decimal):
            # json.dumps() cant handle Decimal
            ret = str(data)
        elif isinstance(data, QuerySet):
            # Actually its the same as a list ...
            ret = _list(data)
        elif isinstance(data, Model):
            ret = _model(data)
        # here we need to encode the string as unicode (otherwise we get utf-16 in the json-response)
        elif isinstance(data, basestring):
            ret = unicode(data)
        # see http://code.djangoproject.com/ticket/5868
        elif isinstance(data, Promise):
            ret = force_unicode(data)
        elif isinstance(data, datetime.datetime):
            # For dojo.date.stamp we convert the dates to use 'T' as separator instead of space
            # i.e. 2008-01-01T10:10:10 instead of 2008-01-01 10:10:10
            ret = str(data).replace(' ', 'T')
        elif isinstance(data, datetime.date):
            ret = str(data)
        elif isinstance(data, datetime.time):
            ret = "T" + str(data)
        else:
            # always fallback to a string!
            ret = data
        return ret
    
    def _model(data):
        ret = {}
        # If we only have a model, we only want to encode the fields.
        for f in data._meta.fields:
            # special FileField handling (they can't be json serialized)
            if isinstance(f, ImageField) or isinstance(f, FileField):
                ret[f.attname] = unicode(getattr(data, f.attname))
            else:
                ret[f.attname] = _any(getattr(data, f.attname))
        # And additionally encode arbitrary properties that had been added.
        fields = dir(data.__class__) + ret.keys()
        # ignoring _state and delete properties
        add_ons = [k for k in dir(data) if k not in fields and k not in ('delete', '_state',)]
        for k in add_ons:
            ret[k] = _any(getattr(data, k))
        return ret

    def _googleModel(data):
        ret = {}
        ret['id'] = data.key().id()
        for f in data.fields():
            ret[f] = _any(getattr(data, f))
        return ret

    def _list(data):
        ret = []
        for v in data:
            ret.append(_any(v))
        return ret
    
    def _dict(data):
        ret = {}
        for k,v in data.items():
            ret[k] = _any(v)
        return ret
    
    ret = _any(data)
    return json.dumps(ret, cls=DateTimeAwareJSONEncoder)


if __name__ == '__main__':
    pass