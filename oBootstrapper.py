import socket
import pickle
import threading

# Map with neighbours
neighbours = {
    'server' : ['10.0.0.1', '10.0.1.1'],
    'n3': [ '10.0.5.2', '10.0.3.2',  '10.0.4.2'],
    'n4': ['10.0.18.2', '10.0.2.1'],
    'n5': [ '10.0.5.1', '10.0.7.2'],
    'n22': [ '10.0.3.1', '10.0.18.1', '10.0.13.2', '10.0.6.2'],
    'n7': [ '10.0.2.2', '10.0.4.1',  '10.0.8.2'],
    'n8': [ '10.0.7.1', '10.0.13.1', '10.0.11.2','10.0.12.2'],
    'n9': [ '10.0.8.1', '10.0.6.1',  '10.0.9.2', '10.0.10.2'],
    'n10': ['10.0.11.1'],
    'n11': ['10.0.12.1', '10.0.9.1'],
    'n12': ['10.0.10.1']
}

class Bootstrapper:
    def __init__(self):
        # Create socket
        bootstrapper = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bootstrapper.bind(('0.0.0.0', 5000))

        print('Bootstrapper listening for connections!')
        try:
            while True:
                bootstrapper.listen()
                conn, addr = bootstrapper.accept()
                threading.Thread(target= self.handler, args=(conn, addr)).start()
        finally:
            bootstrapper.close()

    # Bootstrapper connection handler
    def handler(self, connection, address):
        ip = str(address[0])
        print(f"[INFO] {ip} connection started.")

        data = connection.recv(1024).decode('utf-8')

        if data.startswith('NEIGHBOURS'):

            # Return node neighbours
            _, node_id = data.split()
            response = pickle.dumps(neighbours[node_id])

        connection.send(response)
        print(f"[INFO] Response sent to {ip}.")

        connection.close()
        print(f"[INFO] {ip} connection closed.")

if __name__ == "__main__":
    bootstrapper = Bootstrapper()