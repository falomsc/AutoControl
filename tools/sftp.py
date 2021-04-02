import paramiko


class SftpConnection:
    def __init__(self, host: str, port: int, username: str, password: str):
        self._transport = paramiko.Transport((host, port))
        self._transport.connect(username=username, password=password)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    def get_file(self, remotepath, localpath):
        self._sftp.get(remotepath, localpath)

    def upload_file(self, localpath, remotepath):
        self._sftp.put(localpath, remotepath)

    def mkdir(self, path):
        self._sftp.mkdir(path)

    def rename(self, oldpath, newpath):
        self._sftp.rename(oldpath, newpath)

    def close(self):
        self._sftp.close()