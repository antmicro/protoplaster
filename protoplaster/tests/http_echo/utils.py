import requests


def remote_write(url: str, text: str) -> str:
    """
    Executes on dev1. Sends a POST request with text to the specific URL.
    """
    print(f'remote_write: {url} -> {text}')
    try:
        response = requests.post(url, data=text, timeout=5)
        response.raise_for_status()
        return "Message sent successfully"
    except Exception as e:
        return f"Failed to send message: {e}"


def remote_read(url: str) -> str:
    """
    Executes on dev2. Sends a GET request to the URL to retrieve text.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print(
            f'remote read: {url} -> {response.text} ({response.status_code})')
        return response.text
    except Exception as e:
        return f"Failed to read message: {e}"
