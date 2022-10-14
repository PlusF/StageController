import serial


class MySerial(serial.Serial):
    eol = b'\r'
    leneol = len(eol)
    def __init__(self, port, baudrate, **args):
        super().__init__(port, baudrate, **args)

    def send(self, msg: str):
        msg = msg.encode() + self.eol
        self.write(msg)

    def recv(self):
        line = bytearray()
        while True:
            c = self.read(1)
            if c:
                line += c
                if line[-self.leneol:] == self.eol:
                    break
            else:
                break
        return bytes(line).decode().strip('\r')


def axis2msg(axis: str):
    if axis not in ['x', 'y']:
        raise ValueError('Axis must be x or y.')
    msg = 'AXIs'
    if axis == 'x':
        msg += '1'
    elif axis == 'y':
        msg += '2'
    msg += ':'
    return msg


class DS102Controller:
    def __init__(self, ser: MySerial):
        self.ser = ser
        # 送受信とステータスの確認
        self.ser.send('AXIs1:READY?')
        print(f'X axis: {"READY" if self.ser.recv() == 1 else "NOT READY"}')
        self.ser.send('AXIs2:READY?')
        print(f'Y axis: {"READY" if self.ser.recv() == 1 else "NOT READY"}')

    def set_velocity(self, axis: str, vel: int):
        msg = axis2msg(axis) + f'Fspeed0 {vel}'
        self.ser.send(msg)

    def select_speed(self, axis: str, speed: int):
        msg = axis2msg(axis) + f'SELectSPeed {speed}'
        self.ser.send(msg)

    def speed_is(self, axis: str, speed: int) -> bool:
        msg = axis2msg(axis) + 'SELectSPeed?'
        self.ser.send(msg)
        msg = self.ser.recv()
        if msg == str(speed):
            return True
        else:
            print('selected speed:', msg)
            return False

    def move_velocity(self, axis: str, vel: int):
        self.set_velocity(axis, abs(vel))
        if not self.speed_is(axis, 0):
            self.select_speed(axis, 0)

        msg = axis2msg(axis) + 'GO '
        if vel > 0:
            msg += '5'
        else:
            msg += '6'
        self.ser.send(msg)

    def stop_axis(self, axis: str):
        msg = axis2msg(axis) + 'STOP_Emergency'
        # msg = axis2msg(axis) + 'STOP_Reduction'
        self.ser.send(msg)

    def stop(self):
        msg = 'STOP_Emergency'
        # msg = 'STOP_Reduction'
        self.ser.send(msg)

    def get_position(self):
        msg = axis2msg('x') + 'POSition?'
        self.ser.send(msg)
        pos_x = int(self.ser.recv())
        msg = axis2msg('y') + 'POSition?'
        self.ser.send(msg)
        pos_y = int(self.ser.recv())
        return pos_x, pos_y
