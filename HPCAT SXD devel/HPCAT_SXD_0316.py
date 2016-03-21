__author__ = 'j.smith'

'''
A GUI for collecting single crystal data at HPCAT using various
hutches, sample stacks, and detectors
'''

# import necessary modules, etc
from Tkinter import *
import tkMessageBox
import tkFileDialog
import tkFont
from epics import *
from epics.devices import Struck
import time
import os.path


# define classes
class ExpConfigure:
    """
    ExpConfigure used to specify station, stages, and detector

    This pops up when the program is first started, and cannot be called
    again.  User must close and restart software to choose an alternate
    configuration  Ultimately, this class yields two variables which
    are used to set up all of the epics connections.
    """

    def __init__(self, master):
        # set up frames
        self.popup = Toplevel(master)
        self.popup.title('Select experimental configuration')

        # stage and detector frames nested on left and right
        frame_stages = Frame(self.popup)
        frame_stages.grid(row=1, column=0, padx=20)
        frame_detectors = Frame(self.popup)
        frame_detectors.grid(row=1, column=1, padx=20)

        # define variables for the two basic choices and set defaults
        self.stack_choice = StringVar()
        self.stack_choice.set(None)
        self.detector_choice = StringVar()
        self.detector_choice.set(None)
        self.use_file = BooleanVar()
        self.use_file.set(0)

        # set up lists to make buttons
        stack_list = [
            ('IDB GP High Precision', 'GPHP'),
            ('IDB GP High Load', 'GPHL'),
            ('IDB Laser Heating', 'LH'),
            ('BMD High Precision', 'BMDHP'),
            ('BMD High Load', 'BMDHL')]

        detectors_list = [
            ('PILATUS 1M', '1M'),
            ('marCCD', 'CCD'),
            ('mar345', 'IP'),
            ('Perkin Elmer', 'PE')]

        # make radio buttons for stages using lists
        for stacks, designation in stack_list:
            self.motor_buttons = Radiobutton(frame_stages, text=stacks,
                                             variable=self.stack_choice,
                                             value=designation)
            self.motor_buttons.grid(column=0, sticky='w', pady=5)

        # make radio buttons for detectors using lists
        for detectors, designation in detectors_list:
            self.det_buttons = Radiobutton(frame_detectors,
                                           text=detectors,
                                           variable=self.detector_choice,
                                           value=designation)
            self.det_buttons.grid(column=0, sticky='w', pady=5)

        self.custom_button = Radiobutton(self.popup,
                                         text='Load custom configuration from file',
                                         variable=self.use_file,
                                         value=1)
        self.custom_button.grid(row=3, column=0, columnspan=2, pady=5)

        # make column headings
        self.stack_head = Label(self.popup, text='Select ONE set of stages')
        self.stack_head.grid(row=0, column=0, pady=5)
        self.detector_head = Label(self.popup, text='Select ONE detector')
        self.detector_head.grid(row=0, column=1, pady=5)

        # make confirmation and custom config buttons
        self.confirm_choice = Button(self.popup, text='Confirm choices',
                                     command=self.confirm_choices)
        self.confirm_choice.grid(row=4, column=0, columnspan=2, pady=10)
        self.or_label = Label(self.popup, text='-----OR-----')
        self.or_label.grid(row=2, column=0, columnspan=2, pady=5)

    def confirm_choices(self):
        """
        Destroy window, pass control back to root to define devices
        """
        self.popup.destroy()


class PrefixMaker:
    """
    PrefixMaker used to start building file path, name, etc
    """

    def __init__(self, master):
        """
        :param master: parent frame of the widgets
        :return: instance of PrefixMaker
        """
        self.frame = Frame(master)
        self.frame.grid()

        # define variables
        self.detPath = StringVar()
        self.pathName = StringVar()
        self.sampleName = StringVar()
        self.name_flag = IntVar()
        self.imageNo = StringVar()
        self.pressureNo = StringVar()
        self.prefix = StringVar()
        # set defaults
        self.pathName.set('Select a user directory')
        self.sampleName.set('test')
        self.imageNo.set('001')
        self.pressureNo.set('1')

        # make and place widgets
        self.det_pathLabel1 = Label(self.frame, text='Detector path')
        self.det_pathLabel1.grid(row=0, column=0, padx=5, pady=5)
        self.det_pathLabel2 = Label(self.frame, textvariable=self.detPath,
                                    width=50, relief=SUNKEN, anchor='w')
        self.det_pathLabel2.grid(row=0, column=1, columnspan=3, pady=5)
        self.pathLabel = Label(self.frame, text='User directory')
        self.pathLabel.grid(row=1, column=0, padx=5, pady=5)
        self.label_user_dir = Label(self.frame, textvariable=self.pathName,
                                    relief=SUNKEN, width=40, anchor='w')
        self.label_user_dir.grid(row=1, column=1, columnspan=3, pady=5, sticky='w')
        self.button_browse = Button(self.frame, text='Browse',
                                    command=self.choose_directory)
        self.button_browse.grid(row=1, column=3, sticky='e')
        self.sampleLabel = Label(self.frame, text='Sample name')
        self.sampleLabel.grid(row=2, column=0, padx=5, pady=5)
        self.sampleEntry = Entry(self.frame, textvariable=self.sampleName,
                                 width=46)
        self.sampleEntry.grid(row=2, column=1, columnspan=3, pady=5, sticky='w')
        self.sampleEntry.bind('<FocusOut>', self.sample_name_validation)
        self.sampleEntry.bind('<Return>', self.sample_name_validation)
        self.imageLabel = Label(self.frame, text='Image No.')
        self.imageLabel.grid(row=3, column=0, pady=5)
        self.imageEntry = Entry(self.frame, textvariable=self.imageNo, width=8)
        self.cbox_short_name = Checkbutton(self.frame, text='Short',
                                           variable=self.name_flag)
        self.cbox_short_name.grid(row=2, column=3, sticky='e')
        self.imageEntry.grid(row=3, column=1, sticky='w', pady=5)
        self.imageEntry.bind('<FocusOut>', self.image_no_validation)
        self.imageEntry.bind('<Return>', self.image_no_validation)
        self.pressureLabel = Label(self.frame, text='Pressure No.')
        self.pressureLabel.grid(row=3, column=2, pady=5, sticky='w')
        self.pressureEntry = Entry(self.frame, textvariable=self.pressureNo,
                                   width=8)
        self.pressureEntry.grid(row=3, column=2, sticky='e', pady=5)

    def path_name_validation(self, *event):
        val = self.pathName.get()
        if not (os.path.exists(val)):
            path_warn()
            return
        if val.endswith('\\'):
            pass
        else:
            self.pathName.set(val + '\\')

    def sample_name_validation(self, *event):
        val = self.sampleName.get()
        chars = set(' .\\/')
        if not any((c in chars) for c in val):
            pass
        else:
            self.sampleName.set('test')
            invalid_entry()

    def image_no_validation(self, *event):
        try:
            val = self.imageNo.get()
            int(val)
            self.imageNo.set(val.zfill(3))
        except ValueError:
            self.imageNo.set('001')
            invalid_entry()

    def choose_directory(self, *event):
        old_dir = self.pathName.get()
        if os.path.exists(old_dir):
            user_dir = tkFileDialog.askdirectory(initialdir=old_dir,
                                                 title='Select a user directory')
        else:
            user_dir = tkFileDialog.askdirectory(title='Select a user directory')
        if user_dir and os.path.exists(user_dir):
            win_path = os.path.normpath(user_dir)
            return self.pathName.set(win_path + '\\')
        else:
            path_warn()
            pass


class Rotation:
    """
    Rotation used to set parameters for SXD collection
    """

    def __init__(self, master, idet='D1'):
        """
        :param master: parent frame
        :param idet: specify detector location to get default RBV
        :return: none
        """
        # frame for row of widgets
        self.frame = Frame(master)
        self.frame.grid()

        # define variables for widgets and calculations
        self.dnumber = idet
        self.detPos = DoubleVar()
        self.collect = IntVar()
        self.wStart = DoubleVar()
        self.wRange = DoubleVar()
        self.wEnd = DoubleVar()
        self.nPTS = IntVar()
        self.stepSize = DoubleVar()
        self.tPerDeg = DoubleVar()
        self.wide = IntVar()
        self.steps = IntVar()
        self.num_wide = IntVar()
        # file builder variable below
        self.rot_file_part = 'None'
        # overwrite warning variable
        self.warning = False

        # set initial variable values
        self.detPos.set('%.3f' % mDet.RBV)
        if idet == 'D1':
            self.collect.set(1)
            self.wide.set(1)
        self.wStart.set(-10.0)
        self.wRange.set(20.0)
        self.wEnd.set(10.0)
        self.nPTS.set(20)
        self.stepSize.set(1.0)
        self.tPerDeg.set(1.0)
        self.num_wide.set(1)

        # set up column headings
        if idet == 'D1':
            self.det_head = Label(self.frame, text='Detector Y')
            self.det_head.grid(row=0, column=1)
            self.start_head = Label(self.frame, text='Start')
            self.start_head.grid(row=0, column=3)
            self.range_head = Label(self.frame, text='Range')
            self.range_head.grid(row=0, column=4)
            self.end_head = Label(self.frame, text='End')
            self.end_head.grid(row=0, column=5)
            self.steps_head = Label(self.frame, text='    Steps')
            self.steps_head.grid(row=0, column=6)
            self.size_head = Label(self.frame, text='Step size')
            self.size_head.grid(row=0, column=7)
            self.tPerDeg_head = Label(self.frame, text='time/degree')
            self.tPerDeg_head.grid(row=0, column=8)
            self.num_wide_head = Label(self.frame, text='Wides')
            self.num_wide_head.grid(row=0, column=11)

        # create and place widgets
        self.label_dnumber = Label(self.frame, text=self.dnumber, width=8)
        self.label_dnumber.grid(row=1, column=0, sticky='e')
        self.entry_detPos = Entry(self.frame, textvariable=self.detPos,
                                  width=10)
        self.entry_detPos.grid(row=1, column=1, padx=5)
        self.entry_detPos.bind('<FocusOut>', self.det_pos_validation)
        self.entry_detPos.bind('<Return>', self.det_pos_validation)
        self.check_detCol = Checkbutton(self.frame, text='collect',
                                        variable=self.collect, width=10)
        self.check_detCol.grid(row=1, column=2, padx=5)
        self.entry_wStart = Entry(self.frame, textvariable=self.wStart,
                                  width=10)
        self.entry_wStart.grid(row=1, column=3, padx=5)
        self.entry_wStart.bind('<FocusOut>', self.w_start_validation)
        self.entry_wStart.bind('<Return>', self.w_start_validation)
        self.entry_wRange = Entry(self.frame, textvariable=self.wRange,
                                  width=10)
        self.entry_wRange.grid(row=1, column=4, padx=5)
        self.entry_wRange.bind('<FocusOut>', self.w_range_validation)
        self.entry_wRange.bind('<Return>', self.w_range_validation)
        self.label_wEnd = Label(self.frame, textvariable=self.wEnd,
                                width=8, relief=SUNKEN, anchor='w')
        self.label_wEnd.grid(row=1, column=5, padx=5)
        self.entry_nPTS = Entry(self.frame, textvariable=self.nPTS,
                                width=10)
        self.entry_nPTS.grid(row=1, column=6, padx=(20, 5))
        self.entry_nPTS.bind('<FocusOut>', self.npts_validation)
        self.entry_nPTS.bind('<Return>', self.npts_validation)
        self.label_stepSize = Label(self.frame, textvariable=self.stepSize,
                                    width=8, relief=SUNKEN, anchor='w')
        self.label_stepSize.grid(row=1, column=7, padx=5)
        self.entry_tPerDeg = Entry(self.frame, textvariable=self.tPerDeg,
                                   width=10)
        self.entry_tPerDeg.grid(row=1, column=8, padx=20)
        self.entry_tPerDeg.bind('<FocusOut>', self.t_per_deg_validation)
        self.entry_tPerDeg.bind('<Return>', self.t_per_deg_validation)
        self.check_wide = Checkbutton(self.frame, text='Wide',
                                      variable=self.wide)
        self.check_wide.grid(row=1, column=9, padx=5)
        self.check_steps = Checkbutton(self.frame, text='Steps',
                                       variable=self.steps)
        self.check_steps.grid(row=1, column=10, padx=5)
        self.entry_num_wide = Entry(self.frame, textvariable=self.num_wide, width=10)
        self.entry_num_wide.grid(row=1, column=11, padx=5)
        self.entry_num_wide.bind('<FocusOut>', self.num_wide_validation)
        self.entry_num_wide.bind('<Return>', self.num_wide_validation)

    # define validation methods for each entry widget
    def det_pos_validation(self, event):
        # value must be float
        # in this case, also must lie within backlash-affected limits
        try:
            val = self.detPos.get()
            isinstance(val, float)
            back_min = val - mDet.BDST
            back_max = val + mDet.BDST
            if mDet.within_limits(back_min) and mDet.within_limits(back_max):
                pass
            else:
                self.detPos.set(mDet.RBV)
                limits_warn()
        except ValueError:
            self.detPos.set(mDet.RBV)
            invalid_entry()

    # validations below typically deal only with format (int, float)
    # position/velocity limits, etc. dealt with in preflight_check
    def w_start_validation(self, *event):
        # value must be float
        try:
            val = self.wStart.get()
            isinstance(val, float)
        except ValueError:
            self.wStart.set(-10.0)
            invalid_entry()
        finally:
            self.w_end_calc()
            self.preflight_check()

    def w_range_validation(self, event):
        # value must be positive float
        try:
            val = self.wRange.get()
            isinstance(val, float)
        except ValueError:
            self.wRange.set(20.0)
            invalid_entry()
        finally:
            self.w_end_calc()
            self.step_size_calc()
            self.preflight_check()

    def w_end_calc(self):
        end = self.wStart.get() + self.wRange.get()
        self.wEnd.set(end)

    def npts_validation(self, event):
        # value must be positive integer
        try:
            val = self.nPTS.get()
            isinstance(val, int)
            if val > 0:
                pass
            else:
                raise ValueError
        except ValueError:
            self.nPTS.set(20)
            invalid_entry()
        finally:
            self.step_size_calc()
            self.preflight_check()

    def num_wide_validation(self, *event):
        # value must be positive integer
        try:
            val = self.num_wide.get()
            isinstance(val, int)
            if val > 0:
                pass
            else:
                raise ValueError
        except ValueError:
            self.num_wide.set(1)
            invalid_entry()
        finally:
            self.preflight_check()

    def step_size_calc(self):
        self.stepSize.set(self.wRange.get()/self.nPTS.get())

    def t_per_deg_validation(self, event):
        # value must be float
        try:
            val = self.tPerDeg.get()
            isinstance(val, float)
        except ValueError:
            self.tPerDeg.set(1.0)
            invalid_entry()
        finally:
            self.preflight_check()

    def preflight_check(self):
        # create grounding index
        grounded = 0
        # ensure w_zero and w_final will not violate limits
        temp_velo = 1/self.tPerDeg.get()
        w_zero = self.wStart.get() - temp_velo * mW.ACCL * 1.5
        w_final = self.wEnd.get() + temp_velo * mW.ACCL * 1.5
        if mW.within_limits(w_zero):
            self.entry_wStart.config(bg='white')
        else:
            grounded += 1
            self.entry_wStart.config(bg='red')
        if mW.within_limits(w_final):
            self.label_wEnd.config(bg='SystemButtonFace')
        else:
            grounded += 1
            self.label_wEnd.config(bg='red')
        # check step size is at least 0.1 and integral within 0.001 w.r.t. range
        msize = self.stepSize.get()*10000
        quotient = divmod(msize, 100)
        if quotient[0] >= 10 and round(quotient[1], 5) == 0:
            self.label_stepSize.config(bg='SystemButtonFace')
        else:
            grounded += 1
            self.label_stepSize.config(bg='red')
        # check if t per degree is okay
        if temp_velo <= mW_vmax:
            self.entry_tPerDeg.config(bg='White')
        else:
            grounded += 1
            self.entry_tPerDeg.config(bg='red')
        # check wide step size/number is okay
        msize = (self.wRange.get()/self.num_wide.get())*10000
        quotient = divmod(msize, 100)
        if quotient[0] >= 10 and round(quotient[1], 5) == 0\
                and self.num_wide.get() < self.nPTS.get():
            self.entry_num_wide.config(bg='White')
        else:
            grounded += 1
            self.entry_num_wide.config(bg='red')
        # if any checks failed, uncheck and disable collect box
        if grounded == 0:
            self.check_detCol.config(state=NORMAL)
        else:
            self.collect.set(0)
            self.check_detCol.config(state=DISABLED)
        # see if I can use this later
        return grounded

    def overwrite_warn(self):
        self.warning = tkMessageBox.askyesno(
            'Overwrite Warning',
            'File name already exists.  Do you want to overwrite?',
            default='no')
        return self.warning

    # Define data collection methods for stack and detector combos
    def dc_1m_diffraction(self):
        """carry out diffraction routine for one row

        The primary characteristic of this routine is that a step scan
        will be done in a single pass, with the mcs clicking a channel
        for each step.
        """
        scan_types = [
            ('wide', self.wide.get()),
            ('steps', self.steps.get())]
        for scan_type, checkbox in scan_types:
            if not abort.get():
                pass
            else:
                return
            if checkbox:
                if scan_type == 'wide':
                    full_file_name = self.rot_file_part + 'w'
                    num_points = self.num_wide.get()
                else:
                    full_file_name = self.rot_file_part + 's'
                    num_points = self.nPTS.get()
                # Ensure first file of series does not exist
                first_filename = full_file_name + \
                    '_' + prefix.imageNo.get() + '.tif'
                full_file_path = prefix.pathName.get() + first_filename
                if not os.path.isfile(full_file_path):
                    pass
                else:
                    self.overwrite_warn()
                    if not self.warning:
                        continue
                    else:
                        pass
                # gather info to prep for move
                perm_velo = mW.VELO
                temp_velo = 1 / self.tPerDeg.get()
                w_zero = self.wStart.get() - temp_velo * mW.ACCL * 1.5
                w_final = self.wEnd.get() + temp_velo * mW.ACCL * 1.5
                acq_period = self.wRange.get() / num_points * self.tPerDeg.get()
                if num_points != 1:
                    exp_time = acq_period - .003
                else:
                    exp_time = acq_period
                # make initial moves and prepare for collection
                mDet.move(self.detPos.get(), wait=True)
                mW.move(w_zero, wait=True)
                mW.VELO = temp_velo
                # try to initialzize softglue here
                sg_config.put('name1', 'clear_all', wait=True)
                sg_config.put('loadConfig1.PROC', 1, wait=True)
                sg_config.put('name2', 'xps_master', wait=True)
                sg_config.put('loadConfig2.PROC', 1, wait=True)
                softglue.put('DnCntr-2_PRESET', 32000, wait=True)
                softglue.put('FI1_Signal', 'motor')
                softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
                # initialize struck for dc_1M collection
                mcs.stop()
                mcs.ExternalMode()
                mcs.put('InputMode', 3, wait=True)
                mcs.put('OutputMode', 3, wait=True)
                mcs.put('OutputPolarity', 0, wait=True)
                mcs.put('LNEStretcherEnable', 0, wait=True)
                # mcs.put('LNEOutputPolarity', 1, wait=True)
                # mcs.put('LNEOutputDelay', 0, wait=True)
                # mcs.put('LNEOutputWidth', 1e-6, wait=True)
                mcs.NuseAll = self.nPTS.get()
                detector.AcquirePeriod = acq_period
                detector.AcquireTime = exp_time
                detector.FileName = full_file_name
                detector.TriggerMode = 2
                detector.FileNumber = prefix.imageNo.get()
                detector.NumImages = num_points
                # set up pco
                mWpco.put('PositionCompareMode', 1, wait=True)
                mWpco.put('PositionComparePulseWidth', 1, wait=True)
                mWpco.put('PositionCompareSettlingTime', 3, wait=True)
                mWpco.PositionCompareStepSize = 0.001
                if mWpco.PositionCompareMaxPosition <= self.wStart.get():
                    mWpco.PositionCompareMaxPosition = self.wEnd.get()
                    mWpco.PositionCompareMinPosition = self.wStart.get()
                else:
                    mWpco.PositionCompareMinPosition = self.wStart.get()
                    mWpco.PositionCompareMaxPosition = self.wEnd.get()
                mWpco.PositionCompareStepSize = self.wRange.get() / self.nPTS.get()
                # Final actions plus data collection move
                time_stamp = time.strftime('%d %b %Y %H:%M:%S',
                                           time.localtime())
                softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
                mcs.start()
                detector.Acquire = 1
                mW.move(w_final, wait=True)
                while detector.Acquire:
                    time.sleep(0.1)
                # recover
                image_num = detector.FileNumber + num_points - 1
                string_image_num = str(image_num)
                prefix.imageNo.set(string_image_num.zfill(3))
                detector.FileNumber = image_num
                detector.TriggerMode = 0
                detector.NumImages = 1
                mWpco.put('PositionCompareMode', 0)
                mW.VELO = perm_velo
                if not mcs.Acquiring:
                    ara = mcs.readmca(1)
                    ara_bit = ara[:self.nPTS.get()]
                    total_time = sum(ara_bit) / 50e6
                    expected_time = self.tPerDeg.get() * self.wRange.get()
                    time_error = total_time - expected_time
                    print total_time
                    print expected_time
                    print time_error
                else:
                    mcs.stop()
                    # TODO Send warning to user (front panel)
                # Open (or create) text file for writing
                textfile_name = prefix.sampleName.get() + '_P' + \
                    prefix.pressureNo.get() + '.txt'
                textfile_path = prefix.pathName.get() + textfile_name
                if not os.path.isfile(textfile_path):
                    header_one = 'Data collection values for: ' + \
                                 prefix.sampleName.get() + '_P' + \
                                 prefix.pressureNo.get()
                    header_two = 'Sample stack: ' + config.stack_choice.get() + \
                                 ', Detector: ' + config.detector_choice.get()
                    header_list = ['{:22}'.format('Timestamp'), '{:30}'.format('File Name'),
                                   '{:>8}'.format('Cen X'), '{:>8}'.format('Cen Y'),
                                   '{:>8}'.format('Sam Z'), '{:>8}'.format('Det. Y'),
                                   '{:>8}'.format('Start'), '{:>8}'.format('End'),
                                   '{:^8}'.format('Images'), '{:>8}'.format('Exp. time')]
                    header_three = ' '.join(header_list)
                    textfile = open(textfile_path, 'a')
                    textfile.write(header_one + '\n' * 2)
                    textfile.write(header_two + '\n' * 2)
                    textfile.write(header_three + '\n' * 2)
                else:
                    textfile = open(textfile_path, 'a')
                # Add line to text file and close
                line_list = ['{:22}'.format(time_stamp), '{:30}'.format(first_filename),
                             '{: 8.3f}'.format(mX.RBV), '{: 8.3f}'.format(mY.RBV),
                             '{: 8.3f}'.format(mZ.RBV), '{: 8.3f}'.format(mDet.RBV),
                             '{: 8.2f}'.format(self.wStart.get()), '{:8.2f}'.format(self.wEnd.get()),
                             '{:^9}'.format(num_points), '{:8.3f}'.format(exp_time)]
                text_line = ' '.join(line_list)
                textfile.write(text_line + '\n')
                textfile.close()
            else:
                pass

    def dc_ccd_diffraction(self):
        """carry out diffraction routine for one row"""
        scan_types = [
            ('wide', self.wide.get()),
            ('steps', self.steps.get())]
        for scan_type, checkbox in scan_types:
            if checkbox:
                if scan_type == 'wide':
                    full_file_name = self.rot_file_part + 'w'
                    num_points = self.num_wide.get()
                else:
                    full_file_name = self.rot_file_part + 's'
                    num_points = self.nPTS.get()
                # Next few lines are principle difference for IP and CCD
                step_size = self.wRange.get()/num_points
                for each in range(num_points):
                    if not abort.get():
                        pass
                    else:
                        return
                    step_start = self.wStart.get() + each * step_size
                    step_end = step_start + step_size
                    # Ensure first file of series does not exist
                    if not prefix.name_flag.get():
                        first_filename = full_file_name + '_' + prefix.imageNo.get() + '.tif'
                    else:
                        first_filename = prefix.sampleName.get() + '_' + prefix.imageNo.get() + '.tif'
                    full_file_path = prefix.pathName.get() + first_filename
                    if not os.path.isfile(full_file_path):
                        pass
                    else:
                        self.overwrite_warn()
                        if not self.warning:
                            continue
                        else:
                            pass
                    # clear previous shutter info
                    shutter.error_calc_clear()
                    # gather info to prep for move
                    perm_velo = mW.VELO
                    temp_velo = 1/self.tPerDeg.get()
                    w_zero = step_start - temp_velo*mW.ACCL*1.5
                    w_final = step_end + temp_velo*mW.ACCL*1.5
                    actual_exposure = step_size*self.tPerDeg.get()
                    # Exp time and period arbitrary + 5 seconds
                    acq_period = actual_exposure + 5
                    exp_time = acq_period
                    # make initial moves and prepare for collection
                    mDet.move(self.detPos.get(), wait=True)
                    mW.move(w_zero, wait=True)
                    time.sleep(0.1)
                    mW.VELO = temp_velo
                    # try to initialize softglue here
                    sg_config.put('name1', 'clear_all', wait=True)
                    sg_config.put('loadConfig1.PROC', 1, wait=True)
                    sg_config.put('name2', 'xps_master', wait=True)
                    sg_config.put('loadConfig2.PROC', 1, wait=True)
                    open_preset = 8000000*(0.5245 - shutter.open_delay.get())
                    close_preset = 8000000*(0.5245 + actual_exposure - shutter.close_delay.get())
                    softglue.put('DnCntr-3_PRESET', open_preset, wait=True)
                    softglue.put('DnCntr-4_PRESET', close_preset, wait=True)
                    softglue.put('FI1_Signal', 'motor', wait=True)
                    softglue.put('FO19_Signal', 'gate_shutter', wait=True)
                    softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
                    # initialize struck for dc_ccd collection
                    # modify this for 3801 scaler at 13BMC!!!!!
                    mcs.stop()
                    mcs.ExternalMode()
                    mcs.put('InputMode', 3, wait=True)
                    mcs.put('OutputMode', 3, wait=True)
                    mcs.put('OutputPolarity', 0, wait=True)
                    mcs.put('LNEStretcherEnable', 0, wait=True)
                    # set for right number of channels
                    if scan_type == 'wide':
                        if num_points == 1:
                            mcs.NuseAll = self.nPTS.get()
                        else:
                            mcs.NuseAll = self.num_wide.get()
                    if scan_type == 'steps':
                        mcs.NuseAll = 2
                    detector.ShutterMode = 0
                    detector.AcquirePeriod = acq_period
                    detector.AcquireTime = exp_time
                    if not prefix.name_flag.get():
                        detector.FileName = full_file_name
                    else:
                        detector.Filename = prefix.sampleName.get()
                    detector.FileNumber = prefix.imageNo.get()
                    # set up pco
                    mWpco.put('PositionCompareMode', 1, wait=True)
                    mWpco.put('PositionComparePulseWidth', 1, wait=True)
                    mWpco.put('PositionCompareSettlingTime', 3, wait=True)
                    mWpco.PositionCompareStepSize = 0.001
                    if mWpco.PositionCompareMaxPosition <= step_start:
                        mWpco.PositionCompareMaxPosition = step_end
                        mWpco.PositionCompareMinPosition = step_start
                    else:
                        mWpco.PositionCompareMinPosition = step_start
                        mWpco.PositionCompareMaxPosition = step_end
                    # here begin test of new criteria
                    if scan_type == 'wide':
                        if num_points == 1:
                            mWpco.PositionCompareStepSize = step_size/self.nPTS.get()
                        else:
                            mWpco.PositionCompareStepSize = step_size/self.num_wide.get()
                    if scan_type == 'steps':
                        mWpco.PositionCompareStepSize = step_size/2
                    # end test new criteria
                    # Final actions plus data collection move
                    time_stamp = time.strftime('%d %b %Y %H:%M:%S',
                                               time.localtime())
                    softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
                    mcs.start()
                    detector.Acquire = 1
                    mW.move(w_final, wait=True)
                    detector.Acquire = 0
                    while detector.DetectorState_RBV:
                        time.sleep(0.1)
                    # recover
                    image_num = str(detector.FileNumber)
                    prefix.imageNo.set(image_num.zfill(3))
                    mWpco.put('PositionCompareMode', 0)
                    time.sleep(0.1)
                    detector.ShutterMode = 1
                    mW.VELO = perm_velo
                    if not mcs.Acquiring:
                        ara = mcs.readmca(1)
                        ara_bit = ara[:mcs.get('CurrentChannel')]
                        total_time = sum(ara_bit)/50e6
                        expected_time = self.tPerDeg.get()*step_size
                        time_error = total_time - expected_time
                        print total_time
                        print expected_time
                        print time_error
                    else:
                        mcs.stop()
                    # get shutter sync info
                    shutter.shutter_error_calc()
                    # Open (or create) text file for writing
                    textfile_name = prefix.sampleName.get() + '_P' + \
                        prefix.pressureNo.get() + '.txt'
                    textfile_path = prefix.pathName.get() + textfile_name
                    if not os.path.isfile(textfile_path):
                        header_one = 'Data collection values for: ' + \
                                     prefix.sampleName.get() + '_P' + \
                                     prefix.pressureNo.get()
                        header_two = 'Sample stack: ' + config.stack_choice.get() + \
                                     ', Detector: ' + config.detector_choice.get()
                        header_list = ['{:22}'.format('Timestamp'), '{:30}'.format('File Name'),
                                       '{:>8}'.format('Cen X'), '{:>8}'.format('Cen Y'),
                                       '{:>8}'.format('Sam Z'), '{:>8}'.format('Det. Y'),
                                       '{:>8}'.format('Start'), '{:>8}'.format('End'),
                                       '{:^8}'.format('Images'), '{:>8}'.format('Exp. time')]
                        header_three = ' '.join(header_list)
                        textfile = open(textfile_path, 'a')
                        textfile.write(header_one + '\n' * 2)
                        textfile.write(header_two + '\n' * 2)
                        textfile.write(header_three + '\n' * 2)
                    else:
                        textfile = open(textfile_path, 'a')
                    # Add line to text file and close
                    line_list = ['{:22}'.format(time_stamp), '{:30}'.format(first_filename),
                                 '{: 8.3f}'.format(mX.RBV), '{: 8.3f}'.format(mY.RBV),
                                 '{: 8.3f}'.format(mZ.RBV), '{: 8.3f}'.format(mDet.RBV),
                                 '{: 8.2f}'.format(step_start), '{:8.2f}'.format(step_end),
                                 '{:^9}'.format(1), '{:8.3f}'.format(actual_exposure)]
                    text_line = ' '.join(line_list)
                    textfile.write(text_line + '\n')
                    textfile.close()


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

        # set up trace to autofill blank collects
        self.collect.trace('w', self.autofill_xyz)

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
        mX.move(self.x.get())
        mY.move(self.y.get())
        mZ.move(self.z.get())
        mX.move(self.x.get(), wait=True)
        mY.move(self.y.get(), wait=True)
        mZ.move(self.z.get(), wait=True)

    def autofill_xyz(self, *args):
        if not self.collect.get():
            return
        if not self.x.get() == '':
            pass
        else:
            self.pos_define()


class GridPoints:
    def __init__(self, master, label):
        """
        Define ends points, steps for grid scan
        """
        self.frame = Frame(master)
        self.frame.grid()

        # define instance variables and set defaults
        self.rel_min = DoubleVar()
        self.step_size = DoubleVar()
        self.rel_max = DoubleVar()
        self.num_steps = IntVar()
        self.rel_min.set('%.3f' % -.05)
        self.rel_max.set('%.3f' % .05)
        self.num_steps.set(11)
        self.step_size.set('%.3f' % .01)
        self.label = label

        # make column headings
        if label == 'Cen Y (horizontal)':
            self.head_grid = Label(self.frame, text='Grid Dimensions')
            self.head_grid.grid(row=0, column=0, pady=5)
            self.head_min = Label(self.frame, text='Rel. min.')
            self.head_min.grid(row=0, column=1)
            self.head_size = Label(self.frame, text='Step size')
            self.head_size.grid(row=0, column=2)
            self.head_max = Label(self.frame, text='Rel. max.')
            self.head_max.grid(row=0, column=3)
            self.head_step = Label(self.frame, text='Points')
            self.head_step.grid(row=0, column=4)

        # define and place widgets with bindings
        self.label_stage = Label(self.frame, text=label, width=16)
        self.label_stage.grid(row=1, column=0, padx=5, pady=5)
        self.entry_min = Entry(self.frame, textvariable=self.rel_min, width=8)
        self.entry_min.grid(row=1, column=1, padx=5)
        self.entry_min.bind('<FocusOut>', self.min_validate)
        self.entry_min.bind('<Return>', self.min_validate)
        self.label_step_size = Label(self.frame, textvariable=self.step_size,
                                     relief=SUNKEN, width=8)
        self.label_step_size.grid(row=1, column=2, padx=5)
        self.entry_max = Entry(self.frame, textvariable=self.rel_max, width=8)
        self.entry_max.grid(row=1, column=3, padx=5)
        self.entry_max.bind('<FocusOut>', self.max_validate)
        self.entry_max.bind('<Return>', self.max_validate)
        self.entry_num_steps = Entry(self.frame, textvariable=self.num_steps,
                                     width=8)
        self.entry_num_steps.grid(row=1, column=4, padx=5)
        self.entry_num_steps.bind('<FocusOut>', self.num_steps_validate)
        self.entry_num_steps.bind('<Return>', self.num_steps_validate)

    def calc_size(self):
        # should be called on every validation
        if self.num_steps.get() > 1:
            i = self.rel_min.get()
            f = self.rel_max.get()
            p = self.num_steps.get()
            size = (f - i) / (p - 1)
        else:
            size = 0
        self.grid_check()
        return self.step_size.set('%.3f' % size)

    def min_validate(self, event):
        try:
            val = self.rel_min.get()
            isinstance(val, float)
            if val < self.rel_max.get():
                self.rel_min.set('%.3f' % val)
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            forced_min = self.rel_max.get() - 0.1
            self.rel_min.set('%.3f' % forced_min)
            self.calc_size()
            invalid_entry()
        finally:
            self.grid_check()

    def max_validate(self, event):
        try:
            val = self.rel_max.get()
            isinstance(val, float)
            if val > self.rel_min.get():
                self.rel_max.set('%.3f' % val)
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            forced_max = self.rel_min.get() + 0.1
            self.rel_max.set('%.3f' % forced_max)
            self.calc_size()
            invalid_entry()
        finally:
            self.grid_check()

    def num_steps_validate(self, event):
        try:
            val = self.num_steps.get()
            isinstance(val, int)
            if 0 < val < 102:
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            self.num_steps.set(11)
            self.calc_size()
            invalid_entry()
        finally:
            self.grid_check()

    def grid_check(self):
        # icing index
        iced = 0
        # ensure travel limits not violated
        if mY.within_limits(y_grid.rel_min.get()):
            y_grid.entry_min.config(bg='white')
        else:
            iced += 1
            y_grid.entry_min.config(bg='red')
        if mY.within_limits(y_grid.rel_max.get()):
            y_grid.entry_max.config(bg='white')
        else:
            iced += 1
            y_grid.entry_max.config(bg='red')
        if mZ.within_limits(z_grid.rel_min.get()):
            z_grid.entry_min.config(bg='white')
        else:
            iced += 1
            z_grid.entry_min.config(bg='red')
        if mZ.within_limits(z_grid.rel_max.get()):
            z_grid.entry_max.config(bg='white')
        else:
            iced += 1
            z_grid.entry_max.config(bg='red')
        if iced == 0:
            do.continuous_button.config(state=NORMAL)
        else:
            do.continuous_button.config(state=DISABLED)


class Actions:
    """
    Big buttons that initiate data collection
    """

    def __init__(self, master):
        """
        :param master: frame for inserting widgets
        """
        self.frame = Frame(master, padx=10, pady=5)
        self.frame.grid()

        # define variables
        self.continuous = IntVar()
        self.continuous.set(0)

        # make big font
        bigfont = tkFont.Font(size=10, weight='bold')

        # make and place widgets
        self.shutter_sync_button = Button(self.frame, text='Shutter Sync', height=2, width=15,
                                          font=bigfont, command=self.show_shutter_sync)
        self.shutter_sync_button.grid(row=0, column=0)
        self.start_exp_button = Button(self.frame, text='Start Exposure',
                                       foreground='blue', height=2, width=15,
                                       font=bigfont, command=self.start_exp)
        self.start_exp_button.grid(row=0, column=1, padx=60)
        self.continuous_button = Button(self.frame,
                                        text='Continuous',
                                        height=2, width=15, font=bigfont,
                                        command=self.cont_exp)
        self.continuous_button.grid(row=0, column=2, padx=5)
        self.grid_scan_button = Button(self.frame, text='Grid Scan',
                                       height=2, width=15, font=bigfont,
                                       command=self.grid_scan)
        self.grid_scan_button.grid(row=0, column=3, padx=5)
        self.quit_button = Button(self.frame, text='Quit', height=2, width=15,
                                  font=bigfont, command=quit_now)
        self.quit_button.grid(row=0, column=4, padx=5)

    def show_shutter_sync(self):
        shutter.popup.deiconify()

    def start_exp(self):
        """
        Iterates data collection, file building, and routine for GUI checkboxes
        """
        prefix.image_no_validation()
        # Ensure file path exists, halt execution if it does not
        if os.path.exists(prefix.pathName.get()):
            pass
        else:
            path_warn()
            return
        process_start()
        # define recovery (or abort) values
        abort.put(0)
        mX_ipos = mX.RBV
        mY_ipos = mY.RBV
        mZ_ipos = mZ.RBV
        mW_ipos = mW.RBV
        mDet_ipos = mDet.RBV
        # switch BNC 7206
        bnc.put(bnc_channel)
        # Define list for iterating Cx
        sample_rows = [
            (xtal1, '_C1', xtal1.collect.get()),
            (xtal2, '_C2', xtal2.collect.get()),
            (xtal3, '_C3', xtal3.collect.get()),
            (xtal4, '_C4', xtal4.collect.get()),
            (xtal5, '_C5', xtal5.collect.get()),
            (xtal6, '_C6', xtal6.collect.get()),
            (xtal7, '_C7', xtal7.collect.get()),
            (xtal8, '_C8', xtal8.collect.get()),
            (xtal9, '_C9', xtal9.collect.get())]
        for sample, c_filebit, xtal_collect in sample_rows:
            if not abort.get():
                pass
            else:
                break
            if xtal_collect:
                # move to Cx position for data collection
                sample.move_to()
                # Build partial file name for this Cx
                sample.cs_file_part = prefix.sampleName.get() + '_P' + \
                    prefix.pressureNo.get() + c_filebit
                # Define list for iterating Dx
                detector_rows = [
                    (det1, '_D1', det1.collect.get()),
                    (det2, '_D2', det2.collect.get()),
                    (det3, '_D3', det3.collect.get()),
                    (det4, '_D4', det4.collect.get()),
                    (det5, '_D5', det5.collect.get()),
                    (det6, '_D6', det6.collect.get()),
                    (det7, '_D7', det7.collect.get()),
                    (det8, '_D8', det8.collect.get()),
                    (det9, '_D9', det9.collect.get())]
                for det_n, d_filebit, det_collect in detector_rows:
                    if not abort.get():
                        pass
                    else:
                        break
                    if det_collect:
                        # Build partial file name for this Dx
                        det_n.rot_file_part = sample.cs_file_part + d_filebit
                        # Go to stack- and detector-appropriate routine
                        if config.detector_choice.get() == '1M':
                            det_n.dc_1m_diffraction()
                        elif config.detector_choice.get() == 'CCD':
                            det_n.dc_ccd_diffraction()
        # return to initial positions (or resume continuous collection)
        if not self.continuous.get():
            mX.move(mX_ipos, wait=True)
            mY.move(mY_ipos, wait=True)
            mZ.move(mZ_ipos, wait=True)
            mW.move(mW_ipos, wait=True)
            mDet.move(mDet_ipos, wait=True)
            softglue.put('FI1_Signal', '')
            softglue.put('FO19_Signal', '0', wait=True)
            abort.put(0)
            process_stop()
            tkMessageBox.showinfo('Done', 'Data collection complete')
        elif abort.get():
            abort.put(0)
            self.continuous.set(0)
        else:
            time.sleep(0.1)

    def cont_exp(self):
        # get initial values for continuous
        mX_icpos = mX.RBV
        mY_icpos = mY.RBV
        mZ_icpos = mZ.RBV
        mW_icpos = mW.RBV
        mDet_icpos = mDet.RBV
        self.continuous.set(1)
        while self.continuous.get():
            self.start_exp()
            oldp = int(prefix.pressureNo.get())
            newp = oldp + 1
            prefix.pressureNo.set(newp)
        mX.move(mX_icpos, wait=True)
        mY.move(mY_icpos, wait=True)
        mZ.move(mZ_icpos, wait=True)
        mW.move(mW_icpos, wait=True)
        mDet.move(mDet_icpos, wait=True)
        softglue.put('FI1_Signal', '')
        softglue.put('FO19_Signal', '0', wait=True)
        process_stop()
        tkMessageBox.showinfo('Done', 'Data collection complete')

    def grid_scan(self):
        """
        Iterates data collection, file building, and routine for GUI checkboxes
        """
        prefix.image_no_validation()
        # Ensure file path exists, halt execution if it does not
        if os.path.exists(prefix.pathName.get()):
            pass
        else:
            path_warn()
            return
        process_start()
        # define recovery (or abort) values
        mX_ipos = mX.RBV
        mY_ipos = mY.RBV
        mZ_ipos = mZ.RBV
        mW_ipos = mW.RBV
        mDet_ipos = mDet.RBV
        # switch bnc 7206
        bnc.put(bnc_channel)
        # Define grid for iteration (as opposed to Cx list)
        for zsteps in range(z_grid.num_steps.get()):
            if not abort.get():
                pass
            else:
                break
            g_index = zsteps*z_grid.num_steps.get()
            if z_grid.num_steps.get() > 1:
                z_rel = z_grid.rel_min.get() + zsteps*z_grid.step_size.get()
                z_abs = mZ_ipos + z_rel
                mZ.move(z_abs, wait=True)
            for ysteps in range(y_grid.num_steps.get()):
                if not abort.get():
                    pass
                else:
                    break
                g_index += 1
                g_filebit = str(g_index)
                # display current data point
                total = str(z_grid.num_steps.get() * y_grid.num_steps.get())
                working.current_index.set('Grid point ' + g_filebit + ' of ' + total)
                if y_grid.num_steps.get() > 1:
                    y_rel = y_grid.rel_min.get() + ysteps*y_grid.step_size.get()
                    y_abs = mY_ipos + y_rel
                    mY.move(y_abs, wait=True)
                # Build partial file name for this Gx
                g_file_part = prefix.sampleName.get() + '_P' + \
                              prefix.pressureNo.get() + '_G' + g_filebit
                # Define list for iterating Dx
                detector_rows = [
                    (det1, '_D1', det1.collect.get()),
                    (det2, '_D2', det2.collect.get()),
                    (det3, '_D3', det3.collect.get()),
                    (det4, '_D4', det4.collect.get()),
                    (det5, '_D5', det5.collect.get()),
                    (det6, '_D6', det6.collect.get()),
                    (det7, '_D7', det7.collect.get()),
                    (det8, '_D8', det8.collect.get()),
                    (det9, '_D9', det9.collect.get())]
                for position, d_filebit, det_collect in detector_rows:
                    if not abort.get():
                        pass
                    else:
                        break
                    if det_collect:
                        # Build partial file name for this Dx
                        position.rot_file_part = g_file_part + d_filebit
                        # Go to stack- and detector-appropriate routine
                        if config.detector_choice.get() == '1M':
                            position.dc_1m_diffraction()
                        elif config.detector_choice.get() == 'CCD':
                            position.dc_ccd_diffraction()
        # return to initial positions (or resume continuous collection)
        mX.move(mX_ipos, wait=True)
        mY.move(mY_ipos, wait=True)
        mZ.move(mZ_ipos, wait=True)
        mW.move(mW_ipos, wait=True)
        mDet.move(mDet_ipos, wait=True)
        abort.put(0)
        softglue.put('FI1_Signal', '')
        softglue.put('FO19_Signal', '0', wait=True)
        process_stop()
        tkMessageBox.showinfo('Done', 'Data collection complete')


class Shutter:
    def __init__(self, master):
        self.popup = Toplevel(master)
        self.popup.title('Shutter Synchronization Control')

        self.frame = Frame(self.popup)
        self.frame.grid()

        # define instance variables and set defaults
        self.open_delay = DoubleVar()
        self.close_delay = DoubleVar()
        self.motor_dwell = DoubleVar()
        self.shutter_dwell = DoubleVar()
        self.open_error = StringVar()
        self.close_error = StringVar()
        self.open_correction = DoubleVar()
        self.close_correction = DoubleVar()
        self.open_delay.set(0.032)
        self.close_delay.set(0.048)
        self.motor_dwell.set('')
        self.shutter_dwell.set('')
        self.open_error.set('')
        self.close_error.set('')
        self.open_correction.set('')
        self.close_correction.set('')

        # define and place widgets
        self.head_delay = Label(self.frame, text='Shutter delay inputs')
        self.head_delay.grid(row=0, column=0, columnspan=4, pady=10)
        self.label_open_delay = Label(self.frame, text='Shutter open delay')
        self.label_open_delay.grid(row=1, column=0, padx=5, pady=5)
        self.label_close_delay = Label(self.frame, text='Shutter close delay')
        self.label_close_delay.grid(row=2, column=0, padx=5, pady=5)
        self.entry_open_delay = Entry(self.frame, textvariable=self.open_delay, width=8)
        self.entry_open_delay.grid(row=1, column=1, padx=5, pady=5)
        self.entry_open_delay.bind('<FocusOut>', self.open_delay_validate)
        self.entry_open_delay.bind('<Return>', self.open_delay_validate)
        self.entry_close_delay = Entry(self.frame, textvariable=self.close_delay, width=8)
        self.entry_close_delay.grid(row=2, column=1, padx=5, pady=5)
        self.entry_close_delay.bind('<FocusOut>', self.close_delay_validate)
        self.entry_close_delay.bind('<Return>', self.close_delay_validate)
        self.head_feedback = Label(self.frame, text='Timing and synchronization results')
        self.head_feedback.grid(row=3, column=0, columnspan=4, pady=10)
        self.label_motor_dwell_label = Label(self.frame, text='Motor dwell')
        self.label_motor_dwell_label.grid(row=4, column=0, padx=5, pady=5)
        self.label_shutter_dwell_label = Label(self.frame, text='Shutter dwell')
        self.label_shutter_dwell_label.grid(row=5, column=0, padx=5, pady=5)
        self.label_motor_dwell_data = Label(self.frame, textvariable=self.motor_dwell,
                                            width=7, relief=SUNKEN)
        self.label_motor_dwell_data.grid(row=4, column=1, padx=5, pady=5)
        self.label_shutter_dwell_data = Label(self.frame, textvariable=self.shutter_dwell,
                                              width=7, relief=SUNKEN)
        self.label_shutter_dwell_data.grid(row=5, column=1, padx=5, pady=5)
        self.label_open_error_label = Label(self.frame, text='Shutter open error')
        self.label_open_error_label.grid(row=7, column=0, padx=5, pady=5)
        self.label_close_error_label = Label(self.frame, text='Shutter close error')
        self.label_close_error_label.grid(row=8, column=0, padx=5, pady=5)
        self.label_open_error_data = Label(self.frame, textvariable=self.open_error,
                                           width=10, relief=SUNKEN)
        self.label_open_error_data.grid(row=7, column=1, padx=5, pady=5)
        self.label_close_error_data = Label(self.frame, textvariable=self.close_error,
                                            width=10, relief=SUNKEN)
        self.label_close_error_data.grid(row=8, column=1, )
        self.head_correction = Label(self.frame, text='Suggested\nDelays')
        self.head_correction.grid(row=6, column=2, padx=5, pady=5)
        self.label_open_correction_data = Label(self.frame, textvariable=self.open_correction,
                                                width=7, relief=SUNKEN)
        self.label_open_correction_data.grid(row=7, column=2, padx=5, pady=5)
        self.label_close_correction_data = Label(self.frame, textvariable=self.close_correction,
                                                 width=7, relief=SUNKEN)
        self.label_close_correction_data.grid(row=8, column=2, padx=5, pady=5)
        self.button_make_correction = Button(self.frame, text='Apply Correction',
                                             command=self.modify_delay)
        self.button_make_correction.grid(row=7, rowspan=2, column=3, padx=10)

        # hide window on startup
        self.popup.withdraw()

    def open_delay_validate(self, event):
        try:
            val = self.open_delay.get()
            isinstance(val, float)
            if 0 <= val < 1:
                self.open_delay.set('%.3f' % val)
            else:
                raise ValueError
        except ValueError:
            forced_min = 0.032
            self.open_delay.set('%.3f' % forced_min)
            invalid_entry()

    def close_delay_validate(self, event):
        try:
            val = self.close_delay.get()
            isinstance(val, float)
            if 0 <= val < 1:
                self.close_delay.set('%.3f' % val)
            else:
                raise ValueError
        except ValueError:
            forced_min = 0.048
            self.close_delay.set('%.3f' % forced_min)
            invalid_entry()

    def shutter_error_calc(self):
        # get 8MHz counts for each component
        motor_counts = softglue.get('UpCntr-1_COUNTS')
        shutter_counts = softglue.get('UpCntr-3_COUNTS')
        delta_counts = softglue.get('UpCntr-4_COUNTS')
        # determine if shutter preceded motor
        if softglue.get('DFF-4_OUT_BI'):
            sign = -1
        else:
            sign = 1
        # define endpoints w.r.t. tm_zero = 0
        tm_final = motor_counts
        ts_zero = delta_counts*sign
        ts_final = ts_zero + shutter_counts
        # calculate errors and corrections in seconds
        freq = 8000000
        motor_dwell = motor_counts/freq
        shutter_dwell = shutter_counts/freq
        open_error = ts_zero/freq
        close_error = (ts_final - tm_final)/freq
        open_correction = (self.open_delay.get() + open_error)
        close_correction = (self.close_delay.get() + close_error)
        if not shutter_counts == 0:
            self.motor_dwell.set('%.3f' % motor_dwell)
            self.shutter_dwell.set('%.3f' % shutter_dwell)
            if open_error < 0:
                op_message = '%.3f' % abs(open_error) + ' early'
            else:
                op_message = '%.3f' % open_error + ' late'
            self.open_error.set(op_message)
            if close_error < 0:
                cl_message = '%.3f' % abs(close_error) + ' early'
            else:
                cl_message = '%.3f' % close_error + ' late'
            self.close_error.set(cl_message)
            self.open_correction.set('%.3f' % open_correction)
            self.close_correction.set('%.3f' % close_correction)
        else:
            self.motor_dwell.set('%.3f' % motor_dwell)
            self.open_error.set('Unknown')
            self.close_error.set('Unknown')

    def error_calc_clear(self):
        self.motor_dwell.set('')
        self.shutter_dwell.set('')
        self.open_error.set('')
        self.close_error.set('')
        self.open_correction.set('')
        self.close_correction.set('')

    def modify_delay(self):
        try:
            val = self.open_correction.get()
            isinstance(val, float)
        except ValueError:
            return
        self.open_delay.set('%.3f' % self.open_correction.get())
        self.close_delay.set('%.3f' % self.close_correction.get())


class BusyWindow:
    def __init__(self, master):
        self.popup = Toplevel(master)
        self.popup.title('Working . . .')

        self.frame = Frame(self.popup)
        self.frame.pack()

        self.current_index = StringVar()

        self.label1 = Label(self.frame, text='Data collection in progress')
        self.label1.pack(pady=10)
        self.label2 = Label(self.frame,
                            text='To abort data collection,\n'
                            'press EPICS Python Abort button')
        self.label2.pack(pady=10)
        self.label3 = Label(self.frame, textvariable=self.current_index)
        self.label3.pack(pady=10)
        # ###self.popup.configure(bg='white')
        # ###self.label1.configure(bg='white')
        # ###self.label2.configure(bg='white')

        self.popup.withdraw()


class Extra:
    def __init__(self, master):
        self.frame = Frame(master, padx=10, pady=5)
        self.frame.grid()

        # define variables and set defaults
        # ###self.open_delay = DoubleVar()
        # ###self.close_delay = DoubleVar()
        # ###self.open_delay.set(0.032)
        # ###self.close_delay.set(0.046)

        # define and place widgets
        self.label_d_up = Label(self.frame, text='D-spots')
        self.label_d_up.grid(row=0, column=0, padx=5, pady=5)
        self.label_c_up = Label(self.frame, text='C-spots')
        self.label_c_up.grid(row=1, column=0, padx=5, pady=5)
        self.button_d_up = Button(self.frame, text='More', command=lambda: self.increment(det_list))
        self.button_d_up.grid(row=0, column=1, padx=5, pady=5)
        self.button_d_dn = Button(self.frame, text='Less', command=lambda: self.decrement(det_list))
        self.button_d_dn.grid(row=0, column=2, padx=5, pady=5)
        self.button_c_up = Button(self.frame, text='More', command=lambda: self.increment(xtal_list))
        self.button_c_up.grid(row=1, column=1, padx=5, pady=5)
        self.button_c_dn = Button(self.frame, text='Less', command=lambda: self.decrement(xtal_list))
        self.button_c_dn.grid(row=1, column=2, padx=5, pady=5)

    def increment(self, target):
        for each in target[1:]:
            if each.frame.winfo_ismapped():
                pass
            else:
                each.frame.grid()
                break

    def decrement(self, target):
        if target[-1].frame.winfo_ismapped():
            target[-1].frame.grid_remove()
            target[-1].collect.set(0)
            return
        else:
            for each in target[2:]:
                if each.frame.winfo_ismapped():
                    pass
                else:
                    last_shown = target.index(each) - 1
                    target[last_shown].frame.grid_remove()
                    target[last_shown].collect.set(0)
                    break


# define basic functions
def quit_now():
    quit()


def invalid_entry():
    # generic pop-up notification for invalid text entries
    tkMessageBox.showwarning('Invalid Entry',
                             message='Input was reset to default value')


def path_warn():
    tkMessageBox.showwarning('Invalid Path Name',
                             'Please modify User Directory and try again')


def limits_warn():
    tkMessageBox.showwarning('Limits Violation',
                             'Target position(s) exceeds motor limits\n'
                             'Input was reset to default value')


def process_start():
        do.start_exp_button.config(state=DISABLED)
        do.continuous_button.config(state=DISABLED)
        do.grid_scan_button.config(state=DISABLED)
        xtop = root.winfo_x() + root.winfo_width() / 2 - 150
        ytop = root.winfo_y() + root.winfo_height() / 2 - 60
        working.popup.geometry('300x120+%d+%d' % (xtop, ytop))
        working.popup.deiconify()


def process_stop():
        do.start_exp_button.config(state=NORMAL)
        do.continuous_button.config(state=NORMAL)
        do.grid_scan_button.config(state=NORMAL)
        hide_working()


def hide_shutter():
    shutter.popup.withdraw()


def hide_working():
    working.popup.withdraw()


def path_put(**kwargs):
    prefix.detPath.set(detector.get('FilePath_RBV', as_string=True))
    # test User directory autofill Feb 2016
    result = prefix.detPath.get()
    if result[0:15] == '/mnt/16idb_data':
        user_directory = 'X:' + result[15:]
        windows_path = os.path.normpath(user_directory) + '\\'
        prefix.pathName.set(windows_path)
        prefix.path_name_validation()
    elif result[0:13] == '/ramdisk/Data':
        user_directory = 'P:' + result[13:]
        windows_path = os.path.normpath(user_directory) + '\\'
        prefix.pathName.set(windows_path)
        prefix.path_name_validation()


'''
Program start, define primary UI
'''
root = Tk()
root.title('HPCAT SXD')
# hide root, draw config window, wait for user input
root.withdraw()
config = ExpConfigure(root)
root.wait_window(config.popup)

'''
With choices made, define relevant epics devices
'''
# create motor, mcs, and PCO devices
pco_args = ['PositionCompareMode', 'PositionCompareMinPosition',
            'PositionCompareMaxPosition', 'PositionCompareStepSize',
            'PositionComparePulseWidth', 'PositionCompareSettlingTime']

softglue_args = ['FI1_Signal', 'FI2_Signal', 'FI3_Signal', 'FI4_Signal',
                 'FI5_Signal', 'FI6_Signal', 'FI7_Signal', 'FI8_Signal',
                 'FI9_Signal', 'FI10_Signal', 'FI11_Signal', 'FI12_Signal',
                 'FI13_Signal', 'FI14_Signal', 'FI15_Signal', 'FI16_Signal',
                 'FO17_Signal', 'FO18_Signal', 'FO19_Signal', 'FO20_Signal',
                 'FO21_Signal', 'FO22_Signal', 'FO23_Signal', 'FO24_Signal',
                 'FI25_Signal', 'FI26_Signal', 'FI27_Signal', 'FI28_Signal',
                 'FI29_Signal', 'FI30_Signal', 'FI31_Signal', 'FI32_Signal',
                 'FI33_Signal', 'FI34_Signal', 'FI35_Signal', 'FI36_Signal',
                 'FI37_Signal', 'FI38_Signal', 'FI39_Signal', 'FI40_Signal',
                 'FI41_Signal', 'FI42_Signal', 'FI43_Signal', 'FI44_Signal',
                 'FI45_Signal', 'FI46_Signal', 'FI47_Signal', 'FI48_Signal',
                 'DnCntr-1_PRESET', 'DnCntr-2_PRESET', 'DnCntr-3_PRESET', 'DnCntr-4_PRESET',
                 'UpCntr-1_COUNTS', 'UpCntr-2_COUNTS', 'UpCntr-3_COUNTS', 'UpCntr-4_COUNTS',
                 'DivByN-1_N', 'DFF-4_OUT_BI', 'BUFFER-1_IN_Signal']

sg_config_args = ['name1', 'name2', 'loadConfig1.PROC', 'loadConfig2.PROC']

# option to load and read custom configuration
if config.use_file.get():
    user_config = tkFileDialog.askopenfile(
        mode='r', title='Please select configuration file')
    exec user_config.read()
    user_config.close()
# hard-encoded configuration options
elif config.stack_choice.get() == 'GPHP':
    mX = Motor('XPSGP:m1')
    mY = Motor('XPSGP:m2')
    mZ = Motor('XPSGP:m3')
    mW = Motor('XPSGP:m4')
    mDet = Motor('16IDB:m6')
    mcs = Struck('16IDB:SIS1:')
    mWpco = Device('XPSGP:m4', pco_args)
    bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
    bnc_channel = 's04'
    softglue = Device('16IDB:softGlue:', softglue_args)
    sg_config = Device('16IDB:SGMenu:', sg_config_args)
    abort = PV('16IDB:Unidig1Bo6')
    mW_vmax = 10.0

elif config.stack_choice.get() == 'GPHL':
    mX = Motor('16IDB:m31')
    mY = Motor('16IDB:m32')
    mZ = Motor('16IDB:m5')
    mW = Motor('XPSGP:m5')
    mDet = Motor('16IDB:m6')
    mcs = Struck('16IDB:SIS1:')
    mWpco = Device('XPSGP:m5', pco_args)
    bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
    bnc_channel = 's05'
    softglue = Device('16IDB:softGlue:', softglue_args)
    abort = PV('16IDB:Unidig1Bo6')

elif config.stack_choice.get() == 'LH':
    pass
    mX = Motor('XPSLH:m1')
    mY = Motor('XPSLH:m2')
    mZ = Motor('XPSLH:m3')
    mW = Motor('XPSLH:m4')
    mDet = Motor('16IDB:m13')
    mcs = Struck('16IDB:SIS1:')
    mWpco = Device('XPSLH:m4', pco_args)
    bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
    bnc_channel = 's04'
    softglue = Device('16IDB:softGlue:', softglue_args)
    sg_config = Device('16IDB:SGMenu:', sg_config_args)
    abort = PV('16IDB:Unidig1Bo6')
    mW_vmax = 10.0

elif config.stack_choice.get() == 'BMDHP':
    pass
    # mX = Motor('XPSBMD:m5')
    # mY = Motor('XPSBMD:m4')
    # mZ = Motor('XPSBMD:m3')
    # mW = Motor('XPSBMD:m2')
    # mDet = Motor('16BMD:mxx')
    # bnc = PV('16TEST1:cmdReply1_do_IO.AOUT')
    # bnc_channel = 's02'
elif config.stack_choice.get() == 'BMDHL':
    pass
    # mX = Motor('16IDB:m31')
    # mY = Motor('16IDB:m32')
    # mZ = Motor('16IDB:m5')
    # mW = Motor('XPSGP:m1')
    # mDet = Motor('16IDB:m6')
    # mcs = Struck('16IDB:SIS1:')
    # bnc = PV('16TEST1:cmdReply1_do_IO.AOUT')
    # bnc_channel = 's02'
else:
    pass

# create detector device
detector_args = ['ShutterMode', 'ShutterControl', 'AcquireTime',
                 'AcquirePeriod', 'NumImages', 'TriggerMode',
                 'Acquire', 'DetectorState_RBV', 'FilePath_RBV',
                 'FileName', 'FileNumber', 'AutoIncrement',
                 'FullFileName_RBV']
if config.use_file.get():
    pass
elif config.detector_choice.get() == '1M':
    detector = Device('HP1M-PIL1:cam1:', detector_args)
elif config.detector_choice.get() == 'CCD':
    detector = Device('16IDB:MARCCD:cam1:', detector_args)
elif config.detector_choice.get() == 'IP':
    pass
    # detector = Device('16BMD:MAR345:cam1:', detector_args)
elif config.detector_choice.get() == 'PE':
    pass
    # detector = Device('16IDB:xxx:xxx:', detector_args)
else:
    pass


detector.add_callback('FilePath_RBV', callback=path_put)
# frames for displaying groups of objects
frameFiles = Frame(root)
frameFiles.grid(row=0, column=0, sticky='w', padx=40, pady=15)
frameExtra = Frame(root)
frameExtra.grid(row=0, column=1)
frameRotation = Frame(root)
frameRotation.grid(row=1, column=0, columnspan=2, sticky='w', padx=40, pady=15)
frameCrystalSpot = Frame(root)
frameCrystalSpot.grid(row=2, column=0, padx=15, pady=15)
frameGridPoints = Frame(root)
frameGridPoints.grid(row=2, column=1, padx=15)
frameControl = Frame(root)
frameControl.grid(row=3, column=0, columnspan=2, pady=15, sticky='e')

# collections of objects to put in above frames
prefix = PrefixMaker(frameFiles)
extras = Extra(frameExtra)
det1 = Rotation(frameRotation, idet='D1')
det2 = Rotation(frameRotation, idet='D2')
det3 = Rotation(frameRotation, idet='D3')
det4 = Rotation(frameRotation, idet='D4')
det5 = Rotation(frameRotation, idet='D5')
det6 = Rotation(frameRotation, idet='D6')
det7 = Rotation(frameRotation, idet='D7')
det8 = Rotation(frameRotation, idet='D8')
det9 = Rotation(frameRotation, idet='D9')
xtal1 = CrystalSpot(frameCrystalSpot, label='C1')
xtal2 = CrystalSpot(frameCrystalSpot, label='C2')
xtal3 = CrystalSpot(frameCrystalSpot, label='C3')
xtal4 = CrystalSpot(frameCrystalSpot, label='C4')
xtal5 = CrystalSpot(frameCrystalSpot, label='C5')
xtal6 = CrystalSpot(frameCrystalSpot, label='C6')
xtal7 = CrystalSpot(frameCrystalSpot, label='C7')
xtal8 = CrystalSpot(frameCrystalSpot, label='C8')
xtal9 = CrystalSpot(frameCrystalSpot, label='C9')
y_grid = GridPoints(frameGridPoints, label='Cen Y (horizontal)')
z_grid = GridPoints(frameGridPoints, label='Sam Z (vertical)')
do = Actions(frameControl)
shutter = Shutter(root)
working = BusyWindow(root)

det_list = [det1, det2, det3, det4, det5,
            det6, det7, det8, det9]
xtal_list = [xtal1, xtal2, xtal3, xtal4, xtal5,
             xtal6, xtal7, xtal8, xtal9]
for each in det_list[3:9]:
    each.frame.grid_remove()
for each in xtal_list[3:9]:
    each.frame.grid_remove()

shutter.popup.protocol('WM_DELETE_WINDOW', hide_shutter)
working.popup.protocol('WM_DELETE_WINDOW', hide_working)
path_put()
root.deiconify()
root.mainloop()
