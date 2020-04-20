import argparse
import os

from src import execute


def parse_argument():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input_file', help="Input Json File", required=True, type=str)
    parser.add_argument('-b', '--in_background', help="Should the process be started in background", required=False, type=bool,
                        default=False)
    args = parser.parse_args()
    return args


def main():
    arguments = parse_argument()
    if not os.path.exists(arguments.input_file):
        print("input file not found.")
        return
    execute.execute(arguments.input_file)


if __name__ == '__main__':
    main()
