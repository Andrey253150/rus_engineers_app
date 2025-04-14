from marshmallow import ValidationError

from . import api_v1_bp


@api_v1_bp.errorhandler(ValidationError)
def validation_error(e):
    return {"error": e.args[0]}, 400
