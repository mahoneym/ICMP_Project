# ICMP_Project
By: Maggie Mahoney

For part 2 of the project, I developed it using Python3 on Mac operating system. The program can be run from the command line. In order to be successful, the program must be run using admin or sudo. For example, on Mac, the command to run the program:
          sudo python3 ICMP_Pinger.py --target-host 'www.google.com'
The program will print that it has pinged the given host and, when it receives the response (or the pong), it will print how long it took to receive the pong. The program will ping the target host four times after it receives the pong.
If the program is not run using sudo or admin, it will throw an exception and the program will stop.
