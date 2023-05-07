
from omada import Omada
import utilities as Util
import traceback
import asyncio
import time
import re

class VoucherService:
    def __init__(self):
        self.omada = Omada()

    def __loop__(self):
        # Run infinite
        while True:
            try:
                self.omada.login() # will try to login if no user is logged in yet

                self.getClientsLoginHistory() 
                self.getAllVouchers()

                asyncio.run(self.processVouchers())

                print('Waiting 30 seconds before processing vouchers again')
                time.sleep(30)
            except:
                print(traceback.format_exc())

    def getClientsLoginHistory(self):
        clients = []
        for client in self.omada.getAllAuthedClients():
            clients.append(client)
        self.clientsLoginHistory = clients

    def getAllVouchers(self):
        vouchers = []
        for voucher in self.omada.getAllVouchers():
            vouchers.append(voucher)
        self.vouchers = vouchers

    async def processVouchers(self):
        tasks = [asyncio.create_task(self.voucher_task(voucher)) for voucher in self.vouchers]
        await asyncio.gather(*tasks)

    async def voucher_task(self, voucher):
        try:
            valid_note = self.validate_note(voucher)
            if valid_note:
                time_limit = int(valid_note.group()) # This will get the last group of numbers
                voucher_expired = self.is_expired(voucher['code'], time_limit)
                if voucher_expired['expired'] == True:
                    self.deleteVoucher(voucher['id'], voucher_expired)

        except Exception:
            print(traceback.format_exc())

    def validate_note(self, voucher):
        # Regex expression
        # This will get the last group of numbers, separated by hyphen  (e.g. 'xxxxx-1234', '123456-1234', 'xxxxx-123456-1234', '1234') base on this example it will always get the value '1234'
        pattern = r'\b\d+\b$'
    
        valid_note = None
        if voucher['valid'] == True and 'note' in voucher:
            valid_note = re.search(pattern, voucher['note'])

        return valid_note
    
    def is_expired(self, voucherCode, limit):
        response = {'active_client_id': None, 'expired': False, 'time_used': 0, 'voucherCode': voucherCode, 'limit': limit}
        time_used = 0 # in seconds
        for client in self.clientsLoginHistory:
            if client['voucherCode'] == voucherCode:
                start = client['start']
                end = client['end']

                if client['valid'] == True:
                    response['active_client_id'] = client['id']
                    end = Util.getCurrentTime()

                time_used += Util.calculateTimeDiff(start, end)

        response['time_used'] = time_used
        response['expired'] = time_used >= limit
        print(f'voucher: {voucherCode} exipired: {time_used >= limit} time_used: {time_used} limit: {limit}')
        return response
    
    def deleteVoucher(self, voucherId, voucher_expired):
        voucherCode = voucher_expired['voucherCode']
        active_client_id = voucher_expired['active_client_id']
        time_used = voucher_expired['time_used']
        limit = voucher_expired['limit']

        if active_client_id is not None:
            self.omada.disconnectClient(active_client_id)
        self.omada.deleteVoucher(voucherId)
        message = f'Voucher: {voucherCode} Limit: {limit} Time Used: {round(time_used, 2)}mins'
        print('Deleted ' +message)
        Util.log_to_file('deleted_vouchers.log', message)

Util.checkOmada()

voucherService = VoucherService()
voucherService.__loop__()