import urllib.parse

def is_github_url(url: str = None):

    """Checks that the given url is a secure GitHub URL"""

    if not url:
        return False

    # Parse the URL using the urlparse function
    parsed_url = urllib.parse.urlparse(url)

    # Check if the scheme is https and the hostname is github.com
    return parsed_url.scheme == "https" and parsed_url.hostname == "github.com"
