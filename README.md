**HashCat Multiple Dictionaries and Multiple Host Cluster**

This python script distribute the multiple dictionaries to multiple host for decrypting the hash using hashcat.

For Example,
We have two hosts and two dictionaries for a single input hash file. Then we can  process two dictionaries in the each of the host.  

A sample command for two host and two dictionaries

` python command.py -hs "192.168.0.100" "192.168.0.102" -u "admin" "admin" -s "/Users/your_user/.ssh/id_rsa" -i "omnamashiva.hccapx" -w "wordlist-probable.txt" "nepali-name-suffix-8+.txt" -hc "hashcat -a 0 -m 2500 --status --status-timer=20 -d 1,3"`

Parsed Argument

`host = ['192.168.0.100', '192.168.0.102']`<br>
`users = ['admin', 'admin']`<br>
`ssh_key_filepath = /Users/your_user/.ssh/id_rsa`<br>
`input_file = omnamashiva.hccapx`<br>
`word_list = ['wordlist-probable.txt', 'nepali-name-suffix-8+.txt']`<br>
`hashcat_command = hashcat -a 0 -m 2500 --status --status-timer=20`

What this command will do is,
1. Connect to two hosts parallelly using ssh.
2. Create temporary directory.
3. Copy input file and one of the dictionary file to temporary location using scp.
4. Then it will execute the hashcat command supplied by the user in those hosts.
5. A polling system will poll for output generated by the hashcat command and wait for completion.
6. If any of the hash is recovered(decrypted) then It will pull the result from those hosts.


About hashcat command input => `hashcat -a 0 -m 2500 --status --status-timer=20`
- The user should not include the input and dictionary file in hashcat command. The script will automatically add those file.
- The user should not change the output format of hashcat command.
- User either can add --status and --status-timer argument, If they like to know the progress between some interval of time.
