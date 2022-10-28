import json


class ConfigLoader:
    def __init__(self, filename):
        with open(filename, 'r') as f:
            config = json.load(f)
        self.mode = config['mode']
        self.dt = int(1000 / config['FPS'])
        self.port_xy = f'COM{config["PORT-xy"]}'
        self.port_z = f'COM{config["PORT-z"]}'
        self.baudrate_xy = config["BAUDRATE-xy"]
        self.vel_list_xy = config["VELLIST-xy"]
        self.vel_list_z = config["VELLIST-z"]


def main():
    cl = ConfigLoader('./config.json')
    print(cl.mode)


if __name__ == '__main__':
    main()
