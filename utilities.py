from omada import Omada
import traceback
import logging
import time

# Checks if Omada API is ready
def checkOmada():
    omada_available = None
    print('Checking if omada is available')
    while omada_available is None:
        try:
            omada = Omada()
            omada_available = omada.getApiInfo()
        except Exception:
            print(traceback.format_exc())
        finally:
            if omada_available is None:
                print('Omada is not yet available')
                time.sleep(10)
            else:
                print('Omada is available')

def createUniqueId(credit, multiplier):
    return f"{int(time.time() * 1000)}-{credit * multiplier}"

def translateCreditTime(credit_time):
    return f'Time: {int(credit_time / 60)}hr {credit_time % 60}min'
