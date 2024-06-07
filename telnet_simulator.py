import socket
import threading

class SCPITelnetSimulator:
    def __init__(self, host='127.0.0.1', port=5025):
        self.host = host
        self.port = port
        self.commands = {
            "*IDN?": "Simulated Instrument, Model 1234, Serial 5678, Firmware 1.0",
            "MEAS:VOLT?": "3.3"
        }
        self.server = None

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"Simulated SCPI server started on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def handle_client(self, client_socket):
        with client_socket as sock:
            while True:
                try:
                    data = sock.recv(1024).decode('ascii').strip()
                    if not data:
                        break
                    print(f"Received command: {data}")
                    response = self.commands.get(data, "ERROR: Unknown command")
                    sock.sendall((response + '\n').encode('ascii'))
                except ConnectionResetError:
                    break

    def stop(self):
        if self.server:
            self.server.close()
            self.server = None
            print("Simulated SCPI server stopped")

if __name__ == "__main__":
    simulator = SCPITelnetSimulator()
    try:
        simulator.start()
    except KeyboardInterrupt:
        simulator.stop()
