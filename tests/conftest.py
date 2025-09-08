from pytest_socket import disable_socket, enable_socket
import pytest

@pytest.fixture(autouse=True, scope="session")
def _no_sockets():
    disable_socket()
    yield
    enable_socket()
