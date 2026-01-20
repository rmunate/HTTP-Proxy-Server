from typing import Any
from pydantic import BaseModel, Field, field_validator

class HTTPRequestPayload(BaseModel):
    """
    Validate and store HTTP request payload data.

    Validates that incoming HTTP request payloads conform to the expected
    format and contain the required data.

    Parameters
    ----------
    url : str
        Destination URL for the HTTP request.
    method : str, default="GET"
        HTTP method (GET, POST, PUT, DELETE, etc.).
    params : dict[str, Any] | None, default=None
        Query string parameters for the URL.
    data : dict[str, Any] | str | None, default=None
        Form data for the request body.
    json_data : dict[str, Any] | None, default=None
        JSON data for the request body.
    headers : dict[str, str] | None, default=None
        Additional HTTP headers.
    cookies : dict[str, str] | None, default=None
        Cookies to send with the request.
    timeout : int, default=30
        Timeout in seconds (1-300).
    allow_redirects : bool, default=True
        Whether to allow automatic redirects.

    Returns
    -------
    HTTPRequestPayload
        An instance containing validated HTTP request data.
    """

    url: str = Field(..., description="Destination URL for the request")

    method: str = Field(
        default="GET", description="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )

    params: dict[str, Any] | None = Field(
        default=None, description="Query string parameters"
    )

    data: dict[str, Any] | str | None = Field(
        default=None, description="Form data for the request body"
    )

    json_data: dict[str, Any] | None = Field(
        default=None, description="JSON data for the request body"
    )

    headers: dict[str, str] | None = Field(
        default=None, description="Additional HTTP headers"
    )

    cookies: dict[str, dict] | None = Field(
        default=None, description="Cookies to send with the request"
    )

    timeout: int = Field(
        default=30, ge=1, le=300, description="Timeout in seconds (1-300)"
    )

    allow_redirects: bool = Field(
        default=True, description="Allow automatic redirects"
    )

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """
        Validate that the HTTP method is allowed.

        Parameters
        ----------
        v : str
            HTTP method to validate.

        Returns
        -------
        str
            The validated HTTP method in uppercase.

        Raises
        ------
        ValueError
            If the HTTP method is not allowed.
        """
        allowed_methods = [
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'
        ]
        if v.upper() not in allowed_methods:
            error_msg = (
                f'Invalid HTTP method. Must be one of: {", ".join(allowed_methods)}'
            )
            raise ValueError(error_msg)
        return v.upper()

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Validate that the URL starts with http:// or https://.

        Parameters
        ----------
        v : str
            URL to validate.

        Returns
        -------
        str
            The validated URL.

        Raises
        ------
        ValueError
            If the URL does not start with http:// or https://.
        """
        if not v.startswith(('http://', 'https://')):
            error_msg = 'URL must start with http:// or https://'
            raise ValueError(error_msg)
        return v

    @field_validator('cookies')
    @classmethod
    def validate_cookies( # NOSONAR
        cls, v: dict[str, dict] | None
    ) -> dict[str, dict] | None:
        """
        Validate cookies are in the correct format.

        Parameters
        ----------
        cls : type[HTTPRequestPayload]
            The class on which this method is called.
        v : dict[str, dict] | None
            Cookies to validate. Each cookie must be a dict with keys:
            'value', 'domain', 'path', and all values must be strings.

        Returns
        -------
        dict[str, dict] | None
            The validated cookies if valid, otherwise raises ValueError.

        Raises
        ------
        ValueError
            If cookies are not in the correct format.
        """
        # Check if cookies are provided and validate their structure
        if v is not None:
            for key, value in v.items():
                if not isinstance(value, dict):
                    error_msg = (
                        f'Cookie value for "{key}" must be a dictionary'
                    )
                    raise ValueError(error_msg)
                required_keys = {'value', 'domain', 'path'}
                if set(value.keys()) != required_keys:
                    error_msg = (
                        f'Cookie "{key}" must have keys: '
                        f'{", ".join(required_keys)}'
                    )
                    raise ValueError(error_msg)
                for k in required_keys:
                    if not isinstance(value[k], str):
                        error_msg = (
                            f'Cookie "{key}" field "{k}" must be a string'
                        )
                        raise ValueError(error_msg)
        return v
