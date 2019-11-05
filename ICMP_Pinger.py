import os
import argparse
import socket
import struct
import select
import time


ICMP_ECHO_REQUEST = 8       # Fill in the type of ECHO request here (Platform specific)
DEFAULT_TIMEOUT = 2         # set the timeout for the pinger
DEFAULT_COUNT = 4           # the number of pings to send


class Pinger(object):
    """
    The Pinger class defines an object that will send and receive ICMP echo requests and
    replies to itself or other hosts. The constructor takes a target_host, the number of
    pings to send (defaults to 4 if no input), and the amount of time for a timeout
    (defaults to 2 if no input).
    """

    def __init__(self, target_host, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
        """
        The constructor for the pinger class
        """
        self.target_host = target_host      # the host's address
        self.count = count                  # how many ICMP packets to send
        self.timeout = timeout              # assigns how long the pinger will wait for a response


    def do_checksum(self, source_string):
        """  Verify the packet integrity by calculating the checksum just like we did in class """
        sum = 0
        max_count = (len(source_string)/2)*2
        count = 0
        while count < max_count:

            # To make this program run with Python 2.7.x:
            # val = ord(source_string[count + 1])*256 + ord(source_string[count])
            # ### uncomment the above line, and comment out the below line.
            val = source_string[count + 1]*256 + source_string[count]
            # In Python 3, indexing a bytes object returns an integer.
            # Hence, ord() is redundant.

            sum = sum + val
            sum = sum & 0xffffffff
            count = count + 2

        if max_count<len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff

        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def receive_pong(self, sock, ID, timeout):
        """
        We have to create a socket on our side so we can receive the replies from the destination host.
        We also have to make sure not to wait too long “TIMEOUT”.
        """
        time_remaining = timeout
        while True:
            start_time = time.time()
            readable = select.select([sock], [], [], time_remaining)
            time_spent = (time.time() - start_time)
            if readable == 0: #Timeout occurs if readable is 0, hopefully remember what time out is now
                return                                           # get out of here

            time_received = time.time()
            recv_packet, addr = sock.recvfrom(1024)
            icmp_header = recv_packet[20:28]
            # bbHHh (or the first parameter for unpack) is the format of what is being returned
            # b = signed char or integer in python
            # H = unassigned short or integer in python
            # h = short or integer in python
            type, code, checksum, packet_ID, sequence = struct.unpack(
                "bbHHh", icmp_header
            )
            if packet_ID == ID:
                bytes_In_double = struct.calcsize("d")                                      # returns the size of the struct
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]     # parses the packet to get the time it was sent
                return time_received - time_sent                                            # returns how long it took for response to arrive

            time_remaining = time_remaining - time_spent                                    # resets the time remaining after this loop
            if time_remaining <= 0:                                                         # if there is no time remaining
                return                                                                      # get out of here


    def send_ping(self, sock,  ID):
        """
        We have to create a packet and send it to the destination host,
        we are creating a dummy ICMP packet and attaching it to the IP header.
        """
        target_addr  =  socket.gethostbyname(self.target_host)

        my_checksum = do_checksum()     #Fill in

        # Create a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")                                              # get the size of the struct
        data = (192 - bytes_In_double) * "Q"                                                # fill the remaining packet space with Q's
        data = struct.pack("d", time.time()) + bytes(data.encode('#Fill in'))

        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)

        packet = header + data              # add the data from above to the header to create a complete packet
        #send the packet to the target address
        sock.sendto(#Fill in, (target_addr, 1))


    def ping_once(self):
        """
        Returns the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
        #add the ipv4 socket (same as we did in our first project, SOCK_RAW(to bypass some of the TCP/IP handling by your OS) and the ICMP packet
            #sock = socket.socket(#Fill in, socket.SOCK_RAW, icmp)
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error as e:
            if e.errno == 1:
                print("Permissions error: The program must be run as admin")   # If not run by admin, operation is not permitted
                e.msg +=  "" #Fill in before
                raise socket.error(e.msg)
        except Exception as e:
            print ("Exception: %s" % e)                     #print the errror messege

        my_ID = os.getpid() & 0xFFFF

        #Call the definition from send.ping above and send to the socket you created above
        self.send_ping(sock , my_ID)
        delay = self.receive_pong(sock, my_ID, self.timeout)
        sock.close()
        return delay


    def ping(self):
        """
        Run the ping process
        """
        for i in range(self.count):
            print ("Ping to %s..." % self.target_host,)
            try:
                delay  =  self.ping_once()
            except socket.gaierror as e:
                print ("Ping failed. (socket error: '%s')" % e[1])
                break

            if delay  ==  None:
                print ("Ping failed. (timeout within %ssec.)" % self.timeout)
            else:
                delay  =  delay * 1000
                print ("Get pong in %0.4fms" % delay)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python ping')
    parser.add_argument('--target-host', action="store", dest="target_host", required=True)
    given_args = parser.parse_args()
    target_host = given_args.target_host
    pinger = Pinger(target_host=target_host)
    pinger.ping()
