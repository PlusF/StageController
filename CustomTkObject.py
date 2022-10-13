# tkinterのcanvasに描画する図形をコントローラーに使う
# 範囲内での操作、現在の位置の取得が行える
import math


class MovableObject:
    canvas = None
    thres_list = []

    def __init__(self):
        self.id = None
        self.x0 = None
        self.y0 = None
        self.rank = None

    def dragging(self, event):
        pass

    def reset(self, event):
        self.canvas.moveto(self.id, self.x0, self.y0)
        self.rank = 0

    def get_rank(self):
        return self.rank


class MovableOval(MovableObject):
    def __init__(self, x0, y0, x1, y1, **key):
        super().__init__()
        self.id = self.canvas.create_oval(x0, y0, x1, y1, **key)
        self.canvas.tag_bind(self.id, '<Button1-Motion>', self.dragging)
        self.canvas.tag_bind(self.id, '<ButtonRelease>', self.reset)
        x0, y0, x1, y1 = self.canvas.bbox(self.id)
        self.r = (x1 - x0) / 2
        self.x0 = (x0 + x1) / 2 - self.r
        self.y0 = (y0 + y1) / 2 - self.r
        self.rank = 0

    def dragging(self, event):
        x = event.x - self.r
        y = event.y - self.r
        r = ((x - self.x0) ** 2 + (y - self.y0) ** 2) ** 0.5
        if r > self.thres_list[-1]:
            theta = math.atan2(y - self.y0, x - self.x0)
            x = self.thres_list[-1] * math.cos(theta) + self.x0
            y = self.thres_list[-1] * math.sin(theta) + self.y0
        self.canvas.moveto(self.id, x, y)

        if r < self.thres_list[0]:
            self.rank = 0
        elif r < self.thres_list[1]:
            self.rank = 1
        elif r < self.thres_list[2]:
            self.rank = 2
        else:
            self.rank = 3


class MovableRect(MovableObject):
    def __init__(self, x0, y0, x1, y1, **key):
        super().__init__()
        self.id = self.canvas.create_rectangle(x0, y0, x1, y1, **key)
        self.canvas.tag_bind(self.id, '<Button1-Motion>', self.dragging)
        self.canvas.tag_bind(self.id, '<ButtonRelease>', self.reset)
        x0, y0, x1, y1 = self.canvas.bbox(self.id)
        self.h_half = (y1 - y0) / 2
        self.x0 = x0
        self.y0 = y0
        self.rank = 0

    def dragging(self, event):
        y = event.y - self.h_half
        dy = y - self.y0
        if dy < -self.thres_list[-1]:
            y  = -self.thres_list[-1] + self.y0
        elif dy > self.thres_list[-1]:
            y  = self.thres_list[-1] + self.y0
        self.canvas.moveto(self.id, self.x0, y)

        if abs(dy) < self.thres_list[0]:
            self.rank = 0
        elif abs(dy) < self.thres_list[1]:
            self.rank = 1
        elif abs(dy) < self.thres_list[2]:
            self.rank = 2
        else:
            self.rank = 3