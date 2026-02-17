class APIError(Exception):
    """ Base class fro all API related """

    http_code : int = 404

    def __init__(self, detail, extra = None):
        self.detail = detail
        self.extra = extra or {}
        super().__init__(detail)

    def as_response(self):
        resp = {
            "detail" : self.detail
        }
        if self.extra:
            resp["extra"] = self.extra

        return resp
    
# Response code
class HTTPUnauthorized(APIError):
    http_code = 401

class HTTPConflict(APIError):
    http_code = 409

class HTTPNotFound(APIError):
    http_code = 404

class HTTPBadRequest(APIError):
    http_code = 400

class HTTPInternalServer(APIError):
    http_code = 500
