import socket
import pickle
import threading
import subprocess
import time
from colorama import Back, Style

class oClient:
    def __init__(self):
        self.pops = [] # Lista pontos de presença
        self.pop = '' # Ponto de presença a ser usado
        self.timeout = 1 # Tempo para timeout em segundos

        self.stream_choosen = ''
        self.streams_list = []

        # Client socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 6000))
        self.socket.settimeout(self.timeout)

        # RUN!!!
        self.get_points_of_presence()
        threading.Thread(target=self.monitor_points_of_presence).start()        
        self.get_list_of_streams()

        # Escolhe uma stream da lista de streams disponiveis
        print('--- Lista de streams ---')
        for stream in self.streams_list:
            print(stream)

        while True:
            self.stream_choosen = input('Digite a stream desejada: ')
            if not self.stream_choosen in self.streams_list:
                print(Back.RED + '[FAIL] Stream inserida não existe.' + Style.RESET_ALL)
            else:
                break

        # Display stream
        while self.pop == '': # Aguardar até pop ser selecionado
            time.sleep(1)
        message = str.encode(f'STREAM {self.stream_choosen}')
        self.socket.sendto(message, (self.pop, 6000))
        self.display_stream()

    # Get points of presence from server - UDP
    def get_points_of_presence(self):
        while True:
            try:
                # Envia mensagem
                message = str.encode('POPS')
                self.socket.sendto(message,  ('10.0.0.10', 6000))

                # Recebe lista de POPs
                self.pops = pickle.loads(self.socket.recv(2048))
                print(Back.GREEN + '[SUCCESS] Pontos de presença obtidos com sucesso.' + Style.RESET_ALL)
                break
            except socket.timeout:
                print(Back.YELLOW + '[WARNING] Timeout - Reenvio de pedido de lista de pontos de presença.' + Style.RESET_ALL)
            except:
                print(Back.RED + '[FAIL] Servidor não está a atender pedidos.' + Style.RESET_ALL)
                self.socket.close()
                break

    # Get list of streams available to play (from POP) - UDP
    def get_list_of_streams(self):
        while self.pop == '':
            time.sleep(1)

        while True:
            try:
                # Envia mensagem
                message = str.encode('LISTSTREAMS')
                self.socket.sendto(message, (self.pop, 6000))

                # Recebe lista de streams
                self.streams_list = pickle.loads(self.socket.recv(1024))
                print(Back.GREEN + f'[SUCCESS] Lista de streams obtida com sucesso. STREAMS: {self.streams_list}' + Style.RESET_ALL)
                break
            except socket.timeout:
                print(Back.YELLOW + '[WARNING] Timeout - Reenvio de pedido de lista de streams.' + Style.RESET_ALL)
                continue
            except:
                print(Back.RED + '[FAIL] Servidor não está a atender pedidos.' + Style.RESET_ALL)
                self.socket.close()
                break

    # Display video from server (POP) - UDP
    def display_stream(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 7000))
        sock.settimeout(self.timeout)

        ffplay = subprocess.Popen(
            ['ffplay', '-i', 'pipe:0', '-hide_banner', '-infbuf'],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL)

        pops_timeout = []

        try:
            while True:
                try:
                    data, address = sock.recvfrom(2200)

                    # Se o pacote recebido for de um pop diferente do selecionado atualmente
                    # enviar mensagem para cancelar o envio de pacotes
                    if address[0] != self.pop:
                        message = str.encode(f'NOSTREAM {self.stream_choosen}')
                        self.socket.sendto(message, (address[0], 6000))
                    else:
                        if len(pops_timeout) > 0:
                            pops_timeout = []

                    packet = pickle.loads(data)
                    video = packet['data']
                    ffplay.stdin.write(video)
                    ffplay.stdin.flush()
                except socket.timeout: # 5 segundos
                    pops_timeout.append(self.pop)
                    for pop in self.pops:
                        if pop not in pops_timeout:
                            self.pop = pop
                            message = str.encode(f'STREAM {self.stream_choosen}')
                            self.socket.sendto(message, (self.pop, 6000))
                            break
        except:
            print(Back.RED + f'[FAIL] Erro a mostrar stream' + Style.RESET_ALL)
            message = str.encode(f'NOSTREAM {self.stream_choosen}')
            self.socket.sendto(message, (address[0], 6000))
            sock.close()
            ffplay.stdin.close()
            ffplay.wait()

######## MONITORIZAÇÃO DE POPS POR PARTE DO CLIENTE ########
    def monitor_points_of_presence(self):
        while True:
            valores = {}
            for pop in self.pops:
                times = []
                for _ in range(5):
                    try:
                        msg = str.encode('PING')
                        start = time.time()
                        self.socket.sendto(msg, (pop, 6000))
                        response = self.socket.recv(1024).decode()
                        if response:
                            _, latency = response.split(':')
                            end = time.time()
                            volta = start - end
                            times.append(round(volta + float(latency), 5))
                    except socket.timeout:
                        print(Back.YELLOW + '[WARNING] Timeout - Reenvio de pedido PING.' + Style.RESET_ALL)
                        continue

                if len(times) == 0:
                    valores[pop] = (9999999, 100000)
                else:
                    valores[pop] = (sum(times)/len(times), 5/len(times))

            last_pop = self.pop

            menor = None
            for pop in valores:
                if menor is None:
                    menor = self.avalia(valores[pop])
                    self.pop = pop
                    print(f'Initial evaluation: {menor} for pop {pop}')
                else:
                    print('Comparing ') 
                    atual = self.avalia(valores[pop])
                    print(f'Evaluating: {atual} for pop {pop}')
                    if atual < menor:
                        menor = atual
                        self.pop = pop
                        print(f'POP changed to {self.pop} with a new lower value of {menor}')
                    else:
                        print(f'No change, current value is lower ({menor})')

            if last_pop != self.pop and self.stream_choosen != '':
                # Cancela stream
                message = str.encode(f'NOSTREAM {self.stream_choosen}')
                self.socket.sendto(message, (last_pop, 6000))

                # Pede a stream ao novo pop
                message = str.encode(f'STREAM {self.stream_choosen}')
                self.socket.sendto(message, (self.pop, 6000))

            time.sleep(60)

    def avalia(self, data):
        result = data[0] * data[1]
        if data[1] >= 2: # 2 pings por acerto
            if data[1] < 3.5: # 3.5 pings por acerto
                result *= 1.5
            else:
                result *= 2
        result = round(result,6)
        return result

if __name__ == "__main__":
    client = oClient()