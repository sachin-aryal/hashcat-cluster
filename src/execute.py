#!/usr/bin/env python

import uuid
import time
import subprocess
from shlex import split as shlex_split
from src.utils.client import RemoteClient
from src.utils.helper import *
from threading import Thread


logger = logging.getLogger("Logger")

PROCESS_STATUS = {}


def __execute_in_current_machine(input_file_path, dictionary_file_path, hashcat_command):
    dictionary_file = os.path.basename(dictionary_file_path)
    PROCESS_STATUS[f"CURRENT_{dictionary_file}"] = "Started"
    input_file_name = os.path.basename(input_file_path)
    try:
        hashcat_command = hashcat_command + f" {input_file_path} {dictionary_file_path}"
        result_file = f"CURRENT_{input_file_name}_{dictionary_file}.result"
        sp_hashcat_cmd = shlex_split(hashcat_command)
        with open(f"OUTPUT/{result_file}", "w") as rf:
            subprocess.Popen(sp_hashcat_cmd, stdout=rf).communicate()

        proc = subprocess.Popen(["tail", "-n", "19", f"OUTPUT/{result_file}"], stdout=subprocess.PIPE)
        out, err = proc.communicate()
        if out:
            if is_hash_recovered(str(out)):
                sp_hashcat_cmd.append("--show")
                proc = subprocess.Popen(sp_hashcat_cmd, stdout=subprocess.PIPE)
                output, err = proc.communicate()
                if output:
                    output = str(output).splitlines()
                    output.insert(0, "------------------------Output----------------------")
                    write_output(result_file, output, mode="a")
                    logger.info(f"process completed in Host=CURRENT, Input File={input_file_name},"
                                f" Dictionary File={dictionary_file}, OUTPUT File={result_file}, RESULT=Hash Recovered")
            else:
                logger.info(f"process completed in Host=CURRENT, Input File={input_file_name},"
                            f" Dictionary File={dictionary_file}, OUTPUT File={result_file}, RESULT=Hash not Recovered")
        PROCESS_STATUS[f"CURRENT_{dictionary_file}"] = "Completed"
    except Exception as ex:
        import traceback
        traceback.print_exc()
        logger.error(f"error={str(ex)}")
        PROCESS_STATUS[f"CURRENT_{dictionary_file}"] = "Error"


def __execute_in_node(host, user, ssh_key_filepath, input_file_path, dictionary_file_path, hashcat_command):
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
        remote.bulk_upload([input_file_path, dictionary_file_path])

        """
        Create HashCat full command that redirects outputs to the out.log file.
        cd to the remote directory and execute the hashcat command.
        """
        input_file_name = os.path.basename(input_file_path)
        dictionary_file = os.path.basename(dictionary_file_path)
        hashcat_command = hashcat_command + f" {input_file_name} {dictionary_file}"
        hashcat_full_command = f"cd {remote_directory} && {hashcat_command} > out.log &"
        remote.execute_commands([hashcat_full_command], new_session=True)

        """
        Output file name created using input file name and word list file name.
        It will get the last 19 lines of out.log created by above command in remote and write to local output file.
        """
        result_file = f"{host}_{input_file_name}_{dictionary_file}.result"
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
                        f" Dictionary File={dictionary_file}, OUTPUT File={result_file}, RESULT=Hash Recovered")
        else:
            logger.info(f"process completed in Host={host}, Input File={input_file_name},"
                        f" Dictionary File={dictionary_file}, OUTPUT File={result_file}, RESULT=Hash not Recovered")
        PROCESS_STATUS[host] = "Completed"
    except Exception as ex:
        PROCESS_STATUS[host] = "Error"
        logger.error(f"error={str(ex)}")
    finalize(remote_directory, remote)


def execute(input_file):
    initialize(logger=logger)
    try:
        formatted_data = read_input_file(input_file)
    except Exception as ex:
        logger.error(str(ex))
        return
    for each_data in formatted_data:
        if each_data["host"] == "CURRENT":
            target = __execute_in_current_machine
            args = [
                each_data["input_file"],
                each_data["dictionary"],
                each_data["hashcat_command"]
            ]
        else:
            target = __execute_in_node
            args = [
                each_data["host"],
                each_data["user"],
                each_data["ssh_key_filepath"],
                each_data["input_file"],
                each_data["dictionary"],
                each_data["hashcat_command"]
            ]
        process = Thread(target=target, args=args)
        process.start()

    while True:
        print(PROCESS_STATUS)
        if "Started" not in PROCESS_STATUS.values():
            break
        time.sleep(20)
