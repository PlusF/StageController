import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from zaber_motion import Library
from zaber_motion import LogOutputMode
from zaber_motion.binary import Connection
from zaber_motion import Units  # 実世界の単位に変換するため

# ライブラリをオフラインで使えるようにする
Library.enable_device_db_store()
# ログを取る
Library.set_log_output(LogOutputMode.FILE, "motion_library_log.txt")

WIDTH_BUTTON = 5
DT = 100
FONT = ('游ゴシック', 16)
MAX_Z = 25400.032
UNITS_VEL = ['mm/s', '\u03bcm/s', 'nm/s']
DICT_UNITS_VEL = {'mm/s': Units.VELOCITY_MILLIMETRES_PER_SECOND, '\u03bcm/s': Units.VELOCITY_MICROMETRES_PER_SECOND,
                  'nm/s': Units.VELOCITY_NANOMETRES_PER_SECOND}
LIST_VEL = [0.224, 1, 10, 100, 1000]

XY = tk.DISABLED


class Application(tk.Frame):
    def __init__(self, master=None, device=None):
        super().__init__(master)
        self.master.title('Z Stage Controller')
        self.device = device

        # フォントサイズの調整
        self.style = ttk.Style()
        if os.name == 'nt':
            self.style.theme_use('winnative')  # windowsにしかないテーマ
        self.style.configure('.', font=FONT)

        self.create_widgets()

    def create_widgets(self):
        # 親フレーム
        self.frame_xy = ttk.Frame(self.master)
        self.frame_z = ttk.Frame(self.master)
        self.frame_xy.grid(row=0, column=0)
        self.frame_z.grid(row=0, column=1)
        # 子フレーム
        self.frame_xy_canvas = ttk.Frame(self.frame_xy)
        self.frame_xy_buttons = ttk.Frame(self.frame_xy)
        self.frame_xy_speed = ttk.Frame(self.frame_xy)
        self.frame_z_canvas = ttk.Frame(self.frame_z)
        self.frame_z_buttons = ttk.Frame(self.frame_z)
        self.frame_z_speed = ttk.Frame(self.frame_z)
        self.frame_xy_canvas.grid(row=0, column=0, columnspan=2)
        self.frame_xy_buttons.grid(row=1, column=0)
        self.frame_xy_speed.grid(row=1, column=1)
        self.frame_z_canvas.grid(row=0, column=0, columnspan=2)
        self.frame_z_buttons.grid(row=1, column=0)
        self.frame_z_speed.grid(row=1, column=1)
        # ウィジェット xy_canvas
        self.canvas_xy = tk.Canvas(self.frame_xy_canvas, width=400, height=400, bg='gray')
        self.canvas_xy.pack()
        # ウィジェット xy_buttons
        self.button_top = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='↑')
        self.button_left = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='←')
        self.button_right = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='→')
        self.button_bottom = ttk.Button(self.frame_xy_buttons, width=WIDTH_BUTTON, text='↓')
        self.button_top.grid(row=0, column=1)
        self.button_left.grid(row=1, column=0)
        self.button_right.grid(row=1, column=2)
        self.button_bottom.grid(row=2, column=1)
        # ウィジェット xy_speed
        self.combobox_xy = ttk.Combobox(self.frame_xy_speed, width=WIDTH_BUTTON)
        self.scale_xy = ttk.Scale(self.frame_xy_speed, orient='vertical')
        self.combobox_xy.grid(row=0, column=0)
        self.scale_xy.grid(row=1, column=0)
        # ウィジェット z_canvas
        self.canvas_z = tk.Canvas(self.frame_z_canvas, width=200, height=400, bg='lightgray')
        self.canvas_z.pack()
        # ウィジェット z_buttons
        self.button_up = ttk.Button(self.frame_z_buttons, width=WIDTH_BUTTON, text='UP')
        self.button_down = ttk.Button(self.frame_z_buttons, width=WIDTH_BUTTON, text='DOWN')
        self.button_up.grid(row=0, column=0)
        self.button_down.grid(row=1, column=0)
        # ウィジェット z_speed
        self.combobox_z = ttk.Combobox(self.frame_z_speed, width=WIDTH_BUTTON)
        self.scale_z = ttk.Scale(self.frame_z_speed, orient='vertical')
        self.combobox_z.grid(row=0, column=0)
        self.scale_z.grid(row=1, column=0)


def main():
    # with Connection.open_serial_port('COM4') as connection:
        # device_list = connection.detect_devices()
        # device = device_list[0]
    device = None

    root = tk.Tk()

    # こうしないとコンボボックスのフォントが変わらない
    root.option_add("*font", FONT)

    # ウィンドウを閉じる際のイベント
    def on_closing():
        if messagebox.askokcancel('警告', '自動で定位置へと移動します。よろしいですか？'):
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    app = Application(master=root, device=device)
    app.mainloop()

    # device.move_absolute(9000, unit=Units.LENGTH_MICROMETRES)

    print('Successfully finished the controller program.')

if __name__ == '__main__':
    main()
