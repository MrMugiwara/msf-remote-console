import time
import socket
import string
from metasploit.msfrpc import MsfRpcClient
from metasploit.msfrpc import MsfRpcError
from ssl import SSLError


class MsfConsole:

    # Objects
    client = None
    console = None

    # Variables
    console_id = ""
    current_path = ""
    last_path = ""

    def __init__(self, username, password, port, host, ssl):
        self.username = username
        self.password = password
        self.port = port
        self.host = host
        self.ssl = ssl

    # Connect to the msfrpcd server
    def connect(self):
        print "[*] Connecting to server:\n Host => %s,\n Port => %s,\n User => %s,\n " \
              "Pwd => %s,\n SSL => %s\n" % (self.host, self.port, self.username, '*' * len(self.password), self.ssl)
        # Login to msfrpcd server
        try:
            kwargs = {'username': self.username, 'port': self.port, 'server': self.host, 'ssl': self.ssl}
            self.client = MsfRpcClient(self.password, **kwargs)
            print "[+] Successfully connected"
        except SSLError, msg:
            print "[-] SSL error: " + str(msg)
            print "[-] You probably have installed the wrong pymetasploit version try installing it from here: https://github.com/allfro/pymetasploit.git"
            return False
        except socket.error, msg:
            print "[-] Couldn't connect to server: " + str(msg)
            return False
        except MsfRpcError:
            print "[-] Login failed. Wrong username or password"
            return False
        # Create console and id
        self.console = self.client.consoles.console()
        self.console_id = self.console.cid
        print "[*] Console id: " + self.console_id
        # Read msf banner
        self.read_output()
        return True

    # Read the output from msfconsole
    def read_output(self):
        try:
            timer = 0
            while timer <= 3:
                # Request information from msfrpcd
                resource = self.client.call('console.read', self.console_id)

                # Check for printable information
                if len(resource['data']) > 1:
                    print resource['data']
                    break

                # If msf command still running try requesting again
                if resource['busy']:
                    time.sleep(0.1)
                    continue

                # If msf path changed break out to save time
                elif self.last_path != self.current_path:
                    # print "Path is different use break: current: " + self.current_path + " last: " + self.last_path
                    break

                # Else try again till 3 seconds reached
                else:
                    time.sleep(0.5)
                    timer += 0.5

            return True
        except AttributeError:
            print "[-] You have to be connected to the server"
            return False
        except KeyError:
            print "[-] Has the console been destroyed ? "
            print resource if 'resource' in locals() else "Couldn't print error"
            return False

    # Load resource file and execute every command
    def load_resource(self, path_to_resource):
        try:
            # Read resource file
            try:
                print "[*] Reading resource file..."
                infile = open(path_to_resource, 'r')
                commands = infile.readlines()
                infile.close()
            except IOError:
                print "[-] Path to resource file not found"
                return False

            # Loop through every command and execute it
            print "[*] Number of commands to execute: " + str(len(commands))
            for line in commands:
                self.console.write(line)
                self.read_output()
            print "[+] Finished executing resource script"

            # List created jobs
            self.list_jobs()
            return True
        except AttributeError:
            print "[-] You have to be connected to the server"
            return False

    # List running jobs
    def list_jobs(self):
        try:
            # Request list of running jobs
            resource = self.client.jobs.list

            # If no error occurred
            if "error" not in resource:
                print "[+] Listing jobs..."
                print resource
                return True

            # If error occurred
            elif "error" in resource:
                print "[-] An error has occurred in listing jobs.\n"
                print resource
                return False
        except AttributeError:
            print "[-] You have to be connected to the server"
            return False

    # Execute command in msfconsole
    def exec_command(self, command):
        try:
            self.console.write(command)
            self.get_path()
            self.read_output()
            return True

        except AttributeError:
            print "[-] You have to be connected to the server"
            return False

    # Disconnect from msfconsole
    def disconnect(self):
        try:
            print "[*] Quitting..."
            self.console.destroy()
            self.client.client.close()
        except AttributeError:
            print "[-] You have to be connected to the server"
            return False

    # Get current msfconsole path
    def get_path(self):
        try:
            # Request data from server
            resource = self.client.call('console.list')

            # Filter the path out of it
            for console in resource['consoles']:
                if console['id'] == self.console_id:
                    s = console['prompt']
                    extracted_path = ''.join(c for c in s if c in string.printable)

                    # Check if path of console changed if true save old path and set new current path
                    if extracted_path != self.current_path:
                        self.last_path = self.current_path
                        self.current_path = extracted_path
                    return extracted_path
        except AttributeError:
            print "[-] You have to be connected to the server"
            return ""
