from threading import Lock
from pubsub.pub import subscribe, sendMessage
from serial import Serial, SerialException
from ThreadDecorators import in_new_thread


class Ventolino(Serial):
    """Driver class for Ventolino MFC controllers, uses Pubsub to communicate with GUI"""
    def __init__(self, port=None, channels=4, timeout=1):
        super().__init__(port, timeout=timeout)
        self.port = port
        self.channels = channels

        self.com_lock = Lock()

        self.set_flows = [0.0]*channels
        self.is_flows = [0.0]*channels

        subscribe(self.connect, 'GTE_connect')

    def connect(self, port=None):
        """Connect to serial port, emmit success/error message"""
        if port:
            self.port = port
        try:
            self.open()
            sendMessage(topicName='ETG_status', text='Ventolino connected')

            subscribe(self.disconnect, 'GTE_disconnect')
            subscribe(self.set_flow, 'GTE_set_flow')
            subscribe(self.read_is_flow, 'GTE_read_is_flow')
            subscribe(self.read_set_flow, 'GTE_read_set_flow')
            subscribe(self.read_all_channels_is, 'GTE_read_all_channels_is')
            subscribe(self.read_all_channels_set, 'GTE_read_all_channels_set')

        except SerialException:
            sendMessage(topicName='ETG_status', text='Serial connection error')

    def disconnect(self):
        with self.com_lock:
            self.close()
            sendMessage(topicName='ETG_status', text='Ventolino disconnected')

    @in_new_thread
    def set_flow(self, channel, flow):
        """Set desired flow"""

        assert 0 <= flow <= 100 and 1 <= channel <= self.channels, 'Invalid channel or flow'

        string = '{:02d}SFD{:3.1f}'.format(channel, flow)

        with self.com_lock:
            try:
                self.write(b'\x02')
                self.write(string.encode())
                self.write(b'\x0D')

                answer = self.readline()

                if answer == b'rec\n':
                    sendMessage('ETG_status', text='Channel {:1d} set to {:4.1f} %.'.format(channel, flow))
                else:
                    sendMessage('ETG_status', text='Ventolino not answering')

            except (ValueError, SerialException):
                sendMessage(topicName='ETG_status', text='Serial communication error!')

    @in_new_thread
    def read_is_flow(self, channel):
        """Read flow, emit message with flow value or status message with error"""
        assert 1 <= channel <= self.channels, 'Invalid channel'

        string = '{:02d}RFX'.format(channel)

        with self.com_lock:
            try:
                self.write(b'\x02')
                self.write(string.encode())
                self.write(b'\x0D')

                answer = self.readline()
                self.is_flows[channel - 1] = float(answer.decode())
                sendMessage(topicName='ETG_read_is_flow', channel=channel, flow=self.is_flows[channel - 1])

            except (ValueError, SerialException):
                sendMessage(topicName='ETG_status', text='Serial communication error!')

    @in_new_thread
    def read_set_flow(self, channel):
        assert 1 <= channel <= self.channels, 'Invalid channel'

        string = '{:02d}RFD'.format(channel)

        with self.com_lock:
            try:
                self.write(b'\x02')
                self.write(string.encode())
                self.write(b'\x0D')

                answer = self.readline()
                self.set_flows[channel - 1] = float(answer.decode())
                sendMessage(topicName='ETG_read_set_flow', channel=channel, flow=self.set_flows[channel - 1])

            except (ValueError, SerialException):
                sendMessage(topicName='ETG_status', text='Serial communication error!')

    def read_all_channels_is(self):
        for channel in range(self.channels):
            self.read_is_flow(channel + 1)

    def read_all_channels_set(self):
        for channel in range(self.channels):
            self.read_set_flow(channel + 1)
