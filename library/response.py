import attr

@attr.s
class Response(object):

    data = attr.ib(default=None)
    message = attr.ib(default='Operation not built yet.', validator=attr.validators.optional(attr.validators.instance_of(str)))
    error = attr.ib(default=None)
    authorized = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(str)))
    requestId = attr.ib(default=None)