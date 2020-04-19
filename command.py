#!/usr/bin/env python

import uuid
import time

from utils.client import RemoteClient
from utils.helper import *
from threading import Thread


logger = logging.getLogger("Logger")

PROCESS_STATUS = {}


def execute_in_node(host, user, ssh_key_filepath, input_file_path, wordlist_file_path, hashcat_command):
    remote_directory = remote = None
    try:
        PROCESS_STATUS[host] = "Started"
        remote_path = f"/home/{user}/"
        """Initialize remote host client and execute actions."""
        remote = RemoteClient(host, user, ssh_key_filepath, remote_path, logger)

        remote_directory = f"temp_hash_cat_{str(uuid.uuid4().hex)}"
        remote.remote_path = remote_directory
        create_temp_directory = f"mkdir {remote_directory}"

        remote.execute_commands([create_temp_directory])
        remote.bulk_upload([input_file_path, wordlist_file_path])

        """
        Create HashCat full command that redirects outputs to the out.log file.
        cd to the remote directory and execute the hashcat command.
        """
        input_file_name = os.path.basename(input_file_path)
        wordlist_file_name = os.path.basename(wordlist_file_path)
        hashcat_command = hashcat_command + f" {input_file_name} {wordlist_file_name}"
        hashcat_full_command = f"cd {remote_directory} && {hashcat_command} > out.log &"
        remote.execute_commands([hashcat_full_command], new_session=True)

        """
        Output file name created using input file name and word list file name.
        It will get the last 19 lines of out.log created by above command in remote and write to local output file.
        """
        result_file = f"{input_file_name}_{wordlist_file_name}.result"
        while True:
            time.sleep(20)
            output = remote.execute_commands([f"tail -n 19 {remote_directory}/out.log"])
            out = write_output(result_file, output)
            if "Stopped" in str(output[-1]).strip():
                # If the last line contains the Stopped string, It means the process has finished.
                break
        if is_hash_recovered(out):
            output = remote.execute_commands([f"cd {remote_directory} && {hashcat_command} --show"])
            output.insert(0, "------------------------Output----------------------")
            write_output(result_file, output, mode="a")
            logger.info(f"process completed in Host={host}, Input File={input_file_name},"
                        f" Dictionary File={wordlist_file_name}, OUTPUT File={result_file}, RESULT=Hash Recovered")
        else:
            logger.info(f"process completed in Host={host}, Input File={input_file_name},"
                        f" Dictionary File={wordlist_file_name}, OUTPUT File={result_file}, RESULT=Hash not Recovered")
        PROCESS_STATUS[host] = "Completed"
    except Exception as ex:
        PROCESS_STATUS[host] = "Error"
        logger.error(f"error={str(ex)}")
    finalize(remote_directory, remote)


def is_validate_arguments(arguments):
    valid = True
    if len(arguments.hosts) != len(arguments.users):
        print("The length of hosts and users should match.")
        valid = False
    if not os.path.isfile(arguments.ssh_key_filepath):
        print("ssh key file not found.")
        valid = False
    if not os.path.isfile(arguments.input_file):
        print("input file not found.")
        valid = False
    for each_file in arguments.word_list:
        if not os.path.isfile(each_file):
            print(f"word dictionary file {each_file} not found.")
            valid = False
    return valid


def main():
    arguments = parse_argument()
    if not is_validate_arguments(arguments):
        return
    initialize(logger=logger)
    iterator = arguments.hosts if len(arguments.hosts) < len(arguments.word_list) else arguments.word_list
    for index in range(len(iterator)):
        process = Thread(target=execute_in_node, args=[
            arguments.hosts[index],
            arguments.users[index],
            arguments.ssh_key_filepath,
            arguments.input_file,
            arguments.word_list[index],
            arguments.hashcat_command
        ])
        process.start()
    if len(arguments.host) < len(arguments.word_list) and arguments.use_self:
        # TODO: Run in current machine.
        pass

    while True:
        if "Started" not in PROCESS_STATUS.values():
            break
        print(PROCESS_STATUS.values())
        time.sleep(5)


if __name__ == '__main__':
    main()
