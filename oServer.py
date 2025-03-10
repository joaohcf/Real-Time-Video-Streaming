import os
import socket
import threading
import pickle
import time
from colorama import Back, Style

# List of points of presence
pops = ['10.0.27.1', '10.0.26.1', '10.0.14.1']

class Server:
    def __init__(self):
        # List of neighbours
        self.neighbours = []

        # List of videos available
        self.videos = []

        # List of streams
        # Key:stream & Value:list of clients
        self.streams = {}

        # Create server socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(('0.0.0.0', 6000))

        # RUN!!!
        self.get_neighbours_from_bootstrapper()
        self.make_list_of_videos()
        threading.Thread(target=self.build_distribution_tree).start()
        self.stream_videos()

        print(Back.LIGHTBLUE_EX + '[INFO] Server listening for requests.' + Style.RESET_ALL)
        try:
            while True:
                data, addr = self.server.recvfrom(1024)
                threading.Thread(target=self.handler, args=(data, addr)).start()
        finally:
            self.server.close()

    # Handler for clients
    def handler(self, data, address):
        msg = data.decode('utf-8')
        if msg.startswith('STREAM'):

            # Adiciona o cliente à lista de clientes de uma stream requisitada
            client = str(address[0])
            _, stream_id = msg.split()
            if client not in self.streams[stream_id]:
                self.streams[stream_id].append(client)

        elif msg.startswith('NOSTREAM'):

            # Remove o cliente da lista de clientes de uma stream
            client = str(address[0])
            _, stream_id = msg.split()
            if stream_id in self.streams:
                self.streams[stream_id].remove(client)

        elif msg.startswith('POPS'):

            # Devolve a lista de pops ao cliente
            response = pickle.dumps(pops)
            self.server.sendto(response, address)

        elif msg.startswith('PARENT'):

            # Devolve o IP do nodo pai - Neste caso devolve o próprio servidor
            response = '10.0.0.10'.encode()
            self.server.sendto(response, address)

        elif msg.startswith('KEEPALIVE'):

            print(Back.LIGHTBLUE_EX + f"[INFO] Received from {address[0]}: KEEPALIVE" + Style.RESET_ALL)
            msg = 'ALIVE'.encode()
            self.server.sendto(msg, address)

    # Build distribution tree - UDP
    # every 60 sec
    def build_distribution_tree(self):
        current_flood = 1
        while(True):
            print(Back.LIGHTBLUE_EX + '[INFO] Building distribution trees.' + Style.RESET_ALL)
            for neighbour in self.neighbours:
                message = str.encode(f'BUILDTREE:{current_flood}:{time.time()}:0:0:{self.videos}') # . : horario : latência : saltos
                self.server.sendto(message, (neighbour, 6000))
            current_flood += 1
            time.sleep(60)

    # Make list of videos available to stream
    def make_list_of_videos(self):
        folder_path = './videos'
        try:
            self.videos = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file)) and file != '.gitkeep']
        except Exception as e:
            print(f"An error occurred: {e}")
            self.videos = []

    # Stream available videos
    def stream_videos(self):
        for video in self.videos:
            self.streams[video] = []
            threading.Thread(target=self.stream_video, args=(video,)).start()
        print('[INFO] Streaming videos.')

    # Stream video - UDP
    def stream_video(self, video):
        BUFFERSIZE = 2048
        BITRATE = 2_000_000
        interval = BUFFERSIZE * 8 / BITRATE # CBR
        video_file = open('./videos/' + video, 'rb')
        while True:
            video_data = video_file.read(BUFFERSIZE)

            if not video_data:
                video_file.seek(0)
                continue

            packet = {
                'id': video,
                'data': video_data
            }

            for client in self.streams[video]:
                self.server.sendto(pickle.dumps(packet), (client, 7000))

            time.sleep(interval)

    # Get neighbours from bootstrapper - TCP
    def get_neighbours_from_bootstrapper(self):
        bs_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Conexão com boostrapper
            bs_conn.connect(('10.0.34.2', 5000))

            # Envia mensagem
            message = str.encode(f'NEIGHBOURS server')
            bs_conn.send(message)

            # Recebe lista de vizinhos
            self.neighbours = pickle.loads(bs_conn.recv(2048))
            print('Vizinhos obtidos com sucesso.')
        except:
            print('Bootstrapper offline.')
        finally:
            bs_conn.close()

if __name__ == "__main__":
    server = Server()
