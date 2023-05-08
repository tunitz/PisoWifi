from omada import Omada
import utilities as Util
import traceback
import asyncio
import time

class ClientService:
    time_out = 1 # in minutes

    def __init__(self):
        self.omada = Omada()

    def __loop__(self):
        while True:
            try:
                result = self.omada.login(asAdmin=True)

                if result is not None:
                    self.getClientsLoginHistory()
                    self.getAllActiveClients()
                    asyncio.run(self.processClients())
            except Exception:
                print(traceback.format_exc())
            
            print('Waiting 5 seconds before processing again')
            time.sleep(5)

    def getAllActiveClients(self):
        active_clients = []
        for client in self.omada.getAllActiveClients():
            if client['authStatus'] == 2:
                active_clients.append(client)
        self.active_clients = active_clients

    def getClientsLoginHistory(self):
        self.getAllActiveClients() # refresh active clients
        clientsLoginHistory = []
        for client in self.omada.getAllAuthedClients():
            if client['valid'] == True:
                clientsLoginHistory.append(client)
        self.clientsLoginHistory = clientsLoginHistory

    async def processClients(self):
        tasks = [asyncio.create_task(self.client_task(client)) for client in self.clientsLoginHistory]
        await asyncio.gather(*tasks)

    async def client_task(self, client):
        try:
            not_found = True
            mac = client['mac']
            for active_client in self.active_clients:
                if active_client['mac'] == client['mac']:
                    not_found = False

            if not_found:
                print(f'{mac} not Found! Disconnecting user')
                self.omada.disconnectClient(mac=mac)
            else:
                print(f'{mac} user is online!')

        except Exception:
            print(traceback.format_exc())

Util.checkOmada()

clientService = ClientService()
clientService.__loop__()