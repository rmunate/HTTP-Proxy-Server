from pydantic import Field
from server import HTTPRequestPayload

class LoginPayload(HTTPRequestPayload):
    """
    Define a payload model for login requests.

    Inherits from HTTPRequestPayload and sets the default HTTP method to POST.
    Additional login-specific validation can be added here.

    Parameters
    ----------
    method : str, optional
        HTTP method for login (default is "POST").

    Returns
    -------
    None
        This class is used for data validation and does not return a value.
    """

    method: str = Field(
        default="POST",
        description="HTTP method for login (usually POST)"
    )