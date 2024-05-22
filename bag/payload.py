# noqa
import requests  # pip install requests


def retrieve_payload(source: str) -> bytes:
    """Given a URL or a local filesystem path, return its contents as bytes."""
    if source.startswith(("http://", "https://")):
        response = requests.get(source)
        assert response.status_code == 200, f"Unable to retrieve: {source}"
        assert isinstance(response.content, bytes), f"Content not bytes: {source}"
        return response.content
    else:
        with open(source, mode="rb") as stream:
            return stream.read()
