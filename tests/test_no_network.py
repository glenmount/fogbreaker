import pytest, socket

def test_network_blocked():
    with pytest.raises(Exception):
        socket.create_connection(('example.com',80),timeout=1)
