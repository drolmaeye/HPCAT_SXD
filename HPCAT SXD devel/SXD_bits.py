# import necessary modules, etc
from Tkinter import *
import tkMessageBox
import tkFileDialog
import tkFont
from epics import *
from epics.devices import Struck
import time
import os.path


class CrystalSpot:
    """
    CrystalSpot used to define, display, and move to a unique sample position

    At any time when data collection IS NOT running, the user can define
    a position or move to a particular position using the relevant buttons.
    """

    def __init__(self, master, label='C1'):
        """
        :param master: frame for inserting widgets
        :param label: label to the left of stage RBVs
        :return: none
        """
        self.frame = Frame(master, padx=10, pady=5)
        self.frame.grid()

        # define variables and position label variable
        self.x = StringVar()
        self.y = StringVar()
        self.z = StringVar()
        self.collect = IntVar()
        self.pos = label
        # file builder variable below
        self.cs_file_part = 'None'

        # make and place widgets
        self.label_pos = Label(self.frame, text=self.pos, width=8)
        self.label_pos.grid(row=0, column=0, sticky='e')
        self.label_x = Label(self.frame, textvariable=self.x, relief=SUNKEN,
                             width=8)
        self.label_x.grid(row=0, column=1, padx=5)
        self.label_y = Label(self.frame, textvariable=self.y, relief=SUNKEN,
                             width=8)
        self.label_y.grid(row=0, column=2, padx=5)
        self.label_z = Label(self.frame, textvariable=self.z, relief=SUNKEN,
                             width=8)
        self.label_z.grid(row=0, column=3, padx=5)
        self.button_define = Button(self.frame, text='Define',
                                    command=self.pos_define)
        self.button_define.grid(row=0, column=4, padx=5)
        self.check_collect = Checkbutton(self.frame, text='Collect',
                                         variable=self.collect)
        self.check_collect.grid(row=0, column=5, padx=5)
        self.button_move = Button(self.frame, text='Move to',
                                  command=self.move_to)
        self.button_move.grid(row=0, column=6, padx=5)

        # test stuff
        if label == 'C1':
            self.button_increment_up = Button(self.frame, text='More', command=self.increment)
            self.button_increment_up.grid(row=0, column=7)
            self.button_increment_dn = Button(self.frame, text='Less', command=self.decrement)
            self.button_increment_dn.grid(row=0, column=8)

    def increment(self):
        for each in xtal_list:
            if each.frame.winfo_ismapped():
                pass
            else:
                each.frame.grid()
                break




    def decrement(self):
        if xtal_list[-1].frame.winfo_ismapped():
            xtal_list[-1].frame.grid_remove()
            xtal_list[-1].collect.set(0)
            return
        else:
            for each in xtal_list:
                if each.frame.winfo_ismapped():
                    pass
                else:
                    last_shown = xtal_list.index(each) - 1
                    xtal_list[last_shown].frame.grid_remove()
                    xtal_list[last_shown].collect.set(0)
                    break


    def pos_define(self):
        """
        defines an (x, y, z) position for the relevant row
        :return: none
        """
        self.x.set('%.4f' % mX.RBV)
        self.y.set('%.4f' % mY.RBV)
        self.z.set('%.4f' % mZ.RBV)

    def move_to(self):
        """
        moves to the (x, y, z) position of the relevant row
        :return: none
        """
        mX.move(self.x.get(), wait=True)
        mY.move(self.y.get(), wait=True)
        mZ.move(self.z.get(), wait=True)
root = Tk()
root.title('HPCAT SXD')

mX = Motor('XPSGP:m1')
mY = Motor('XPSGP:m2')
mZ = Motor('XPSGP:m3')


frameCrystalSpot = Frame(root)
frameCrystalSpot.grid(row=2, column=0, padx=15, pady=15)

xtal1 = CrystalSpot(frameCrystalSpot, label='C1')
xtal2 = CrystalSpot(frameCrystalSpot, label='C2')
xtal3 = CrystalSpot(frameCrystalSpot, label='C3')
xtal4 = CrystalSpot(frameCrystalSpot, label='C4')
xtal5 = CrystalSpot(frameCrystalSpot, label='C5')
xtal6 = CrystalSpot(frameCrystalSpot, label='C6')
xtal7 = CrystalSpot(frameCrystalSpot, label='C7')
xtal8 = CrystalSpot(frameCrystalSpot, label='C8')
xtal9 = CrystalSpot(frameCrystalSpot, label='C9')
xtal10 = CrystalSpot(frameCrystalSpot, label='C10')

xtal_list = [xtal2, xtal3, xtal4, xtal5,
             xtal6, xtal7, xtal8, xtal9, xtal10]

for each in xtal_list:
    each.frame.grid_remove()


root.mainloop()