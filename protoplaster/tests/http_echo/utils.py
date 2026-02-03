import requests
import time


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


def remote_read_poll(url: str, timeout: int = 30) -> str:
    """
    Executes on dev2. Polls the URL until a message is received (200 OK) or timeout expires.
    """
    start_time = time.time()
    print(f"remote_read_poll: Polling {url} for {timeout}s...")

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f'remote read success: {response.text}')
                return response.text
        except Exception:
            pass
        time.sleep(0.5)

    return "Timeout: No message received"
