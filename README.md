# Start Hashcat Process in Multiple Nodes

## What it does ?

### Problem

- We can have multiple servers that are free, where we can crack some hash. 
- We need to run different hash files with different dictionaries in those servers.
- Its really troublesome to every time going to each server and starting the process.

### Solution

- We can create a input.json file as shown in the example below.
- Then execute the command with the input.json file as argument.
- The script will forward those files to each server, process and get the result.
- This way we can get all the result in centralized location.



### Example

We create input.json file such as 

```json
{
  "global": {
    "user": "admin",
    "hashcat_command": "hashcat -a 0 -m 2500 --status --status-timer=20",
    "ssh_key_filepath": "/Users/your_user/.ssh/id_rsa",
    "input_file": "omnamashiva.hccapx"
  },
  "hosts": [
    {
      "ip": "192.168.0.100",
      "dictionary": "nepali-name-suffix-8+.txt"
    },
    {
      "ip": "192.168.0.105",
      "user": "support",
      "dictionary": "wordlist-probable.txt",
      "ssh_key_filepath": "/Users/your_user/.ssh/support/id_rsa",
      "hashcat_command": "hashcat -a 0 -m 2500 --status --status-timer=60"
    },
    {
      "ip": "192.168.0.101",
      "dictionary": "nepali-name-suffix-8+.txt"
    },
    {
      "ip": "192.168.0.102",
      "dictionary": "custom-wordlist.txt"
    },
    {
      "ip": "192.168.0.104",
      "dictionary": "rockyou.txt"
    },
    {
      "ip": "CURRENT",
      "hashcat_command": "hashcat -a 0 -m 2500 --status --status-timer=5",
      "dictionary": "small-size.txt"
    }
  ]
}
```

### About the Input Format

1. ***global***: This should contain
    - USER: The user for ssh access in the nodes.
    - HASHCAT COMMAND: The hashcat command.(It should not contain the input hash file and dictionary, and also the 
    output format of the hashcat command should not be changed.)
    - SSH KEY FILE PATH: SSH identity file path.
    - HASH INPUT FILE PATH: A single input hash file path.
    
2. ***hosts***:
    - This contains the list of nodes where hashcat process will run.<br>
    - In each of the row inside ***hosts***, the **ip** and **dictionary** fields are mandatory. If other fields are missing then, 
    It will update them from the global.
    - We can also execute the commands in current machine, We just need to assign **CURRENT** in the **ip** field


**To start the process, we execute the command with input.json file as argument.**

`python hashcat_cluster.py --input_file input.json`


### What this command will do is,
1. Connect to all the  hosts parallelly using ssh.
2. Create temporary directory in every host.
3. Copy input file and the assigned dictionary file to temporary location using scp.
4. Then it will execute the hashcat command supplied by the user in those hosts.
5. A polling system will poll for output generated by the hashcat command and wait for completion.
6. If any of the hash is recovered(decrypted) then It will pull the result from those hosts.
7. The process logs and the result will be inside the OUTPUT folder.



### Hashcat Command 
**User can change the command according to their need. But there are certain things that we need to remember. **

- The user should not include the input and dictionary file in hashcat command. The script will automatically add those file.
- The user should not change the output format of hashcat command.
- User either can add --status and --status-timer argument, If they like to know the progress between some interval of time.


### Result File

- Result of every process will be inside the OUTPUT Folder.
- The format of the result file is `{host}_{input_file_name}_{dictionary_file}.result`
- The Result file contains the last 19 lines of log generated from the hashcat process and result of the hashcat process.
