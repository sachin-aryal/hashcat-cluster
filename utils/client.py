"""Client to handle connections and actions executed against a remote host."""
from os import system
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.auth_handler import AuthenticationException, SSHException
from scp import SCPClient, SCPException


class RemoteClient:
    """Client to interact with a remote host via SSH & SCP."""

    def __init__(self, host, user, ssh_key_filepath, remote_path, logger):
        self.host = host
        self.user = user
        self.ssh_key_filepath = ssh_key_filepath
        self.remote_path = remote_path
        self.client = None
        self.scp = None
        self.conn = None
        self.logger = logger
        # self._upload_ssh_key()

    def _get_ssh_key(self):
        """
        Fetch locally stored SSH key.
        """
        try:
            self.ssh_key = RSAKey.from_private_key_file(self.ssh_key_filepath)
            self.logger.debug(f'Found SSH key at self {self.ssh_key_filepath}')
        except SSHException as error:
            self.logger.error(error)
        return self.ssh_key

    def _upload_ssh_key(self):
        try:
            system(f'ssh-copy-id -i {self.ssh_key_filepath} {self.user}@{self.host}>/dev/null 2>&1')
            system(f'ssh-copy-id -i {self.ssh_key_filepath}.pub {self.user}@{self.host}>/dev/null 2>&1')
            self.logger.debug(f'{self.ssh_key_filepath} uploaded to {self.host}')
        except FileNotFoundError as error:
            self.logger.error(error)

    def _connect(self):
        """
        Open connection to remote host.
        """
        if self.conn is None:
            self.logger.info(f"connecting {self.host} ")
            try:
                self.client = SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(AutoAddPolicy())
                self.client.connect(self.host,
                                    username=self.user,
                                    key_filename=self.ssh_key_filepath,
                                    look_for_keys=True,
                                    timeout=5000)
                self.scp = SCPClient(self.client.get_transport(), socket_timeout=3600)
            except AuthenticationException as error:
                self.logger.info('Authentication failed: did you remember to create an SSH key?')
                self.logger.error(error)
                raise error
            self.logger.info(f"connected successfully to {self.host}.")
        return self.client

    def disconnect(self):
        """
        Close ssh connection.
        """
        self.client.close()
        self.scp.close()

    def bulk_upload(self, files):
        """
        Upload multiple files to a remote directory.

        :param files: List of strings representing file paths to local files.
        """
        self.conn = self._connect()
        uploads = [self._upload_single_file(file) for file in files]
        self.logger.debug(f'Finished uploading {len(uploads)} files to {self.remote_path} on {self.host}')

    def _upload_single_file(self, file):
        """Upload a single file to a remote directory."""
        try:
            self.scp.put(file,
                         recursive=False,
                         remote_path=self.remote_path)
        except SCPException as error:
            self.logger.error(error)
            raise error
        finally:
            self.logger.info(f'Uploaded {file} to {self.remote_path}')

    def download_file(self, file):
        """Download file from remote host."""
        self.conn = self._connect()
        self.scp.get(file)

    def execute_commands(self, commands, new_session=False):
        """
        Execute multiple commands in succession.

        :param commands: List of unix commands as strings.
        """
        self.conn = self._connect()
        for cmd in commands:
            self.logger.info(f'Executing Command: {cmd}')
            if new_session:
                transport = self.client.get_transport()
                channel_hashcat = transport.open_session()
                channel_hashcat.exec_command(cmd)  # will return instantly due to new thread being spawned.
            else:
                stdin, stdout, stderr = self.client.exec_command(cmd)
                stdout.channel.recv_exit_status()
                response = stdout.readlines()
                if "tail" in cmd or "--show" in cmd:
                    return [line for line in response]
                else:
                    for line in response:
                        self.logger.debug(f'INPUT: {cmd} | OUTPUT: {line}')
