import pytest, socket
from pytest_socket import disable_socket

def test_network_blocked():
    disable_socket()  # force-disable sockets for this test
    with pytest.raises(Exception):
        socket.create_connection(("example.com", 80), timeout=1)
