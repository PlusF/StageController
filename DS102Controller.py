import serial


class MySerial(serial.Serial):
    # serial.SerialではEOLが\nに設定されており、DS102の規格と異なる
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
    """
    convert axis to 'AXIs<axis>:'
    :param axis: 'x' or 'y'
    :type axis: str
    :rtype: str
    :return: message string
    """
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
        """
        initialization
        :param ser: opened port for communication
        :type ser: MySerial
        """
        self.ser = ser
        # 送受信とステータスの確認
        self.ser.send('AXIs1:READY?')
        print(f'X axis: {"READY" if self.ser.recv() == "1" else "NOT READY"}')
        self.ser.send('AXIs2:READY?')
        print(f'Y axis: {"READY" if self.ser.recv() == "1" else "NOT READY"}')

    def set_velocity(self, axis: str, vel: int):
        """
        set Fspeed0 vel
        :param axis: 'x' or 'y'
        :param vel: velocity you want to set
        :type axis: str
        :type vel: int
        :return:
        """
        msg = axis2msg(axis) + f'Fspeed0 {vel}'
        self.ser.send(msg)

    def select_speed(self, axis: str, speed: int):
        """
        select set of speed from 0~9
        :param axis: 'x' or 'y'
        :param speed: number(0~9) of the set you want to select
        :type axis: str
        :type speed: int
        :return:
        """
        msg = axis2msg(axis) + f'SELectSPeed {speed}'
        self.ser.send(msg)

    def speed_is(self, axis: str, speed: int) -> bool:
        """
        check the selected speed
        :param axis: 'x' or 'y'
        :param speed: number(0~9) of the set
        :type axis: str
        :type speed: int
        :rtype: bool
        :return: True or False
        """
        msg = axis2msg(axis) + 'SELectSPeed?'
        self.ser.send(msg)
        msg = self.ser.recv()
        if msg == str(speed):
            return True
        else:
            print('selected speed:', msg)
            return False

    def move_velocity(self, axis: str, vel: int):
        """
        move along selected axis with selected velocity
        :param axis: 'x' or 'y'
        :param vel: velocity
        :type axis: str
        :type vel: int
        :return:
        """
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
        """
        stop each axis
        Emergency( or Reduction)
        :param axis: 'x' or 'y'
        :type axis: str
        :return:
        """
        msg = axis2msg(axis) + 'STOP Emergency'
        # msg = axis2msg(axis) + 'STOP Reduction'
        self.ser.send(msg)

    def stop(self):
        """
        stop all
        :return:
        """
        msg = 'STOP Emergency'
        # msg = 'STOP Reduction'
        self.ser.send(msg)

    def get_position(self):
        """
        get x and y position
        the unit is mm
        :rtype (int, int)
        :return: x position, y position
        """
        msg = axis2msg('x') + 'POSition?'
        self.ser.send(msg)
        pos_x = int(float(self.ser.recv()) * 1000)
        msg = axis2msg('y') + 'POSition?'
        self.ser.send(msg)
        pos_y = int(float(self.ser.recv()) * 1000)
        return pos_x, pos_y

    def get_position_request(self):
        """
        send a request to get x and y position
        :rtype (int, int)
        :return:
        """
        msg = axis2msg('x') + 'POSition?'
        self.ser.send(msg)
        msg = axis2msg('y') + 'POSition?'
        self.ser.send(msg)
