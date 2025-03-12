class InvalidCSRFToken(Exception):
    """
    Raised when a CSRF token is invalid.
    """

    pass


class MissingCSRFToken(Exception):
    """
    Raised when a CSRF token is not found in redis for the user.
    """

    pass


def generate_csrf_token(user_id: int):
    """
    Generates a new CSRF token for the specified user and stores it in redis under `csrf:{user.id}`
    The token should be generated upon log in persists for the duration of the login session.
    """
    import secrets

    from app.lib.redis import session

    token = secrets.token_hex()
    csrf_key = f"csrf:{user_id}"
    session.set(csrf_key, token)


def get_csrf_token() -> str:
    """
    Get the generated CSRF token for the current user from redis.
    If no token is found then a `MissingCSRFToken` exception is raised.
    """

    from app.controllers.user.util import get_user
    from app.lib.redis import session

    user = get_user()
    csrf_key = f"csrf:{user.id}"

    token = session.get(csrf_key)
    if not token:
        raise MissingCSRFToken("No CSRF token generated")

    return token.decode("utf-8")


def validate_csrf_token(token: str):
    """
    Validate a provided CSRF token against the one stored in redis for this user.
    If invalid an `InvalidCSRFToken` exception is raised.
    """
    from app.controllers.user.util import get_user
    from app.lib.redis import session

    user = get_user()
    expected_token = session.get(f"csrf:{user.id}")

    if not expected_token:
        raise InvalidCSRFToken("Invalid CSRF token")

    if expected_token.decode("utf-8") != token:
        raise InvalidCSRFToken("Invalid CSRF token")


def enable_csrf_protection(app):
    """
    Enables CSRF token protection by checking all form submissions for a CSRF token
    and validating it against the one stored in redis.

    If the form does not contain a CSRF token then no checks are done, so it is important
    that any route we want to protect with CSRF tokens has a CSRF token in the form.

    This can be done by adding the following to the template:
    ```html
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
    ```
    """

    from werkzeug.datastructures import ImmutableDict

    from app.lib.util.security import validate_csrf_token

    @app.before_request
    def validate():
        from flask import request

        routes_without_csrf = [
            "/login",
            "/logout",
            "/register",
        ]

        if request.path in routes_without_csrf:
            return

        # All forms other than the ones listed above should have a CSRF token
        if request.form:
            csrf_token = request.form.get("csrf_token")
            if not csrf_token:
                raise MissingCSRFToken("No CSRF token provided")

            validate_csrf_token(csrf_token)
            form_data = request.form.to_dict()
            form_data.pop("csrf_token")
            request.form = ImmutableDict(form_data)  # type:ignore
