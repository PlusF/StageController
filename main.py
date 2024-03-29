import os
import sys
import time
import copy
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from zaber_motion import Units, Library, LogOutputMode
from zaber_motion.binary import Connection
from ds102controller import MySerial, DS102Controller
from CustomTkObject import MovableOval, MovableRect
from ConfigLoader import ConfigLoader


# ライブラリをオフラインで使えるようにする
Library.enable_device_db_store()
# ログを取る
Library.set_log_output(LogOutputMode.FILE, "motion_library_log.txt")

WIDTH_BUTTON = 7
SIZE_CANVAS = 400
SIZE_CONT = 15
DT = 200
FONT = ('游ゴシック', 16)
MAX_Z = 25400.032


def get_color_by_float(value: float):
    codes = ['#222', '#333', '#444', '#555', '#666', '#777', '#888', '#999', '#aaa', '#bbb', '#ccc',
             '#ddd', '#eee', '#fff']
    value *= len(codes)
    for i, color in enumerate(codes):
        if value < i:
            return color


class Application(tk.Frame):
    def __init__(self, master=None, config='./config.json'):
        super().__init__(master)
        self.master.title('Stage Controller')

        # フォントサイズの調整
        self.style = ttk.Style()
        if os.name == 'nt':
            self.style.theme_use('winnative')  # windowsにしかないテーマ
        self.style.configure('.', font=FONT)
        self.style.configure("stop.TButton", activeforeground='red', foreground='red')

        self.cl = ConfigLoader(config)
        if self.cl.dt is not None:
            self.dt = self.cl.dt
        else:
            self.dt = DT

        self.open_port()

        self.create_widgets()

        self.unit_pos = Units.LENGTH_MICROMETRES
        self.unit_vel = Units.VELOCITY_MICROMETRES_PER_SECOND

        self.rank_xy_pre = 0
        self.rank_z_pre = 0
        self.direction_xy_pre = [0, 0, 0]
        self.direction_z_pre = [0, 0, 0]

        self.create_thread()

        self.update()

    def open_port(self):
        if self.cl.mode == 'RELEASE':
            self.ser = MySerial(self.cl.port_xy, self.cl.baudrate_xy, write_timeout=0)
            self.device_xy = DS102Controller(self.ser)
            self.connection = Connection.open_serial_port(self.cl.port_z)
            self.device_z = self.connection.detect_devices()[0]
        elif self.cl.mode == 'DEBUG':
            self.ser = self.device_xy = self.connection = self.device_z = None
        else:
            raise ValueError('Wrong format in config.json. Mode must be DEBUG or RELEASE.')

    def create_widgets(self):
        # 親フレーム
        self.frame_xy = ttk.Frame(self.master)
        self.frame_z = ttk.Frame(self.master)
        self.frame_xy.grid(row=0, column=0)
        self.frame_z.grid(row=0, column=1)
        # 子フレーム
        self.frame_xy_canvas = ttk.Frame(self.frame_xy)
        self.frame_xy_buttons = ttk.Frame(self.frame_xy)
        self.frame_xy_position = ttk.Frame(self.frame_xy)
        self.frame_z_canvas = ttk.Frame(self.frame_z)
        self.frame_z_buttons = ttk.Frame(self.frame_z)
        self.frame_z_position = ttk.Frame(self.frame_z)
        self.frame_xy_canvas.grid(row=0, column=0, columnspan=2)
        self.frame_xy_buttons.grid(row=1, column=0)
        self.frame_xy_position.grid(row=2, column=0)
        self.frame_z_canvas.grid(row=0, column=0, columnspan=2)
        self.frame_z_buttons.grid(row=1, column=0)
        self.frame_z_position.grid(row=2, column=0)
        # ウィジェット xy_canvas
        self.canvas_xy = tk.Canvas(self.frame_xy_canvas, width=SIZE_CANVAS*0.9, height=SIZE_CANVAS)
        center = SIZE_CANVAS/2
        r_list = [SIZE_CONT*9, SIZE_CONT*7, SIZE_CONT*5, SIZE_CONT*3, SIZE_CONT*1]
        for i, r in enumerate(r_list):
            color = get_color_by_float(i / len(r_list))
            self.canvas_xy.create_oval(center - r, center - r, center + r, center + r, fill=color)
        MovableOval.canvas = self.canvas_xy
        MovableOval.thres_list = r_list
        self.oval_xy = MovableOval(center-SIZE_CONT, center-SIZE_CONT, center+SIZE_CONT, center+SIZE_CONT, fill='lightblue')
        self.canvas_xy.pack()
        # ウィジェット xy_buttons
        self.vel_xy = tk.IntVar(value=100)
        self.combobox_xy = ttk.Combobox(self.frame_xy_buttons, values=self.cl.vel_list_xy[1:], textvariable=self.vel_xy, justify='center', width=WIDTH_BUTTON)
        self.button_top = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='↑')
        self.button_left = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='←')
        self.button_right = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='→')
        self.button_bottom = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='↓')
        self.button_top.bind('<Button-1>', self.move_top)
        self.button_top.bind('<ButtonRelease-1>', self.stop_xy)
        self.button_left.bind('<Button-1>', self.move_left)
        self.button_left.bind('<ButtonRelease-1>', self.stop_xy)
        self.button_right.bind('<Button-1>', self.move_right)
        self.button_right.bind('<ButtonRelease-1>', self.stop_xy)
        self.button_bottom.bind('<Button-1>', self.move_bottom)
        self.button_bottom.bind('<ButtonRelease-1>', self.stop_xy)
        self.button_top.grid(row=0, column=1)
        self.button_left.grid(row=1, column=0)
        self.combobox_xy.grid(row=1, column=1)
        self.button_right.grid(row=1, column=2)
        self.button_bottom.grid(row=2, column=1)
        # ウィジェット xy_position
        self.x_cur = tk.DoubleVar(value=0)
        self.y_cur = tk.DoubleVar(value=0)
        self.label_x = ttk.Label(self.frame_xy_position, text='X [\u03bcm]')
        self.label_y = ttk.Label(self.frame_xy_position, text='Y [\u03bcm]')
        self.label_x_cur = ttk.Label(self.frame_xy_position, textvariable=self.x_cur)
        self.label_y_cur = ttk.Label(self.frame_xy_position, textvariable=self.y_cur)
        self.label_x.grid(row=0, column=0)
        self.label_x_cur.grid(row=0, column=1)
        self.label_y.grid(row=1, column=0)
        self.label_y_cur.grid(row=1, column=1)
        # ウィジェット z_canvas
        self.canvas_z = tk.Canvas(self.frame_z_canvas, width=SIZE_CANVAS/2, height=SIZE_CANVAS)
        xmin = SIZE_CANVAS * 0.1
        xmax = SIZE_CANVAS * 0.4
        y_list = [SIZE_CONT*11, SIZE_CONT*9, SIZE_CONT*7, SIZE_CONT*5, SIZE_CONT*3, SIZE_CONT*1]
        for i, y in enumerate(y_list):
            color = get_color_by_float(i / len(y_list))
            self.canvas_z.create_rectangle(xmin, SIZE_CANVAS/2-y, xmax, SIZE_CANVAS/2+y, fill=color)
        MovableRect.canvas = self.canvas_z
        MovableRect.thres_list = y_list
        self.rect_z = MovableRect(xmin, SIZE_CANVAS/2-SIZE_CONT, xmax, SIZE_CANVAS/2+SIZE_CONT, fill='lightblue')
        self.canvas_z.pack()
        # ウィジェット z_buttons
        self.vel_z = tk.DoubleVar(value=100)
        self.combobox_z = ttk.Combobox(self.frame_z_buttons, values=self.cl.vel_list_z[1:], textvariable=self.vel_z, justify='center', width=WIDTH_BUTTON)
        self.button_up = ttk.Button(self.frame_z_buttons, width=WIDTH_BUTTON, text='UP')
        self.button_down = ttk.Button(self.frame_z_buttons, width=WIDTH_BUTTON, text='DOWN')
        self.button_up.bind('<Button-1>', self.move_up)
        self.button_up.bind('<ButtonRelease-1>', self.stop_z)
        self.button_down.bind('<Button-1>', self.move_down)
        self.button_down.bind('<ButtonRelease-1>', self.stop_z)
        self.button_up.grid(row=0, column=0)
        self.combobox_z.grid(row=1, column=0)
        self.button_down.grid(row=2, column=0)
        # ウィジェット z_position
        self.z_cur = tk.DoubleVar(value=0)
        self.label_z = ttk.Label(self.frame_z_position, text='Z [\u03bcm]')
        self.label_z_cur = ttk.Label(self.frame_z_position, textvariable=self.z_cur)
        self.label_z.grid(row=0, column=0)
        self.label_z_cur.grid(row=0, column=1)

        self.button_stop = ttk.Button(self.master, text='STOP ALL STAGES', command=self.stop_all, style='stop.TButton')
        self.button_stop.grid(row=2, columnspan=2)

        self.button_quit = ttk.Button(self.master, text='QUIT', command=self.quit, style='stop.TButton')
        self.button_quit.grid(row=3, columnspan=2)
        self.label_quit = ttk.Label(self.master, text='必ずQUITボタンからプログラムを終了してください\nサンプルを外してから終了してください。')
        self.label_quit.grid(row=4, columnspan=2)

    def create_thread(self):
        # update_positionの受信待ちで画面がフリーズしないようthreadを立てる
        self.thread = threading.Thread(target=self.update_position)
        self.thread.daemon = True
        self.thread.start()

    def quit(self):
        if messagebox.askyesno('確認', 'ステージが定位置へと移動します。'):
            # 定位置に戻る & openしているポートをcloseする。
            if self.cl.mode == 'RELEASE':
                self.device_z.move_absolute(9000, unit=Units.LENGTH_MICROMETRES)
                self.ser.close()
                self.connection.close()
            self.master.destroy()
            sys.exit()  # デーモン化してあるスレッドはここで死ぬ

    def update(self):
        # 動く or 止まる
        self.check_and_move()
        self.check_and_stop()
        # previous変数を更新
        self.rank_xy_pre = self.oval_xy.get_rank()
        self.rank_z_pre = self.rect_z.get_rank()
        self.direction_xy_pre = copy.copy(self.oval_xy.get_direction())
        self.direction_z_pre = copy.copy(self.rect_z.get_direction())

        self.master.after(self.dt, self.update)

    def check_and_move(self):
        # 図形から操作された場合を検知
        # XY方向
        if self.rank_xy_pre != self.oval_xy.get_rank() or self.direction_xy_pre != self.oval_xy.get_direction():
            # バグで方向が転換できないことがあるので、一度止めるようにする
            if self.direction_xy_pre != self.oval_xy.get_direction():
                self.stop_xy()
            if self.oval_xy.direction[0] > 0:
                self.move_right()
            elif self.oval_xy.direction[0] < 0:
                self.move_left()
            if self.oval_xy.direction[1] > 0:
                self.move_top()
            elif self.oval_xy.direction[1] < 0:
                self.move_bottom()
        # Z方向
        if self.rank_z_pre != self.rect_z.get_rank() or self.direction_z_pre != self.rect_z.get_direction():
            if self.rect_z.direction[2] > 0:
                self.move_up()
            elif self.rect_z.direction[2] < 0:
                self.move_down()

    def check_and_stop(self):
        # 前回までは動く命令、今回止まる命令が出ていればstopを呼び出す
        if self.rank_xy_pre != 0 and self.oval_xy.get_rank() == 0:
            self.stop_xy()
        if self.rank_z_pre != 0 and self.rect_z.get_rank() == 0:
            self.stop_z()

    def move_up(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = self.cl.vel_list_z[self.rect_z.get_rank()]
        else:
            vel = self.vel_z.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move up by {vel} \u03bcm/s')
        else:
            self.device_z.move_velocity(vel, unit=self.unit_vel)

    def move_down(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = -self.cl.vel_list_z[self.rect_z.get_rank()]
        else:
            vel = -self.vel_z.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move down by {vel} \u03bcm/s')
        else:
            self.device_z.move_velocity(vel, unit=self.unit_vel)

    def move_right(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = self.cl.vel_list_xy[self.oval_xy.get_rank()]
        else:
            vel = self.vel_xy.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move right by {vel} \u03bcm/s')
        else:
            self.device_xy.move_velocity('x', vel)

    def move_left(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = -self.cl.vel_list_xy[self.oval_xy.get_rank()]
        else:
            vel = -self.vel_xy.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move left by {vel} \u03bcm/s')
        else:
            self.device_xy.move_velocity('x', vel)

    def move_top(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = self.cl.vel_list_xy[self.oval_xy.get_rank()]
        else:
            vel = self.vel_xy.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move top by {vel} \u03bcm/s')
        else:
            self.device_xy.move_velocity('y', vel)

    def move_bottom(self, event=None):
        # event is None: 図形操作から呼ばれた
        if event is None:
            vel = -self.cl.vel_list_xy[self.oval_xy.get_rank()]
        else:
            vel = -self.vel_xy.get()

        if vel == 0:
            return

        if self.cl.mode == 'DEBUG':
            print(f'move bottom by {vel} \u03bcm/s')
        else:
            self.device_xy.move_velocity('y', vel)

    def stop_xy(self, event=None):
        # xy方向に停止命令を出す
        if self.cl.mode == 'DEBUG':
            print('stop xy')
        else:
            self.device_xy.stop()

    def stop_z(self, event=None):
        # z方向に停止命令を出す
        if self.cl.mode == 'DEBUG':
            print('stop z')
        else:
            self.device_z.stop()

    def stop_all(self):
        self.stop_xy()
        self.stop_z()

    def update_position(self):
        # 現在位置を更新
        # シリアル通信で受信する必要があるため，mainloopとは別threadで処理する．
        while True:
            if self.cl.mode == 'DEBUG':
                self.x_cur.set(self.x_cur.get() + 1)
                self.y_cur.set(self.y_cur.get() + 1)
                self.z_cur.set(self.z_cur.get() + 1)
            else:
                x, y = self.device_xy.get_position()
                z = MAX_Z - self.device_z.get_position(unit=self.unit_pos)
                self.x_cur.set(round(x, 0))
                self.y_cur.set(round(y, 0))
                self.z_cur.set(round(z, 3))
            time.sleep(self.dt * 0.001)


def main():
    root = tk.Tk()
    root.option_add("*font", FONT)  # こうしないとコンボボックスのフォントが変わらない
    root.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())  # QUITボタン以外の終了操作を許可しない
    app = Application(master=root, config='./config.json')
    app.mainloop()

    print('Successfully finished the controller program.')


if __name__ == '__main__':
    main()
