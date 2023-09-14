import time

def createUniqueId(credit, multiplier):
    return f"{int(time.time() * 1000)}-{credit * multiplier}"

def translateCreditTime(credit_time):
    return f'Time: {int(credit_time / 60)}hr {credit_time % 60}min'

def getCurrentTime():
    return int(time.time() * 1000)