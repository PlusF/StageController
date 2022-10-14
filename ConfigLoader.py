import json


class ConfigLoader:
    def __init__(self, filename):
        with open(filename, 'r') as f:
            config = json.load(f)
        self.mode = config['mode']
        self.dt = int(1000 / config['FPS'])
        self.port_x = f'COM{config["PORT-x"]}'
        self.port_y = f'COM{config["PORT-y"]}'
        self.port_z = f'COM{config["PORT-z"]}'
        self.baudrate_x = config["BAUDRATE-x"]
        self.baudrate_y = config["BAUDRATE-y"]


def main():
    cl = ConfigLoader('./config.json')
    print(cl.mode)


if __name__ == '__main__':
    main()
