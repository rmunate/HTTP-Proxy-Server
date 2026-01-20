from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    """
    Represent a standard API response.

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
    url : str or None, optional
        Final URL after redirects.
    elapsed : float or None, optional
        Time taken for the request in seconds.
    encoding : str or None, optional
        Response encoding.
    ok : bool, optional
        Indicates if the request was successful.
    history : list[str], optional
        List of redirect URLs.
    content_type : str or None, optional
        Content-Type of the response.
    body : str
        Response body as text.

    Returns
    -------
    APIResponse
        An instance containing the API response data.
    """

    status: str
    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    elapsed: float | None = None
    encoding: str | None = None
    ok: bool = False
    history: list[str] = Field(default_factory=list)
    content_type: str | None = None
    body: str = ""