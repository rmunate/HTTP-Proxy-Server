class Port:

    @staticmethod
    def isAvailable(host: str, port: int) -> bool:
        """
        Check if a TCP port is available for binding on the specified host.

        Parameters
        ----------
        host : str
            The hostname or IP address to check.
        port : int
            The TCP port number to check.

        Returns
        -------
        bool
            True if the port is available for binding, False otherwise.
        """
        import socket

        # Attempt to bind to the specified host and port to check availability.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False