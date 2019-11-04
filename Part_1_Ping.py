import subprocess
import shlex

cmd   = "ping -c 1 www.cs.xu.edu"           # saves the command in a variable

args = shlex.split(cmd)                     # parses cmd to get it ready for the check_call method
try:
    subprocess.check_call(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print ("Xavier CS web server is up!")       # prints that the ping was received
except subprocess.CalledProcessError:           # if CalledProcessError exception, the ping wasn't received
    print ("Failed to get ping.")               # prints failed ping
