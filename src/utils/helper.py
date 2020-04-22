import logging.handlers
import sys
import os
import re
import json
import subprocess
import shutil

from shlex import split as shlex_split

logger = logging.getLogger("Logger")


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


def write_output(filename, out, mode="w"):
    """
    :param mode: Output File Mode
    :param filename: Output File Name
    :param output: Result of tail -n 19 from out.log created by hashcat command.
    It will removes extra next lines and spaces and write to output file. It will override the output file each time.
    """
    if mode == "w":
        out = "\n".join(x.strip() for x in out if len(x.strip()) > 0)
    else:
        out = "\n".join(x for x in out)
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


def split_files(dictionary_file, chunks):
    temp_dir = f"temp_{os.path.basename(dictionary_file)}"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)
    os.chdir(temp_dir)
    subprocess.Popen(shlex_split(f"gsplit -n {str(chunks)} {dictionary_file}")).communicate()
    os.chdir("../")
    return temp_dir


def input_validation_and_finalization(formatted_data):
    host_dictionary = {}
    for each_row in formatted_data:
        if None in each_row.values():
            raise Exception(f"Input error in row={each_row}")

        if not is_file_exist(each_row["input_file"]):
            raise Exception(f"input file not found: {each_row['input_file']} for host={each_row['host']}")
        if not is_file_exist(each_row["dictionary"]):
            raise Exception(f"dictionary file not found: {each_row['dictionary']} for host={each_row['host']}")
        if not is_file_exist(each_row["ssh_key_filepath"]):
            raise Exception(f"ssh_key_filepath file not found: {each_row['ssh_key_filepath']} for host={each_row['host']}")
        entry = host_dictionary.get(each_row["dictionary"], [])
        entry.append(each_row["host"])
        host_dictionary[each_row["dictionary"]] = entry

    host_dictionary_mapping = {}
    same_dictionaries = {key: val for key, val in host_dictionary.items() if len(val) > 1}
    for dictionary, hosts in same_dictionaries.items():
        logger.info(f"split dictionary {dictionary} in {len(hosts)} parts.")
        split_file_directory = split_files(dictionary, len(hosts))
        file_list = os.listdir(split_file_directory)
        for i, each_host in enumerate(hosts):
            host_dictionary_mapping[each_host] = os.path.join(split_file_directory, file_list[i])
    for each_row in formatted_data:
        if each_row["host"] in host_dictionary_mapping:
            each_row["dictionary"] = host_dictionary_mapping[each_row["host"]]


def read_input_file(input_file):
    with open(input_file) as fh:
        data = json.load(fh)

    formatted_data = []
    global_data = data["global"]
    hosts = data["hosts"]
    ip_list = []
    for each_host in hosts:
        if each_host["ip"] in ip_list:
            raise Exception(f"Duplicate host not allowed;ip={each_host['ip']}")
        ip_list.append(each_host["ip"])
        formatted_data.append(
            {
                "host": each_host["ip"],
                "user": each_host.get("user") or global_data.get("user"),
                "ssh_key_filepath": each_host.get("ssh_key_filepath") or global_data.get("ssh_key_filepath"),
                "input_file": each_host.get("input_file") or global_data.get("input_file"),
                "dictionary": each_host.get("dictionary") or global_data.get("dictionary"),
                "hashcat_command": each_host.get("hashcat_command") or global_data.get("hashcat_command"),
            }
        )
    input_validation_and_finalization(formatted_data=formatted_data)
    print(formatted_data)
    return formatted_data
