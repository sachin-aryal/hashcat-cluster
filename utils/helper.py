import logging.handlers
import sys
import os
import argparse
import re


def initialize(logger):
    logger.setLevel(logging.INFO)
    file_handler = logging.handlers.RotatingFileHandler("info.log", mode="w", maxBytes=1000000, backupCount=20)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    if not os.path.exists("OUTPUT"):
        os.mkdir("OUTPUT")


def parse_argument():
    parser = argparse.ArgumentParser()

    parser.add_argument('-hs', '--hosts', nargs='+', help="list of working hosts. ", required=True, type=str)
    parser.add_argument('-u', '--users', nargs='+', help="list of host users in same order as host.", required=True,
                        type=str)
    parser.add_argument('-s', '--ssh_key_filepath', help="path of current machine's private key.", required=True,
                        type=str)
    parser.add_argument('-i', '--input_file', help="Path of input file.", required=True, type=str)
    parser.add_argument('-w', '--word_list', nargs='+', help="path of list of word dictionary.", required=True,
                        type=str)
    parser.add_argument('-hc', '--hashcat_command', help="hashcat command without input and word dictionary parameter",
                        required=True, type=str)
    parser.add_argument('-us', '--use_self', help="use the current machine for processing.",
                        required=False, type=bool, default=False)
    args = parser.parse_args()
    return args


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
        delete_temp_directory = "rm -rf {}".format(remote_directory)
        remote.execute_commands([delete_temp_directory])
        remote.disconnect()
    except:
        pass


def is_hash_recovered(out):
    recovered_count = re.findall(r'Recovered.*:\s([\d]+).*', out)
    if len(recovered_count) > 0:
        count = int(recovered_count[0])
        if count == 0:
            return False
    return True
