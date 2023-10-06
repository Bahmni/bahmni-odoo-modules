import logging
import datetime
import json
import ast
#from urllib.parse import unquote

import werkzeug.wrappers

_logger = logging.getLogger(__name__)


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data = {"count": len(data), "data": data}
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        headers=[("Cache-Control", "no-store"),('Access-Control-Allow-Headers', 'Origin, Content-Type, X-Auth-Token, charset'),('Access-Control-Allow-Methods','POST, GET, OPTIONS, DELETE, PUT'), ('Access-Control-Allow-Origin', '*'), ("Pragma", "no-cache")],
        response=json.dumps(data, default=default),
    )


def invalid_response(typ, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    # return json.dumps({})
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
headers=[("Cache-Control", "no-store"),('Access-Control-Allow-Headers', 'Origin, Content-Type, X-Auth-Token, charset'),('Access-Control-Allow-Methods','POST, GET, OPTIONS, DELETE, PUT'), ('Access-Control-Allow-Origin', '*'), ("Pragma", "no-cache")],
        response=json.dumps(
            {
                "status": typ,
                "message": str(message)
                if str(message)
                else "wrong arguments (missing validation)",
            },
            default=datetime.datetime.isoformat,
        ),
    )


def extract_arguments(payloads, offset=0, limit=0, order=None):
    """Parse additional data  sent along request."""
    #payloads=unquote(unquote(payloads))
    fields, domain, payload = [], [], {}

    if payloads.get("domain", None):
        domain = ast.literal_eval(payloads.get("domain"))
    if payloads.get("fields"):
        fields += payloads.get("fields")
    if payloads.get("offset"):
        offset = int(payloads["offset"])
    if payloads.get("limit"):
        limit = int(payloads.get("limit"))
    if payloads.get("order"):
        order = payloads.get("order")
    return [domain, fields, offset, limit, order]
