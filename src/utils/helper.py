import logging.handlers
import sys
import os
import re
import json


def initialize(logger):
    logger.setLevel(logging.INFO)
    file_handler = logging.handlers.RotatingFileHandler("hash_cluster.log", mode="w", maxBytes=1000000, backupCount=20)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    if not os.path.exists("OUTPUT"):
        os.mkdir("OUTPUT")


def write_output(filename, output, mode="w"):
    """
    :param mode: Output File Mode
    :param filename: Output File Name
    :param output: Result of tail -n 19 from out.log created by hashcat command.
    It will removes extra next lines and spaces and write to output file. It will override the output file each time.
    """
    out = "\n".join(x.strip() for x in output if len(x.strip()) > 0)
    with open(os.path.join("OUTPUT", filename), mode) as fh:
        fh.write(out)
    return out


def finalize(remote_directory, remote):
    """
    :param remote_directory: Temporary path created for processing
    :param remote: SSH Client
    This will delete the temporary path in remote and disconnect the ssh client.
    """
    try:
        if remote and remote.conn and remote_directory:
            delete_temp_directory = "rm -rf {}".format(remote_directory)
            remote.execute_commands([delete_temp_directory])
            remote.disconnect()
    except:
        pass


def is_hash_recovered(out):
    recovered_count = re.findall(r'Recovered\.*:\s([\d]+).*', out)
    if len(recovered_count) > 0 and int(recovered_count[0]) > 0:
        return True
    return False


def is_file_exist(filepath):
    if os.path.exists(filepath):
        return True
    return False


def check_if_all_fields_are_available(formatted_data):
    for each_row in formatted_data:
        if None in each_row.values():
            raise Exception(f"Input error in row={each_row}")

        if not is_file_exist(each_row["input_file"]):
            raise Exception(f"input file not found: {each_row['input_file']} for host={each_row['host']}")
        if not is_file_exist(each_row["dictionary"]):
            raise Exception(f"dictionary file not found: {each_row['dictionary']} for host={each_row['host']}")
        if not is_file_exist(each_row["ssh_key_filepath"]):
            raise Exception(f"ssh_key_filepath file not found: {each_row['ssh_key_filepath']} for host={each_row['host']}")


def read_input_file(input_file):
    with open(input_file) as fh:
        data = json.load(fh)

    formatted_data = []
    global_data = data["global"]
    hosts = data["hosts"]
    for each_host in hosts:
        formatted_data.append(
            {
                "host": each_host["ip"],
                "user": each_host.get("user") or global_data.get("user"),
                "ssh_key_filepath": each_host.get("ssh_key_filepath") or global_data.get("ssh_key_filepath"),
                "input_file": each_host.get("input_file") or global_data.get("input_file"),
                "dictionary": each_host.get("dictionary"),
                "hashcat_command": each_host.get("hashcat_command") or global_data.get("hashcat_command"),
            }
        )
    check_if_all_fields_are_available(formatted_data=formatted_data)
    return formatted_data
