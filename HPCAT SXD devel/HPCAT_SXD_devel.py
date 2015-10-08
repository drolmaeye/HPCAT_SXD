__author__ = 'j.smith'

# ##important: last version before classing abort!!!

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

        det_list = [
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
        for detectors, designation in det_list:
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
        self.frame.pack()

        # define variables
        self.detPath = StringVar()
        self.pathName = StringVar()
        self.sampleName = StringVar()
        self.imageNo = StringVar()
        self.pressureNo = StringVar()
        self.prefix = StringVar()
        # set defaults
        self.pathName.set('P:\\2015-1\\HPCAT\\SXD_test\\')
        self.sampleName.set('test')
        self.imageNo.set('001')
        self.pressureNo.set('1')

        # make and place widgets
        self.det_pathLabel1 = Label(self.frame, text='Detector path')
        self.det_pathLabel1.grid(row=0, column=0, padx=5, pady=5)
        self.det_pathLabel2 = Label(self.frame, textvariable=self.detPath,
                                    width=40, relief=SUNKEN, anchor='w')
        self.det_pathLabel2.grid(row=0, column=1, columnspan=3, pady=5)
        self.pathLabel = Label(self.frame, text='User directory')
        self.pathLabel.grid(row=1, column=0, padx=5, pady=5)
        self.pathEntry = Entry(self.frame, textvariable=self.pathName,
                               width=46)
        self.pathEntry.grid(row=1, column=1, columnspan=3, pady=5)
        self.pathEntry.bind('<Button-1>', self.choose_directory)
        self.pathEntry.bind('<FocusOut>', self.path_name_validation)
        self.pathEntry.bind('<Return>', self.path_name_validation)
        self.sampleLabel = Label(self.frame, text='Sample name')
        self.sampleLabel.grid(row=2, column=0, padx=5, pady=5)
        self.sampleEntry = Entry(self.frame, textvariable=self.sampleName,
                                 width=46)
        self.sampleEntry.grid(row=2, column=1, columnspan=3, pady=5)

        self.imageLabel = Label(self.frame, text='Image No.')
        self.imageLabel.grid(row=3, column=0, pady=5)
        self.imageEntry = Entry(self.frame, textvariable=self.imageNo,
                                width=8)
        self.imageEntry.grid(row=3, column=1, sticky='w', pady=5)
        self.imageEntry.bind('<FocusOut>', self.image_no_validation)
        self.imageEntry.bind('<Return>', self.image_no_validation)
        self.pressureLabel = Label(self.frame, text='Pressure No.')
        self.pressureLabel.grid(row=3, column=2, pady=5)
        self.pressureEntry = Entry(self.frame, textvariable=self.pressureNo,
                                   width=8)
        self.pressureEntry.grid(row=3, column=3, sticky='w', pady=5)

    def path_name_validation(self, event):
        val = self.pathName.get()
        if not (os.path.exists(val)):
            path_warn()
            return
        if val.endswith('\\'):
            pass
        else:
            self.pathName.set(val + '\\')

    def image_no_validation(self, *event):
        try:
            val = self.imageNo.get()
            int(val)
            self.imageNo.set(val.zfill(3))
        except ValueError:
            self.imageNo.set('001')
            invalid_entry()

    def choose_directory(self, event):
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

    def __init__(self, master, idet='Center'):
        """
        :param master: parent frame
        :param idet: specify detector location to get default RBV
        :return: none
        """
        # frame for row of widgets
        self.frame = Frame(master)
        self.frame.pack()

        # define variables for widgets and calculations
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
        if idet == 'Center':
            self.detPos.set(mDet.RBV)
            self.collect.set(1)
            self.wide.set(1)
        elif idet == 'Negative':
            if mDet.within_limits(mDet.RBV - 70.0):
                self.detPos.set(mDet.RBV - 70.0)
            else:
                self.detPos.set(mDet.RBV)
        elif idet == 'Positive':
            if mDet.within_limits(mDet.RBV + 70.0):
                self.detPos.set(mDet.RBV + 70.0)
            else:
                self.detPos.set(mDet.RBV)
        else:
            pass
        self.wStart.set(-10.0)
        self.wRange.set(20.0)
        self.wEnd.set(10.0)
        self.nPTS.set(20)
        self.stepSize.set(1.0)
        self.tPerDeg.set(1.0)
        self.num_wide.set(1)

        # set up column headings
        if idet == 'Center':
            self.det_head = Label(self.frame, text='Detector Y')
            self.det_head.grid(row=0, column=0)
            self.start_head = Label(self.frame, text='Start')
            self.start_head.grid(row=0, column=2)
            self.range_head = Label(self.frame, text='Range')
            self.range_head.grid(row=0, column=3)
            self.end_head = Label(self.frame, text='End')
            self.end_head.grid(row=0, column=4)
            self.steps_head = Label(self.frame, text='    Steps')
            self.steps_head.grid(row=0, column=5)
            self.size_head = Label(self.frame, text='Step size')
            self.size_head.grid(row=0, column=6)
            self.tPerDeg_head = Label(self.frame, text='time/degree')
            self.tPerDeg_head.grid(row=0, column=7)
            self.num_wide_head = Label(self.frame, text='Wides')
            self.num_wide_head.grid(row=0, column=10)

        # create and place widgets
        self.entry_detPos = Entry(self.frame, textvariable=self.detPos,
                                  width=10)
        self.entry_detPos.grid(row=1, column=0, padx=5)
        self.entry_detPos.bind('<FocusOut>', self.det_pos_validation)
        self.entry_detPos.bind('<Return>', self.det_pos_validation)
        self.check_detCol = Checkbutton(self.frame, text=idet,
                                        variable=self.collect, width=10)
        self.check_detCol.grid(row=1, column=1, padx=5)
        self.entry_wStart = Entry(self.frame, textvariable=self.wStart,
                                  width=10)
        self.entry_wStart.grid(row=1, column=2, padx=5)
        self.entry_wStart.bind('<FocusOut>', self.w_start_validation)
        self.entry_wStart.bind('<Return>', self.w_start_validation)
        self.entry_wRange = Entry(self.frame, textvariable=self.wRange,
                                  width=10)
        self.entry_wRange.grid(row=1, column=3, padx=5)
        self.entry_wRange.bind('<FocusOut>', self.w_range_validation)
        self.entry_wRange.bind('<Return>', self.w_range_validation)
        self.label_wEnd = Label(self.frame, textvariable=self.wEnd,
                                width=8, relief=SUNKEN, anchor='w')
        self.label_wEnd.grid(row=1, column=4, padx=5)
        self.entry_nPTS = Entry(self.frame, textvariable=self.nPTS,
                                width=10)
        self.entry_nPTS.grid(row=1, column=5, padx=(20, 5))
        self.entry_nPTS.bind('<FocusOut>', self.npts_validation)
        self.entry_nPTS.bind('<Return>', self.npts_validation)
        self.label_stepSize = Label(self.frame, textvariable=self.stepSize,
                                    width=8, relief=SUNKEN, anchor='w')
        self.label_stepSize.grid(row=1, column=6, padx=5)
        self.entry_tPerDeg = Entry(self.frame, textvariable=self.tPerDeg,
                                   width=10)
        self.entry_tPerDeg.grid(row=1, column=7, padx=20)
        self.entry_tPerDeg.bind('<FocusOut>', self.t_per_deg_validation)
        self.entry_tPerDeg.bind('<Return>', self.t_per_deg_validation)
        self.check_wide = Checkbutton(self.frame, text='Wide',
                                      variable=self.wide)
        self.check_wide.grid(row=1, column=8, padx=5)
        self.check_steps = Checkbutton(self.frame, text='Steps',
                                       variable=self.steps)
        self.check_steps.grid(row=1, column=9, padx=5)
        self.entry_num_wide = Entry(self.frame, textvariable=self.num_wide, width=10)
        self.entry_num_wide.grid(row=1, column=10, padx=5)
        self.entry_num_wide.bind('<FocusOut>', self.num_wide_validation)
        self.entry_num_wide.bind('<Return>', self.num_wide_validation)

    # define validation methods for each entry widget
    def det_pos_validation(self, event):
        # value must be float within motor limits
        try:
            val = self.detPos.get()
            isinstance(val, float)
            if mDet.within_limits(val):
                pass
            else:
                raise ValueError
        except ValueError:
            self.detPos.set(mDet.RBV)
            invalid_entry()

    def w_start_validation(self, *event):
        # value must be float within motor limits
        try:
            val = self.wStart.get()
            isinstance(val, float)
            if mW.within_limits(val) and \
                    mW.within_limits(val + self.wRange.get()):
                pass
            else:
                raise ValueError
        except ValueError:
            self.wStart.set(-10.0)
            invalid_entry()
        finally:
            self.w_end_calc()

    def w_range_validation(self, event):
        # value must be positive float and
        # together with start, must pass motor limits
        try:
            val = self.wRange.get()
            isinstance(val, float)
            if mW.within_limits(self.wStart.get() + val) and val > 1.0:
                pass
            else:
                raise ValueError
        except ValueError:
            self.wRange.set(20.0)
            invalid_entry()
            # ensure start plus default range does not exceed limits
            self.w_start_validation()
        finally:
            self.w_end_calc()
            self.step_size_calc()

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

    def num_wide_validation(self, event):
        # value must be positive integer
        try:
            val = self.num_wide.get()
            isinstance(val, int)
            if 0 < val <= self.nPTS.get():
                pass
            else:
                raise ValueError
        except ValueError:
            self.num_wide.set(1)
            invalid_entry()
        finally:
            self.step_size_calc()

    def step_size_calc(self):
        size = self.wRange.get() / self.nPTS.get()
        self.stepSize.set(size)

    def t_per_deg_validation(self, event):
        # value must be float larger than 0.05 (not more than 20 deg per sec)
        try:
            val = self.tPerDeg.get()
            isinstance(val, float)
            if val >= 0.05:
                pass
            else:
                raise ValueError
        except ValueError:
            self.tPerDeg.set(1.0)
            invalid_entry()

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
            if not do.abort.get():
                pass
            else:
                return
            if checkbox:
                if scan_type == 'wide':
                    full_file_name = self.rot_file_part + 'w'
                    num_points = 1
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
                    abort_window.lift()
                    abort_window.grab_set()
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
                # initialize struck for dc_1M collection
                mcs.stop()
                mcs.ExternalMode()
                mcs.put('InputMode', 3, wait=True)
                mcs.put('OutputMode', 3, wait=True)
                mcs.put('OutputPolarity', 0, wait=True)
                mcs.put('LNEStretcherEnable', 1, wait=True)
                mcs.put('LNEOutputPolarity', 1, wait=True)
                mcs.put('LNEOutputDelay', 0, wait=True)
                mcs.put('LNEOutputWidth', 1e-6, wait=True)
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
                # update to give abort a chance
                abort_window.update()
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
                step_size = self.wRange.get() / num_points
                for each in range(num_points):
                    if not do.abort.get():
                        pass
                    else:
                        return
                    # ###begin delay code test here
                    temp_velo = 1 / self.tPerDeg.get()
                    step_start_t = self.wStart.get() + each * step_size
                    step_end_t = step_start_t + step_size
                    offset = temp_velo * 0.039
                    step_start = step_start_t - offset
                    step_end = step_end_t - offset
                    # ###end delay test
                    # Ensure first file of series does not exist
                    first_filename = full_file_name + \
                        '_' + prefix.imageNo.get() + '.tif'
                    full_file_path = prefix.pathName.get() + first_filename
                    if not os.path.isfile(full_file_path):
                        pass
                    else:
                        self.overwrite_warn()
                        abort_window.lift()
                        abort_window.grab_set()
                        if not self.warning:
                            continue
                        else:
                            pass
                    # gather info to prep for move
                    perm_velo = mW.VELO
                    # ###temp_velo = 1 / self.tPerDeg.get()
                    w_zero = step_start - temp_velo * mW.ACCL * 1.5
                    w_final = step_end + temp_velo * mW.ACCL * 1.5
                    # TODO limit check
                    actual_exposure = step_size * self.tPerDeg.get()
                    # Exp time and period arbitrary + 5 seconds
                    acq_period = actual_exposure + 5
                    exp_time = acq_period
                    # make initial moves and prepare for collection
                    mDet.move(self.detPos.get(), wait=True)
                    mW.move(w_zero, wait=True)
                    time.sleep(0.5)
                    mW.VELO = temp_velo
                    # initialize struck for dc_ccd collection
                    mcs.stop()
                    mcs.ExternalMode()
                    mcs.put('InputMode', 3, wait=True)
                    mcs.put('OutputMode', 3, wait=True)
                    mcs.put('OutputPolarity', 0, wait=True)
                    mcs.put('LNEStretcherEnable', 0, wait=True)
                    mcs.NuseAll = self.nPTS.get()
                    detector.ShutterMode = 0
                    detector.AcquirePeriod = acq_period
                    detector.AcquireTime = exp_time
                    detector.FileName = full_file_name
                    detector.TriggerMode = 0
                    detector.FileNumber = prefix.imageNo.get()
                    # set up pco
                    mWpco.put('PositionCompareMode', 1, wait=True)
                    mWpco.put('PositionComparePulseWidth', 1, wait=True)
                    mWpco.PositionCompareStepSize = 0.001
                    if mWpco.PositionCompareMaxPosition <= step_start:
                        mWpco.PositionCompareMaxPosition = step_end
                        mWpco.PositionCompareMinPosition = step_start
                    else:
                        mWpco.PositionCompareMinPosition = step_start
                        mWpco.PositionCompareMaxPosition = step_end
                    # TODO make some arbitrary cutoff here
                    mWpco.PositionCompareStepSize = step_size / self.nPTS.get()
                    # Final actions plus data collection move
                    time_stamp = time.strftime('%d %b %Y %H:%M:%S',
                                               time.localtime())
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
                    time.sleep(0.5)
                    detector.ShutterMode = 1
                    mW.VELO = perm_velo
                    if not mcs.Acquiring:
                        ara = mcs.readmca(1)
                        ara_bit = ara[:self.nPTS.get()]
                        total_time = sum(ara_bit) / 50e6
                        expected_time = self.tPerDeg.get() * step_size
                        time_error = total_time - expected_time
                        print total_time
                        print expected_time
                        print time_error
                    else:
                        mcs.stop()
                        # TODO Send warning to front panel
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
                                 '{: 8.2f}'.format(step_start_t), '{:8.2f}'.format(step_end_t),
                                 '{:^9}'.format(1), '{:8.3f}'.format(actual_exposure)]
                    text_line = ' '.join(line_list)
                    textfile.write(text_line + '\n')
                    textfile.close()
                    # update to give abort a chance
                    abort_window.update()
            else:
                pass


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
        self.frame.pack()

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


class GridPoints:
    def __init__(self, master, label):
        """
        Define ends points, steps for grid scan
        """
        self.frame = Frame(master)
        self.frame.pack()

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
        i = self.rel_min.get()
        f = self.rel_max.get()
        p = self.num_steps.get()
        size = (f - i) / (p - 1)
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

    def num_steps_validate(self, event):
        try:
            val = self.num_steps.get()
            isinstance(val, int)
            if val > 1:
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            self.num_steps.set(11)
            self.calc_size()
            invalid_entry()


class Actions:
    """
    Big buttons that initiate data collection
    """

    def __init__(self, master):
        """
        :param master: frame for inserting widgets
        """
        self.frame = Frame(master, padx=10, pady=5)
        self.frame.pack()

        # define variables
        self.abort = IntVar()
        self.abort.set(0)
        self.continuous = IntVar()
        self.continuous.set(0)

        # make big font
        bigfont = tkFont.Font(size=10, weight='bold')

        # make and place widgets
        self.start_exp_button = Button(self.frame, text='Start Exposure',
                                       foreground='blue', height=2, width=15,
                                       font=bigfont, command=self.start_exp)
        self.start_exp_button.grid(row=0, column=0, padx=60)
        self.continuous_button = Button(self.frame,
                                        text='Continuous',
                                        height=2, width=15, font=bigfont,
                                        command=self.cont_exp)
        self.continuous_button.grid(row=0, column=1, padx=5)
        self.grid_scan_button = Button(self.frame, text='Grid Scan',
                                       height=2, width=15, font=bigfont,
                                       command=self.grid_scan)
        self.grid_scan_button.grid(row=0, column=2, padx=5)
        self.quit_button = Button(self.frame, text='Quit', height=2, width=15,
                                  font=bigfont, command=quit_now)
        self.quit_button.grid(row=0, column=3, padx=5)

    def start_exp(self):
        """
        Iterates data collection, file building, and routine for GUI checkboxes
        """
        global abort_window
        prefix.image_no_validation()
        # Ensure file path exists, halt execution if it does not
        if os.path.exists(prefix.pathName.get()):
            pass
        else:
            path_warn()
            return
        # setup abort window
        abort_window = Toplevel()
        xtop = root.winfo_x() + root.winfo_width() / 2 - 150
        ytop = root.winfo_y() + root.winfo_height() / 2 - 150
        abort_window.geometry('300x300+%d+%d' % (xtop, ytop))
        abort_window.title('Working . . .')
        # abort_window.configure(bg='white')
        bigfont = tkFont.Font(size=10, weight='bold')
        label1 = Label(abort_window, text='Data collection in progress')
        label1.pack(side=TOP, pady=10)
        abort_button = Button(abort_window, text='ABORT', height=2,
                              width=15, font=bigfont, bg='red',
                              command=lambda: self.abort.set(1))
        abort_button.pack(pady=20)
        label2 = Label(abort_window,
                            text='Press ONCE and wait '
                                 'patiently to abort data collection')
        label2.pack(pady=10)
        abort_window.grab_set()
        abort_window.lift()
        abort_window.update()
        # define recovery (or abort) values
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
            (xtal3, '_C3', xtal3.collect.get())]
        for sample, c_filebit, xtal_collect in sample_rows:
            if not self.abort.get():
                pass
            else:
                break
            if xtal_collect:
                # if positions are blank (unusual), use current positions
                if not sample.x.get() == '':
                    pass
                else:
                    sample.pos_define()
                    time.sleep(1)
                # move to Cx position for data collection
                sample.move_to()
                # Build partial file name for this Cx
                sample.cs_file_part = prefix.sampleName.get() + '_P' + \
                    prefix.pressureNo.get() + c_filebit
                # Define list for iterating Dx
                detector_rows = [
                    (detCen, '_D1', detCen.collect.get()),
                    (detMin, '_D2', detMin.collect.get()),
                    (detPlus, '_D3', detPlus.collect.get())]
                for position, d_filebit, det_collect in detector_rows:
                    if not self.abort.get():
                        pass
                    else:
                        break
                    if det_collect:
                        # Build partial file name for this Dx
                        position.rot_file_part = sample.cs_file_part + d_filebit
                        # Go to stack- and detector-appropriate routine
                        if config.detector_choice.get() == '1M':
                            position.dc_1m_diffraction()
                        elif config.detector_choice.get() == 'CCD':
                            position.dc_ccd_diffraction()
                        else:
                            pass
                    else:
                        pass
            else:
                pass
        # return to initial positions (or resume continuous collection)
        if not self.continuous.get():
            mX.move(mX_ipos, wait=True)
            mY.move(mY_ipos, wait=True)
            mZ.move(mZ_ipos, wait=True)
            mW.move(mW_ipos, wait=True)
            mDet.move(mDet_ipos, wait=True)
            self.abort.set(0)
            abort_window.destroy()
            tkMessageBox.showinfo('Done', 'Data collection complete')
        elif self.abort.get():
            self.abort.set(0)
            self.continuous.set(0)
            abort_window.destroy()
        else:
            time.sleep(0.1)
            abort_window.destroy()

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
        tkMessageBox.showinfo('Done', 'Data collection complete')

    def grid_scan(self):
        """
        Iterates data collection, file building, and routine for GUI checkboxes
        """
        global abort_window
        prefix.image_no_validation()
        # Ensure file path exists, halt execution if it does not
        if os.path.exists(prefix.pathName.get()):
            pass
        else:
            path_warn()
            return
        # setup abort window and clear any previous abort
        abort_window = Toplevel()
        xtop = root.winfo_x() + root.winfo_width() / 2 - 150
        ytop = root.winfo_y() + root.winfo_height() / 2 - 150
        abort_window.geometry('300x300+%d+%d' % (xtop, ytop))
        abort_window.title('Working . . .')
        bigfont = tkFont.Font(size=10, weight='bold')
        current_index = StringVar()
        label1 = Label(abort_window, text='Data collection in progress')
        label1.pack(side=TOP, pady=10)
        abort_button = Button(abort_window, text='ABORT', height=2,
                              width=15, font=bigfont, bg='red',
                              command=lambda: self.abort.set(1))
        abort_button.pack(pady=20)
        label2 = Label(abort_window,
                            text='Press ONCE and wait '
                                 'patiently to abort data collection')
        label2.pack(pady=10)
        label3 = Label(abort_window, textvariable=current_index)
        label3.pack(pady=10)
        abort_window.grab_set()
        abort_window.lift()
        abort_window.update()
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
            if not self.abort.get():
                pass
            else:
                break
            g_index = zsteps * z_grid.num_steps.get()
            z_rel = z_grid.rel_min.get() + zsteps * z_grid.step_size.get()
            z_abs = mZ_ipos + z_rel
            mZ.move(z_abs, wait=True)
            for ysteps in range(y_grid.num_steps.get()):
                if not self.abort.get():
                    pass
                else:
                    break
                g_index += 1
                g_filebit = str(g_index)
                # display current data point
                total = str(z_grid.num_steps.get() * y_grid.num_steps.get())
                current_index.set('Grid point ' + g_filebit + ' of ' + total)
                abort_window.update_idletasks()
                y_rel = y_grid.rel_min.get() + ysteps * y_grid.step_size.get()
                y_abs = mY_ipos + y_rel
                mY.move(y_abs, wait=True)
                # Build partial file name for this Gx
                g_file_part = prefix.sampleName.get() + '_P' + \
                              prefix.pressureNo.get() + '_G' + g_filebit
                # Define list for iterating Dx
                detector_rows = [
                    (detCen, '_D1', detCen.collect.get()),
                    (detMin, '_D2', detMin.collect.get()),
                    (detPlus, '_D3', detPlus.collect.get())]
                for position, d_filebit, det_collect in detector_rows:
                    if not self.abort.get():
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
                        else:
                            pass
                    else:
                        pass
            else:
                pass
        # return to initial positions (or resume continuous collection)
        mX.move(mX_ipos, wait=True)
        mY.move(mY_ipos, wait=True)
        mZ.move(mZ_ipos, wait=True)
        mW.move(mW_ipos, wait=True)
        mDet.move(mDet_ipos, wait=True)
        self.abort.set(0)
        abort_window.destroy()
        tkMessageBox.showinfo('Done', 'Data collection complete')


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


def path_put(**kwargs):
    prefix.detPath.set(detector.get('FilePath_RBV', as_string=True))

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
# option to load and read custom configuration
if config.use_file.get():
    user_config = tkFileDialog.askopenfile(
        mode='r', title='Please select configuration file')
    exec user_config.read()
    user_config.close()
# hard-encoded configuration options
elif config.stack_choice.get() == 'GPHP':
    mX = Motor('XPSGP:m5')
    mY = Motor('XPSGP:m4')
    mZ = Motor('XPSGP:m3')
    mW = Motor('XPSGP:m2')
    mDet = Motor('16IDB:m6')
    mcs = Struck('16IDB:SIS1:')
    mWpco = Device('XPSGP:m2', pco_args)
    bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
    bnc_channel = 's02'
elif config.stack_choice.get() == 'GPHL':
    mX = Motor('16IDB:m31')
    mY = Motor('16IDB:m32')
    mZ = Motor('16IDB:m5')
    mW = Motor('XPSGP:m1')
    mDet = Motor('16IDB:m6')
    mcs = Struck('16IDB:SIS1:')
    mWpco = Device('XPSGP:m1', pco_args)
    bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
    bnc_channel = 's01'
elif config.stack_choice.get() == 'LH':
    pass
    # mX = Motor('XPSLH:m1')
    # mY = Motor('XPSLH:m2')
    # mZ = Motor('XPSLH:m3')
    # mW = Motor('XPSLH:m4')
    # mDet = Motor('16IDB:m13')
    # mcs = Struck('16IDB:SIS1:')
    # mWpco = Device('XPSLH:m4', pco_args)
    # bnc = PV('16TEST1:cmdReply1_do_IO.AOUT')
    # bnc_channel = 's02'
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
# frameEpics = Frame(root)
# frameEpics.grid(row=0, column=0, sticky='e')
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
detCen = Rotation(frameRotation, idet='Center')
detMin = Rotation(frameRotation, idet='Negative')
detPlus = Rotation(frameRotation, idet='Positive')
xtal1 = CrystalSpot(frameCrystalSpot, label='C1')
xtal2 = CrystalSpot(frameCrystalSpot, label='C2')
xtal3 = CrystalSpot(frameCrystalSpot, label='C3')
y_grid = GridPoints(frameGridPoints, label='Cen Y (horizontal)')
z_grid = GridPoints(frameGridPoints, label='Sam Z (vertical)')
do = Actions(frameControl)

path_put()
root.deiconify()
root.mainloop()

