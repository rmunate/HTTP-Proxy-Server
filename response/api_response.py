from typing import Any
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    """
    Represent a standard API response object.

    Parameters
    ----------
    status : str
        HTTP status reason phrase.
    status_code : int
        HTTP status code.
    headers : dict[str, str], optional
        Response headers.
    cookies : dict[str, str], optional
        Response cookies.
    url : str | None, optional
        Final URL after redirects.
    elapsed : float | None, optional
        Time taken for the request in seconds.
    encoding : str | None, optional
        Response encoding.
    ok : bool, optional
        Indicates if the request was successful.
    history : list[str], optional
        List of redirect URLs.
    content_type : str | None, optional
        Content-Type of the response.
    body : str
        Response body as text.

    Returns
    -------
    APIResponse
        An instance containing the API response data.
    """

    # HTTP status reason phrase.
    status: str

    # HTTP status code.
    status_code: int

    # Response headers.
    headers: dict[str, str] = Field(
        default_factory=dict
    )

    # Response cookies.
    cookies: dict[str, Any] = Field(
        default_factory=dict
    )

    # Final URL after redirects.
    url: str | None = None

    # Time taken for the request in seconds.
    elapsed: float | None = None

    # Response encoding.
    encoding: str | None = None

    # Indicates if the request was successful
    ok: bool = False

    # List of redirect URLs
    history: list[str] = Field(
        default_factory=list
    )

    # Content-Type of the response
    content_type: str | None = None

    # Response body as text.
    body: str = ""
