# Start Hashcat Process in Multiple Nodes

## Overview

### Problem

We often have multiple available servers where we can perform hash cracking. However, it becomes cumbersome to manually start the cracking process on each server every time. 

### Solution

To address this problem, we can automate the process using a script. The script takes an input JSON file as an argument and performs the following steps:

1. Connects to multiple servers in parallel using SSH.
2. Creates a temporary directory on each server.
3. Copies the input hash file and assigned dictionary file to the temporary directory using SCP (Secure Copy).
4. Executes the user-defined hashcat command on each server.
5. Monitors the progress and waits for completion.
6. Retrieves the results if any hashes are decrypted.
7. Logs the process and stores the results in a centralized location.

## Usage Example

To initiate the process, you need to create an `input.json` file with the desired configuration. Here's an example of the input file structure:

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

To start the process, execute the following command with the input.json file as an argument:

```
python hashcat_cluster.py --input_file input.json
```

The script will handle the execution on multiple servers, monitor the progress, and collect the results in a centralized location for easy access.
