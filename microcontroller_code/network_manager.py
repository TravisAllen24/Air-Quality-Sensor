import wifi
import socketpool

class WifiManager:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.pool = None

    def connect(self):
        """Connect to the specified Wi-Fi network."""
        wifi.radio.connect(self.ssid, self.password)
        print(f"Connected to {self.ssid}!")
        self.pool = socketpool.SocketPool(wifi.radio)

    def disconnect(self):
        """Disconnect from the Wi-Fi network."""
        wifi.radio.disconnect()
        print("Disconnected from Wi-Fi.")
        self.pool = None

    def is_connected(self):
        """Check if the device is connected to Wi-Fi."""
        return wifi.radio.ipv4_address is not None

    def create_socket(self):
        """Create a TCP socket using the socket pool."""
        if not self.pool:
            raise RuntimeError("Socket pool not initialized. Call connect() first.")
        return self.pool.socket(socketpool.AF_INET, socketpool.SOCK_STREAM)
    
    def open_tcp_connection(self, host, port):
        """Open a TCP connection to the specified host and port."""
        sock = self.create_socket()
        sock.connect((host, port))
        return sock
    
    def close_tcp_connection(self, sock):
        """Close the given TCP socket."""
        sock.close()

    def send_data(self, sock, data):
        """Send data over the given TCP socket."""
        sock.send(data)

    def receive_data(self, sock, buffer_size=1024):
        """Receive data from the given TCP socket."""
        return sock.recv(buffer_size)
    


class BluetoothManager:
    ...