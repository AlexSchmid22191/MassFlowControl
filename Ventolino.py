from serial import Serial


class Ventolino(Serial):
    def __init__(self, port=None, channels=4):
        super().__init__(port, timeout=1)
        self.port = port
        self.channels = channels

        self.set_flows = [0.0]*4
        self.is_flows = [0.0]*4

    def connect(self, port=None):
        if port:
            self.port = port
        self.open()

    def disconnect(self):
        self.close()

    def set_flow(self, channel, flow):
        """Set desired flow"""
        if 0 <= flow <= 100 and 1 <= channel <= 4:
            string = '{:02d}SFD{:3.1f}'.format(channel, flow)
            self.write(b'\x02')
            self.write(string.encode())
            self.write(b'\x0D')

    def read_is_flow(self, channel):
        if 1 <= channel <= 4:
            string = '{:02d}RFX'.format(channel)
            self.write(b'\x02')
            self.write(string.encode())
            self.write(b'\x0D')

            answer = float(self.readline().decode())
            self.is_flows[channel - 1] = answer

    def read_set_flow(self, channel):
        if 1 <= channel <= 4:
            string = '{:02d}RFD'.format(channel)
            self.write(b'\x02')
            self.write(string.encode())
            self.write(b'\x0D')

            answer = float(self.readline().decode())
            self.set_flows[channel - 1] = answer

    def read_all_channels_is(self):
        for channel in range(self.channels):
            self.read_is_flow(channel + 1)

    def read_all_channels_set(self):
        for channel in range(self.channels):
            self.read_set_flow(channel + 1)
