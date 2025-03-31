from socket import *
import os
import sys
import struct
import time
import select
from src.constants import ICMP_ECHO_REQUEST, MAX_HOPS, TIMEOUT, TRIES
from src.geo import cached_gethostbyname

def checksum(source_string):
    csum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = source_string[count+1] * 256 + source_string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(source_string):
        csum = csum + source_string[len(source_string) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def build_packet():
    my_id = os.getpid() & 0xFFFF
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, my_id, 1)
    data = struct.pack("d", time.time())
    my_checksum = checksum(header + data)
    if sys.platform == 'darwin':
        my_checksum = htons(my_checksum) & 0xffff
    else:
        my_checksum = htons(my_checksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, my_id, 1)
    return header + data

def get_route(hostname):
    hops = []
    # Use cached DNS resolution
    try:
        print(f"Resolving hostname: {hostname}")
        dest_ip = cached_gethostbyname(hostname)
        print(f"Resolved {hostname} to {dest_ip}")
    except Exception as e:
        print(f"Error resolving hostname {hostname}: {e}")
        return hops
    
    # Check socket permissions early
    try:
        test_socket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
        test_socket.close()
    except PermissionError:
        print("ERROR: Insufficient permissions to create raw socket. Run as administrator/root.")
        error_hop = {
            "ttl": 1, 
            "ip": None, 
            "rtt": None, 
            "status": "error: Insufficient permissions. Run as root/administrator.",
            "attempt": 1
        }
        hops.append(error_hop)
        return hops
    except Exception as e:
        print(f"Error creating test socket: {e}")
    
    for ttl in range(1, MAX_HOPS + 1):
        print(f"Tracing route to {hostname} with TTL={ttl}")
        for attempt in range(TRIES):
            mySocket = None
            try:
                mySocket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
                mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
                mySocket.settimeout(TIMEOUT)
                packet = build_packet()
                mySocket.sendto(packet, (dest_ip, 0))
                start_time = time.time()
                whatReady = select.select([mySocket], [], [], TIMEOUT)
                if whatReady[0] == []:  # Timeout
                    print(f"  TTL={ttl}, Attempt={attempt+1}: Timeout")
                    hops.append({"ttl": ttl, "ip": None, "rtt": None, "status": "timeout", "attempt": attempt + 1})
                    continue
                recvPacket, addr = mySocket.recvfrom(1024)
                rtt = (time.time() - start_time) * 1000  # ms
                print(f"  TTL={ttl}, Attempt={attempt+1}: Success, IP={addr[0]}, RTT={rtt:.2f}ms")
                hops.append({"ttl": ttl, "ip": addr[0], "rtt": rtt, "status": "success", "attempt": attempt + 1})
                if addr[0] == dest_ip:  # Reached destination
                    print(f"Reached destination {dest_ip}")
                    return hops
                break
            except Exception as e:
                print(f"  TTL={ttl}, Attempt={attempt+1}: Error: {str(e)}")
                hops.append({"ttl": ttl, "ip": None, "rtt": None, "status": f"error: {str(e)}", "attempt": attempt + 1})
                break
            finally:
                if mySocket:
                    mySocket.close()
    
    print(f"Completed route trace to {hostname}, collected {len(hops)} hops")
    return hops
