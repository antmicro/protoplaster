import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from protoplaster.tools.tools import trigger_on_remote
from protoplaster.conf.module import ModuleName, BaseTest
from protoplaster.tests.http_echo.utils import remote_write, remote_read, remote_read_poll
from protoplaster.conf.consts import SERVE_IP


class SimpleEchoHandler(BaseHTTPRequestHandler):
    """
    A simple handler that stores a POSTed message and returns it on GET.
    """
    shared_message = None

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        SimpleEchoHandler.shared_message = post_data

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Received")

    def do_GET(self):
        if SimpleEchoHandler.shared_message:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(SimpleEchoHandler.shared_message.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"No message set")


def start_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), SimpleEchoHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server


@ModuleName("http_echo")
class TestEcho(BaseTest):

    def setup_class(self):
        assert hasattr(self, "dev1"), "dev1 parameter required in yaml"
        assert hasattr(self, "dev2"), "dev2 parameter required in yaml"
        self.test_string = getattr(self, "test_string", "Hello World!")
        self.port = getattr(self, "port", 8899)

    def test_echo_multinode(self):
        """
        Orchestration test:
        1. Main PC starts HTTP server.
        2. dev1 connects to Main PC and POSTs "Hello world".
        3. dev2 connects to Main PC and GETs the message.
        4. Main PC verifies the message matches.
        """

        SimpleEchoHandler.shared_message = None
        server = start_server(self.port)
        target_url = f"http://{SERVE_IP}:{self.port}"
        print(f"Main PC Server running at {target_url}")

        try:
            # Command `dev1` to write the message
            print(f"[{self.dev1}] Writing '{self.test_string}' to Main PC...")
            write_result = trigger_on_remote(self.dev1, remote_write,
                                             [target_url, self.test_string])
            print(f"[{self.dev1}] Result: {write_result}")

            # Verify `dev1` successfully sent it
            assert "successfully" in str(
                write_result), f"dev1 failed to write to {target_url}"

            # Command `dev2` to read the message
            print(f"[{self.dev2}] Reading from Main PC...")
            read_result = trigger_on_remote(self.dev2, remote_read,
                                            [target_url])
            print(f"[{self.dev2}] Result: {read_result}")

            assert read_result == self.test_string, (
                f"[{self.dev2}] Read incorrect message. "
                f"Expected '{self.test_string}', got '{read_result}'")
            print("SUCCESS: Message propagation verified!")

        finally:
            server.shutdown()
            server.server_close()

    def test_echo_async(self):
        """
        Async Orchestration test:
        1. Main PC starts HTTP server.
        2. dev2 starts polling for the message (non-blocking).
        3. Main PC thread sleeps for 5 seconds.
        4. dev1 connects to Main PC and POSTs "Hello world".
        5. dev2 receives the message and returns it.
        """

        SimpleEchoHandler.shared_message = None
        server = start_server(self.port)
        target_url = f"http://{SERVE_IP}:{self.port}"
        print(f"Main PC Server running at {target_url}")

        try:
            # Start `dev2` listener in the background
            print(f"[{self.dev2}] Starting async listen...")
            future_read = trigger_on_remote(self.dev2,
                                            remote_read_poll, [target_url],
                                            non_blocking=True)

            # Command `dev1` to write the message after 5 seconds
            time.sleep(5)
            print(f"[{self.dev1}] Writing '{self.test_string}' to Main PC...")
            write_result = trigger_on_remote(self.dev1, remote_write,
                                             [target_url, self.test_string])

            assert "successfully" in str(
                write_result), f"dev1 failed to write to {target_url}"

            # Wait for `dev2` to finish reading (it should have picked up the message)
            print(f"[{self.dev2}] Waiting for async read result...")
            read_result = future_read.result()
            print(f"[{self.dev2}] Async Result: {read_result}")

            assert read_result == self.test_string, (
                f"[{self.dev2}] Read incorrect message. "
                f"Expected '{self.test_string}', got '{read_result}'")
            print("SUCCESS: Async message propagation verified!")

        finally:
            server.shutdown()
            server.server_close()

    def test_echo_fully_async(self):
        """
        Fully Async test:
        1. Main PC starts HTTP server.
        2. Triggers dev2 (read) AND dev1 (write) asynchronously.
        3. Waits for both to complete.
        """

        SimpleEchoHandler.shared_message = None
        server = start_server(self.port)
        target_url = f"http://{SERVE_IP}:{self.port}"

        try:
            print(
                f"Starting fully async execution on {self.dev1} and {self.dev2}..."
            )

            # Trigger `dev2` as async listener
            future_read = trigger_on_remote(self.dev2,
                                            remote_read_poll, [target_url],
                                            non_blocking=True)

            # Trigger `dev1` as async writer
            future_write = trigger_on_remote(self.dev1,
                                             remote_write,
                                             [target_url, self.test_string],
                                             non_blocking=True)

            print("Waiting for tasks to complete...")

            write_result = future_write.result()
            print(f"[{self.dev1}] Write finished: {write_result}")
            assert "successfully" in str(write_result), "Write failed"

            read_result = future_read.result()
            print(f"[{self.dev2}] Read finished: {read_result}")
            assert read_result == self.test_string, \
                f"Expected '{self.test_string}', got '{read_result}'"
            print("SUCCESS: Fully async execution verified!")

        finally:
            server.shutdown()
            server.server_close()

    def name(self):
        return f"HTTP echo test ({self.dev1}, {self.dev2})"
