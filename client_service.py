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
                    self.getAllActiveClients()

                    asyncio.run(self.processClients())

                    self.getClientsLoginHistory()
                    asyncio.run(self.processDoubleCheck())
                    
            except Exception:
                print(traceback.format_exc())
            
            print('Waiting 30 seconds before processing clients again')
            time.sleep(30)

    def getClientsLoginHistory(self):
        self.getAllActiveClients() # refresh active clients
        clientsLoginHistory = []
        for client in self.omada.getAllAuthedClients():
            if client['valid'] == True:
                clientsLoginHistory.append(client)
        self.clientsLoginHistory = clientsLoginHistory

    async def processDoubleCheck(self):
        tasks = [asyncio.create_task(self.double_check_task(client)) for client in self.clientsLoginHistory]
        await asyncio.gather(*tasks)

    async def double_check_task(self, client):
        try:
            not_found = True
            mac = client['mac']
            for active_client in self.active_clients:
                if active_client['mac'] == client['mac']:
                    not_found = False

            if not_found:
                print(f'{mac} not Found! Disconnecting user')
                self.omada.disconnectClient(mac=mac)

        except Exception:
            print(traceback.format_exc())

    def getAllActiveClients(self):
        active_clients = []
        for client in self.omada.getAllActiveClients():
            if client['authStatus'] == 2:
                active_clients.append(client)
        self.active_clients = active_clients

    async def processClients(self):
        tasks = [asyncio.create_task(self.client_task(client)) for client in self.active_clients]
        await asyncio.gather(*tasks)

    async def client_task(self, client):
        try:
            mac = client['mac']
            lastSeen = client['lastSeen']
            now = Util.getCurrentTime()
            time_passed = Util.calculateTimeDiff(lastSeen, now)
            print(f'mac: {mac} lastSeen: {lastSeen} time_passed: {round(time_passed, 2)}')
            if time_passed > self.time_out:
                print(f'Disconnecting user {mac}')
                self.omada.disconnectClient(mac=mac)
        except Exception:
            print(traceback.format_exc())

Util.checkOmada()

clientService = ClientService()
clientService.__loop__()