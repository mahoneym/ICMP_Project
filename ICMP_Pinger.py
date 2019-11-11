import os
import argparse
import socket
import struct
import select
import time


ICMP_ECHO_REQUEST = 8       # type of ECHO request here
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
        self.target_host = target_host                                      # the host's address
        self.count = count                                                  # how many ICMP packets to send
        self.timeout = timeout                                              # assigns how long the pinger will wait for a response


    def do_checksum(self, source_string):
        """
        Verify the packet integrity by calculating the checksum just like we did in class
        """
        sum = 0                                                             # initialize sum to 0
        max_count = (len(source_string)/2)*2                                # make the max_count equal to the length of string
        count = 0                                                           # initialize count to 0
        while count < max_count:                                            # as long as count is less than max_count
            val = source_string[count + 1]*256 + source_string[count]

            sum = sum + val                                                 # add val to the new sum
            sum = sum & 0xffffffff                                          # AND the sum with the unsigned integer
            count = count + 2                                               # increment the count by 2

        if max_count<len(source_string):                                    # if count is less than the length of the source string
            sum = sum + ord(source_string[len(source_string) - 1])          # set sum equal to the sum plus the unicode of length - 1
            sum = sum & 0xffffffff                                          # and the sum with the max unsigned int

        sum = (sum >> 16)  +  (sum & 0xffff)                                # adds sum shifted to the right 16 places and sum bitwise and 0xffff
        sum = sum + (sum >> 16)                                             # adds sum to sum shifted right 16 bits
        answer = ~sum                                                       # answer equals the inverted bits of sum
        answer = answer & 0xffff                                            # sets answers equal to answer bitwise anded with 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)                       # answer shifted right 8 bits ored with answer shifted left 8 anded with 0xff00
        return answer                                                       # return the answer

    def receive_pong(self, sock, ID, timeout):
        """
        We have to create a socket on our side so we can receive the replies from the destination host.
        We also have to make sure not to wait too long “TIMEOUT”.
        """
        time_remaining = timeout
        while True:
            start_time = time.time()                                        # get the time of starrting to listen
            readable = select.select([sock], [], [], time_remaining)
            time_spent = (time.time() - start_time)                         # calculates how much time has passed
            if readable == 0:                                               # if readable is 0, timeout has occurred
                return                                                      # get out of here cause we timed out

            time_received = time.time()
            recv_packet, addr = sock.recvfrom(1024)
            icmp_header = recv_packet[20:28]
            # bbHHh (or the first parameter for unpack) is the format of what is being returned by unpack
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
            if time_remaining <= 0:                                                         # if a timeout occurred
                return                                                                      # get out of here


    def send_ping(self, sock,  ID):
        """
        We have to create a packet and send it to the destination host,
        we are creating a dummy ICMP packet and attaching it to the IP header.
        """
        target_addr  =  socket.gethostbyname(self.target_host)                         # get the host name's IPv4 address

        my_checksum = 0                                                                # initialize checksum to zero

        # Create a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")                                         # get the size of the struct
        data = (192 - bytes_In_double) * "Q"                                           # fill the remaining packet space with Q's
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))

        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)                                               # compute the checksum of the header and data
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)       # set header to the packet as a byte object

        # add the data from above to the header to create a complete packet
        packet = header + data                                                         # put the header and data into a packet
        sock.sendto(packet, (target_addr, 1))                                          # send the packet to the socket


    def ping_once(self):
        """
        Returns the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")                                           # returns the constant for the ICMP protocol from the socket
        try:
            # add the ipv4 socket (same as we did in our first project,
            # SOCK_RAW(to bypass some of the TCP/IP handling by your OS)
            # and the ICMP packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)                 # create a new socket for icmp
        except socket.error as e:                                                       # catch an error thrown by the socket
            if e.errno == 1:                                                            # if there is an operations not permitted error
                print("Permissions error: The program must be run as admin")            # print operation is not permitted
                e.msg +=  "Not run as admin"                                            # Add 'Not run as admin' to the exception message
                raise socket.error(e.msg)                                               # throw the exception
        except Exception as e:                                                          # catch any other exceptions
            print ("Exception: %s" % e)                                                 # print the exception messege

        my_ID = os.getpid() & 0xFFFF                                                    # get the process id and bitwise AND it with 0xFFFF

        # Call the definition from send_ping above and send to the socket you created above
        self.send_ping(sock , my_ID)                                                    # send the ping
        delay = self.receive_pong(sock, my_ID, self.timeout)                            # receive the response and save the return value
        sock.close()                                                                    # close the socket
        return delay


    def ping(self):
        """
        Run the ping process
        """
        for i in range(self.count):                                                     # pings the number of times passed into the constructor
            print ("Ping to %s..." % self.target_host,)                                 # prints the ping message in the terminal
            try:
                delay  =  self.ping_once()                                              # pings the target_host and save the return value
            except socket.gaierror as e:                                                # if the result was an address error
                print ("Ping failed. (socket error: '%s')" % e[1])                      # prints an error message to the user
                break

            if delay  ==  None:                                                         # if the delay is null
                print ("Ping failed. (timeout within %ssec.)" % self.timeout)           # the ping failed during the timeout
            else:
                delay  =  delay * 1000                                                  # multiply the delay by 1000 to get milliseconds
                print ("Get pong in %0.4fms" % delay)                                   # print the delay for the user



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python ping')                                     # create a parser to add arguments
    parser.add_argument('--target-host', action="store", dest="target_host", required=True)         # adds the host argument to the command
    given_args = parser.parse_args()                                                                # parses the arguments
    target_host = given_args.target_host                                                            # puts the argument into target_host
    pinger = Pinger(target_host=target_host)                                                        # create a pinger with the given target_host
    pinger.ping()                                                                                   # ping the target_host
