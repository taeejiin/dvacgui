# Graphical User Interface for the Data Visualization and Analysis of Material Mechanics
# Colin Kang | Greer Group at Caltech

# GUI uses tkinter, pandas, matplotlib, numpy, skicitlearn
import tkinter as tk
from functools import partial
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import pandas as pd
import math
import numpy as np
import gc
import os
import time

# Global CSV interface variables
has_csv_path: bool = False
csv_list: dict = {}
data_frames: dict = {}
alphabet: list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
csv_identities: list = []
index: int = 0

class CSVInterface(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """
        function initializes CSVInterface class upon initializing the program
        :param parent: reference to main frame of the CSVInterface class
        :param args: N/A
        :param kwargs: N/A
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.csv_calculation: dict = {}
        self.csv_label: dict = {}
        self.a_completed: dict = {}
        self.o_completed: dict = {}
        self.a_ready: bool = False
        self.o_ready: bool = False
        self.abscissa_values: dict = {}
        self.ordinate_values: dict = {}
        self.abscissa_buttons: dict = {}
        self.abscissa_drops: dict = {}
        self.ordinate_buttons: dict = {}
        self.ordinate_drops: dict = {}
        self.once_ab: bool = False
        self.once_or: bool = False
        self.can_export_multiplot: bool = False
        self.units_list: dict = {}
        self.create_button('Choose CSV File', self.open_file, 3, 0, 5, 10)
        self.create_button('Parse Cycles (Displacement Controlled)', self.parse_displacement_controlled, 3, 5, 12, 30)
        self.create_button('Parse Cycles (Load Controlled)', self.parse_load_controlled, 3, 17, 9, 27)
        self.create_button('Parse Cycles (Arbitrary Displacement Peak)', self.parse_arbitrary_displacement, 4, 0, 13, 32)
        self.create_button('Parse Cycles (Arbitrary Load Peak)', self.parse_arbitrary_load, 4, 13, 10, 29)
        self.create_button('Refresh Plot-able Options', self.refresh_both, 10, 0, 8, 20)
        self.create_button('Plot All', self.plot_all, 10, 8, 3, 7)
        self.create_button('Export SVG File', self.save_svg, 10, 11, 6, 14)
        self.create_button('Statistics Panel', self.statistics_window, 10, 17, 6, 15)
        self.create_button('Weibull Distribution', self.weibull_window, 10, 23, 8, 20)
        self.multiplot_info()
        self.program_info()
        self.input_domain()
        self.input_range()
        self.xmin_value: float = 0.0
        self.xmax_value: float = 0.0
        self.ymin_value: float = 0.0
        self.ymax_value: float = 0.0
        self.xmin_exists: bool = False
        self.ymin_exists: bool = False
        self.xmax_exists: bool = False
        self.ymax_exists: bool = False

    def unit_storage(self, data: {}):
        """
        function takes the csv data file and iterates through each column and stores the respective unit value for that
        column into units_list; if there is no listed unit, the function leaves it as a visibly null value
        :param data: csv data file user selects from desktop
        :return: list containing corresponding units for each data column entry of csv data file
        """
        num_columns = len(data.columns)
        for x in range(0, num_columns):
            self.units_list[data.columns[x].format(x)] = data.iloc[0, x]
        for i in self.units_list:
            try:
                if math.isnan(self.units_list[i]) is True:
                    self.units_list[i] = 'null'
            except TypeError:
                self.units_list[i] = self.units_list[i]

    def reindex(self, data: {}):
        """
        function takes the csv data file and removes the 0th index of each column (where the unit information is stored
        in the excel file) and changes each value in the data file to float64 (decimal) values because the values are
        previously recognized as strings
        :param data: csv data file user selects from desktop
        :return: data converted to float64 values where each column has its 0th row index removed
        """
        data = data.loc[data.index > 0]
        data = data.reset_index(drop=True)
        for col_name in data.columns:
            try:
                data[col_name] = data[col_name].astype('float64')
            except ValueError:
                data[col_name] = None
        return data

    def re_zero(self, data: {}):
        """
        function takes the csv data file and re-zero displaces it; finds lowest bound to the data, whether it be a
        + or - number, and shifts all data such that the bound is the new zero
        :param data: csv data file user selects from desktop
        :return: data shifted to a new zero value
        """
        for i in data.columns:
            column_edge = data[i].min()
            if column_edge >= 0:
                data[i] = data[i] - column_edge
            elif column_edge < 0:
                data[i] = data[i] + abs(column_edge)
        return data

    def create_button(self, title, call, r, c, cs, w):
        """
        function creates buttons w/ commands for the GUI
        :param title: button's title
        :param call: function called upon mouse-click
        :param r: row
        :param c: column
        :param cs: columnspan
        :param w: width
        :return: customized button
        """
        button = tk.Button(self.parent, text=title, width=w, command=call)
        button.grid(row=r, column=c, columnspan=cs, sticky=tk.EW)

    def create_pop_up(self, arg):
        """
        function creates a pop-up 'Help' window that indicates missing parameters or problems
        :param arg: message displayed in the pop-up window
        :return: pop-up 'Help' window
        """
        pop_up = tk.Toplevel()
        pop_up.title('Help')
        msg = tk.Message(pop_up, text=arg)
        msg.grid(row=0)
        remove_button = tk.Button(pop_up, text="Dismiss", command=pop_up.destroy)
        remove_button.grid(row=1)

    def select_adata(self, n, arg):
        """
        function takes the nth DataFrame based on csv file upload from the user and corresponds the user-selected
        column to an abscissa assignment for plotting
        :param n: nth DataFrame
        :param arg: none
        :return: abscissa column corresponding to nth DataFrame is updated to user-selected column
        """
        df = data_frames[n]
        for col_name in df.columns:
            if col_name == self.abscissa_buttons[n].get():
                self.abscissa_values[n] = col_name
                self.a_completed[n] = True

    def select_odata(self, n, arg):
        """
        function takes the nth DataFrame based on csv file upload from the user and corresponds the user-selected
        column to an ordinate assignment for plotting
        :param n: nth DataFrame
        :param arg: none
        :return: ordinate column corresponding to nth DataFrame is updated to user-selected column
        """
        df = data_frames[n]
        for col_name in df.columns:
            if col_name == self.ordinate_buttons[n].get():
                self.ordinate_values[n] = col_name
                self.o_completed[n] = True

    def refresh_both(self):
        """
        function updates all abscissa & ordinate column selection availability to newest calculations
        :return: column selection with updated options
        """
        for i in range(0, index):
            self.abscissa_buttons[i].set('Select Abscissa')
            self.abscissa_drops[i]['menu'].delete(0, 'end')
            df = data_frames[i]
            column_names = []
            for col_name in df.columns:
                column_names.append(col_name)
            for j in column_names[:]:
                try:
                    u = csv_identities[i].units_list[j]
                except AttributeError:
                    u = self.units_list[j]
                self.abscissa_drops[i]['menu'].add_command(label=j + ' (' + u + ')', command=tk._setit(self.abscissa_buttons[i], j, partial(self.select_adata, i)))

        for w in range(0, index):
            self.ordinate_buttons[w].set('Select Ordinate')
            self.ordinate_drops[w]['menu'].delete(0, 'end')
            df = data_frames[w]
            column_names = []
            for col_name in df.columns:
                column_names.append(col_name)
            for x in column_names[:]:
                try:
                    du = csv_identities[w].units_list[x]
                except AttributeError:
                    du = self.units_list[x]
                self.ordinate_drops[w]['menu'].add_command(label=x + ' (' + du + ')', command=tk._setit(self.ordinate_buttons[w], x, partial(self.select_odata, w)))

    def calc_window(self, n):
        """
        function creates a new Data Calculations sheet corresponding to a specific CSV file selection
        :param n: nth GraphSoftware
        :return: Data Calculations sheet created by GraphSoftware for the particular CSV file
        """
        csv_pop_up = tk.Toplevel()
        csv_pop_up.title('Data Calculations')
        csv_pop_up.geometry('1120x750') # -temp- 1120x750
        frame = ScrollableFrame(csv_pop_up, 1100, 710) # -temp- 1100, 710
        frame.grid(row=0)
        csv_identities[n] = GraphSoftware(frame.scrollable_frame, n)
        csv_identities[n].grid(row=0)
        remove_button = tk.Button(csv_pop_up, text='Dismiss', command=csv_pop_up.destroy)
        remove_button.grid(row=46)

    def statistics_window(self):
        """
        function creates a new Statistics panel sheet that analyzes output values of all CSV files that have been
        processed in their respective Data Calculations sheets
        :return: Statistics Panel sheet for holistic overview of data
        """
        statistics_pop_up = tk.Toplevel()
        statistics_pop_up.title('Statistical Analysis Panel')
        statistics_pop_up.geometry('1195x990') # -temp- 995x790
        frame = ScrollableFrame(statistics_pop_up, 1175, 950) # -temp- 975, 750
        frame.grid()
        statistics_interface = StatisticsInterface(frame.scrollable_frame)
        statistics_interface.grid()

    def weibull_window(self):
        """
        function creates a new Weibull Distribution plot interface that takes the calculated ultimate failure stress
        of each specimen and parameterizes the values to a Weibull distribution
        :return: Weibull Distributions plot interface for holistic failure analysis of material specimens
        """
        weibull_pop_up = tk.Toplevel()
        weibull_pop_up.title('Weibull Distribution Interface')
        weibull_pop_up.geometry('1195x990') # -temp- 995x790
        frame = ScrollableFrame(weibull_pop_up, 1175, 950) # -temp- 975, 750
        frame.grid()
        weibull_interface = WeibullInterface(frame.scrollable_frame)
        weibull_interface.grid()

    def parse_displacement_controlled(self):
        """
        function creates the pop-up window that provides availability for the user to select the most recently
        uploaded CSV file and parse it based on displacement controlled
        :return: parse_displacement_cycles or pop-up
        """
        if has_csv_path is True:
            parse_pop_up = tk.Toplevel()
            parse_pop_up.title('Parse Cycles (Displacement Controlled)')
            self.parse_button = tk.Button(parse_pop_up, text='Parse CSV File ' + str(index),
                                          command=partial(self.parse_displacement_cycles, index-1))
            self.parse_button.grid(row=index-1, column=0, columnspan=3, sticky=tk.W)
        else:
            self.create_pop_up('Add CSV files first.')

    def parse_displacement_cycles(self, r):
        """
        function parses the CSV file's DataFrame into multiple DataFrames that are separated based off displacement
        (displacement has a known peak every time and is constant throughout)
        :param r: rth CSV file
        :return: multiple CSV files rather than the large cycle data file
        """
        global index
        global csv_list
        temp = index
        for i in data_frames[r].columns:
            if 'Displacement' in i:
                displacement_column = i
                break
        self.unit_storage(data_frames[r])
        temp_df = self.reindex(data_frames[r])
        val = int(temp_df[displacement_column].max() * 2)
        nrows = val - 1
        groups = temp_df.groupby(temp_df.index // nrows)
        self.csv_calculation[r].destroy()
        self.abscissa_drops[r].destroy()
        self.ordinate_drops[r].destroy()
        self.csv_label[r].destroy()
        self.a_completed[r] = True
        self.o_completed[r] = True
        del data_frames[r]
        gc.collect()
        for (frameno, frame) in groups:
            csv_list[index] = 'parse'
            csv_calculation = tk.Button(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=10, command=partial(self.calc_window, index))
            csv_calculation.grid(row=2, column=(index * 4), columnspan=4, sticky=tk.EW)
            csv_identities.append(alphabet[index])
            data_frames[index] = frame
            data_frames[index] = data_frames[index].append(pd.Series(), ignore_index=True)
            data_frames[index] = data_frames[index].shift(1)
            data_frames[index].index = range(val)
            for i in data_frames[index].columns:
                data_frames[index].loc[0, i] = self.units_list[i]
            index += 1
            csv_label = tk.Label(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=25)
            csv_label.grid(row=7, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            column_names = []
            for col_name in data_frames[index-1].columns:
                column_names.append(col_name)

            self.a_completed[index-1] = False
            self.abscissa_buttons[index-1] = tk.StringVar(self.parent)
            self.abscissa_buttons[index-1].set('Select Abscissa')
            self.abscissa_drops[index-1] = tk.OptionMenu(self.parent, self.abscissa_buttons[index-1],
                                                           'Select Abscissa', command=lambda *args: None)
            for i in column_names[:]:
                self.abscissa_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.abscissa_buttons[index - 1],
                                                                                     i, partial(self.select_adata,
                                                                                                index - 1)))
            self.abscissa_drops[index-1].grid(row=8, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            self.o_completed[index-1] = False
            self.ordinate_buttons[index-1] = tk.StringVar(self.parent)
            self.ordinate_buttons[index-1].set('Select Ordinate')
            self.ordinate_drops[index-1] = tk.OptionMenu(self.parent, self.ordinate_buttons[index-1],
                                                           'Select Ordinate', command=lambda *args: None)
            for i in column_names[:]:
                self.ordinate_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.ordinate_buttons[index - 1],
                                                                                     i, partial(self.select_odata,
                                                                                                index - 1)))
            self.ordinate_drops[index - 1].grid(row=9, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

    def parse_load_controlled(self):
        """
        function creates the pop-up window that provides availability for the user to select the most recently
        uploaded CSV file and parse it based on load controlled
        :return: parse_load_cycles or pop-up
        """
        if has_csv_path is True:
            parse_pop_up = tk.Toplevel()
            parse_pop_up.title('Parse Cycles (Load Controlled)')
            self.parse_button = tk.Button(parse_pop_up, text='Parse CSV File ' + str(index),
                                          command=partial(self.parse_load_cycles, index-1))
            self.parse_button.grid(row=index-1, column=0, columnspan=3, sticky=tk.W)
        else:
            self.create_pop_up('Add CSV files first.')

    def parse_load_cycles(self, r):
        """
        function parses the CSV file's DataFrame into multiple DataFrames that are separated based off load
        (load has a known peak every time and is constant throughout)
        :param r: rth CSV file
        :return: multiple CSV files rather than the large cycle data file
        """
        global index
        global csv_list
        temp = index
        for i in data_frames[r].columns:
            if 'Load' in i:
                load_column = i
                break
        self.unit_storage(data_frames[r])
        temp_df = self.reindex(data_frames[r])
        val = int(temp_df[load_column].max() * 2)
        nrows = val - 1
        groups = temp_df.groupby(temp_df.index // nrows)
        self.csv_calculation[r].destroy()
        self.abscissa_drops[r].destroy()
        self.ordinate_drops[r].destroy()
        self.csv_label[r].destroy()
        self.a_completed[r] = True
        self.o_completed[r] = True
        del data_frames[r]
        gc.collect()
        for (frameno, frame) in groups:
            csv_list[index] = 'parse'
            csv_calculation = tk.Button(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=10, command=partial(self.calc_window, index))
            csv_calculation.grid(row=2, column=(index * 4), columnspan=4, sticky=tk.EW)
            csv_identities.append(alphabet[index])
            data_frames[index] = frame
            data_frames[index] = data_frames[index].append(pd.Series(), ignore_index=True)
            data_frames[index] = data_frames[index].shift(1)
            data_frames[index].index = range(val)
            for i in data_frames[index].columns:
                data_frames[index].loc[0, i] = self.units_list[i]
            index += 1
            csv_label = tk.Label(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=25)
            csv_label.grid(row=7, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            column_names = []
            for col_name in data_frames[index-1].columns:
                column_names.append(col_name)

            self.a_completed[index-1] = False
            self.abscissa_buttons[index-1] = tk.StringVar(self.parent)
            self.abscissa_buttons[index-1].set('Select Abscissa')
            self.abscissa_drops[index-1] = tk.OptionMenu(self.parent, self.abscissa_buttons[index-1],
                                                           'Select Abscissa', command=lambda *args: None)
            for i in column_names[:]:
                self.abscissa_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.abscissa_buttons[index - 1],
                                                                                     i, partial(self.select_adata,
                                                                                                index - 1)))
            self.abscissa_drops[index-1].grid(row=8, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            self.o_completed[index-1] = False
            self.ordinate_buttons[index-1] = tk.StringVar(self.parent)
            self.ordinate_buttons[index-1].set('Select Ordinate')
            self.ordinate_drops[index-1] = tk.OptionMenu(self.parent, self.ordinate_buttons[index-1],
                                                           'Select Ordinate', command=lambda *args: None)
            for i in column_names[:]:
                self.ordinate_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.ordinate_buttons[index - 1],
                                                                                     i, partial(self.select_odata,
                                                                                                index - 1)))
            self.ordinate_drops[index - 1].grid(row=9, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

    def parse_arbitrary_displacement(self):
        """
        function creates the pop-up window that provides availability for the user to select the most recently
        uploaded CSV file and parse it based on arbitrary (unknown) displacement peaks & minima
        :return: parse_arbitrary_displacement_cycles or pop-up
        """
        if has_csv_path is True:
            parse_pop_up = tk.Toplevel()
            parse_pop_up.title('Parse Cycles (Arbitrary Displacement Peak)')
            self.parse_button = tk.Button(parse_pop_up, text='Parse CSV File ' + str(index),
                                          command=partial(self.parse_arbitrary_displacement_cycles, index-1))
            self.parse_button.grid(row=index-1, column=0, columnspan=3, sticky=tk.W)
        else:
            self.create_pop_up('Add CSV files first')

    def parse_arbitrary_displacement_cycles(self, r):
        """
        function parses the CSV file's DataFrame into multiple DataFrames that are separated based off random
        displacement extrema (peak value is different each time as well as minima)
        :param r: rth CSV file
        :return: multiple CSV files rather than the large cycle data file
        """
        global index
        global csv_list
        temp = index
        for i in data_frames[r].columns:
            if 'Displacement' in i:
                displacement_column = i
                break
        self.unit_storage(data_frames[r])
        temp_df = self.reindex(data_frames[r])

        col = temp_df[displacement_column]
        minima = (col <= col.shift()) & (col < col.shift(-1))
        g = minima.cumsum()
        groups = temp_df.groupby(g)

        self.csv_calculation[r].destroy()
        self.abscissa_drops[r].destroy()
        self.ordinate_drops[r].destroy()
        self.csv_label[r].destroy()
        self.a_completed[r] = True
        self.o_completed[r] = True
        del data_frames[r]
        gc.collect()
        for (frameno, frame) in groups:
            csv_list[index] = 'parse'
            csv_calculation = tk.Button(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=10,
                                        command=partial(self.calc_window, index))
            csv_calculation.grid(row=2, column=(index * 4), columnspan=4, sticky=tk.EW)
            csv_identities.append(alphabet[index])
            data_frames[index] = frame
            data_frames[index] = data_frames[index].append(pd.Series(), ignore_index=True)
            data_frames[index] = data_frames[index].shift(1)
            data_frames[index].index = range(int(frame.size / 2) + 1)
            for i in data_frames[index].columns:
                data_frames[index].loc[0, i] = self.units_list[i]
            index += 1
            csv_label = tk.Label(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=25)
            csv_label.grid(row=7, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

            column_names = []
            for col_name in data_frames[index - 1].columns:
                column_names.append(col_name)

            self.a_completed[index - 1] = False
            self.abscissa_buttons[index - 1] = tk.StringVar(self.parent)
            self.abscissa_buttons[index - 1].set('Select Abscissa')
            self.abscissa_drops[index - 1] = tk.OptionMenu(self.parent, self.abscissa_buttons[index - 1],
                                                           'Select Abscissa', command=lambda *args: None)
            for i in column_names[:]:
                self.abscissa_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.abscissa_buttons[index - 1],
                                                                                     i, partial(self.select_adata,
                                                                                                index - 1)))
            self.abscissa_drops[index - 1].grid(row=8, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

            self.o_completed[index - 1] = False
            self.ordinate_buttons[index - 1] = tk.StringVar(self.parent)
            self.ordinate_buttons[index - 1].set('Select Ordinate')
            self.ordinate_drops[index - 1] = tk.OptionMenu(self.parent, self.ordinate_buttons[index - 1],
                                                           'Select Ordinate', command=lambda *args: None)
            for i in column_names[:]:
                self.ordinate_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.ordinate_buttons[index - 1],
                                                                                     i, partial(self.select_odata,
                                                                                                index - 1)))
            self.ordinate_drops[index - 1].grid(row=9, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

    def parse_arbitrary_load(self):
        """
        function creates the pop-up window that provides availability for the user to select the most recently
        uploaded CSV file and parse it based on arbitrary (unknown) load peaks & minima
        :return: parse_arbitrary_load_cycles or pop-up
        """
        if has_csv_path is True:
            parse_pop_up = tk.Toplevel()
            parse_pop_up.title('Parse Cycles (Arbitrary Load Peak)')
            self.parse_button = tk.Button(parse_pop_up, text='Parse CSV File ' + str(index),
                                          command=partial(self.parse_arbitrary_load_cycles, index-1))
            self.parse_button.grid(row=index-1, column=0, columnspan=3, sticky=tk.W)
        else:
            self.create_pop_up('Add CSV files first')

    def parse_arbitrary_load_cycles(self, r):
        """
        function parses the CSV file's DataFrame into multiple DataFrames that are separated based off random
        load extrema (peak value is different each time as well as minima)
        :param r: rth CSV file
        :return: multiple CSV files rather than the large cycle data file
        """
        global index
        global csv_list
        temp = index
        for i in data_frames[r].columns:
            if 'Load' in i:
                load_column = i
                break
        self.unit_storage(data_frames[r])
        temp_df = self.reindex(data_frames[r])

        col = temp_df[load_column]
        minima = (col <= col.shift()) & (col < col.shift(-1))
        g = minima.cumsum()
        groups = temp_df.groupby(g)

        self.csv_calculation[r].destroy()
        self.abscissa_drops[r].destroy()
        self.ordinate_drops[r].destroy()
        self.csv_label[r].destroy()
        self.a_completed[r] = True
        self.o_completed[r] = True
        del data_frames[r]
        gc.collect()
        for (frameno, frame) in groups:
            csv_list[index] = 'parse'
            csv_calculation = tk.Button(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=10,
                                        command=partial(self.calc_window, index))
            csv_calculation.grid(row=2, column=(index * 4), columnspan=4, sticky=tk.EW)
            csv_identities.append(alphabet[index])
            data_frames[index] = frame
            data_frames[index] = data_frames[index].append(pd.Series(), ignore_index=True)
            data_frames[index] = data_frames[index].shift(1)
            data_frames[index].index = range(int(frame.size / 2) + 1)
            for i in data_frames[index].columns:
                data_frames[index].loc[0, i] = self.units_list[i]
            index += 1
            csv_label = tk.Label(self.parent, text='CSV File ' + str(temp) + alphabet[frameno], width=25)
            csv_label.grid(row=7, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

            column_names = []
            for col_name in data_frames[index - 1].columns:
                column_names.append(col_name)

            self.a_completed[index - 1] = False
            self.abscissa_buttons[index - 1] = tk.StringVar(self.parent)
            self.abscissa_buttons[index - 1].set('Select Abscissa')
            self.abscissa_drops[index - 1] = tk.OptionMenu(self.parent, self.abscissa_buttons[index - 1],
                                                           'Select Abscissa', command=lambda *args: None)
            for i in column_names[:]:
                self.abscissa_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.abscissa_buttons[index - 1],
                                                                                     i, partial(self.select_adata,
                                                                                                index - 1)))
            self.abscissa_drops[index - 1].grid(row=8, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

            self.o_completed[index - 1] = False
            self.ordinate_buttons[index - 1] = tk.StringVar(self.parent)
            self.ordinate_buttons[index - 1].set('Select Ordinate')
            self.ordinate_drops[index - 1] = tk.OptionMenu(self.parent, self.ordinate_buttons[index - 1],
                                                           'Select Ordinate', command=lambda *args: None)
            for i in column_names[:]:
                self.ordinate_drops[index - 1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                                                   command=tk._setit(self.ordinate_buttons[index - 1],
                                                                                     i, partial(self.select_odata,
                                                                                                index - 1)))
            self.ordinate_drops[index - 1].grid(row=9, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

    def open_file(self):
        """
        function allows user to upload new CSV files, and stores the data form the CSV files into DataFrames that are
        organized in dictionaries as well as the units
        :return: new CSV file added to the CSV interface and stored in the dictionary
        """
        global has_csv_path
        global csv_list
        global data_frames
        global csv_identities
        global index
        csv_list[index] = askopenfilename()
        if csv_list[index] == '':
            return
        index += 1
        has_csv_path = True
        if has_csv_path is True:
            self.csv_calculation[index-1] = tk.Button(self.parent, text='CSV File' + str(index), width=10, command=partial(self.calc_window, index-1))
            self.csv_calculation[index-1].grid(row=2, column=(index-1) * 4, columnspan=4, sticky=tk.EW)
            csv_identities.append(alphabet[index-1])
            data_frames[index-1] = pd.read_csv(csv_list[index-1])
            print(data_frames[index-1])
            self.unit_storage(data_frames[index-1])

            self.csv_label[index-1] = tk.Label(self.parent, text='CSV File' + str(index), width=25)
            self.csv_label[index-1].grid(row=7, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            column_names = []
            for col_name in data_frames[index-1].columns:
                column_names.append(col_name)

            self.a_completed[index-1] = False
            self.abscissa_buttons[index-1] = tk.StringVar(self.parent)
            self.abscissa_buttons[index-1].set('Select Abscissa')
            self.abscissa_drops[index-1] = tk.OptionMenu(self.parent, self.abscissa_buttons[index-1], 'Select Abscissa', command=lambda *args: None)
            for i in column_names[:]:
                self.abscissa_drops[index-1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')', command=tk._setit(self.abscissa_buttons[index-1], i, partial(self.select_adata, index-1)))
            self.abscissa_drops[index-1].grid(row=8, column=(index-1) * 10, columnspan=10, sticky=tk.EW)

            self.o_completed[index-1] = False
            self.ordinate_buttons[index-1] = tk.StringVar(self.parent)
            self.ordinate_buttons[index-1].set('Select Ordinate')
            self.ordinate_drops[index-1] = tk.OptionMenu(self.parent, self.ordinate_buttons[index-1], 'Select Ordinate', command=lambda *args: None)
            for i in column_names[:]:
                self.ordinate_drops[index-1]['menu'].add_command(label=i + ' (' + self.units_list[i] + ')', command=tk._setit(self.ordinate_buttons[index-1], i, partial(self.select_odata, index-1)))
            self.ordinate_drops[index-1].grid(row=9, column=(index - 1) * 10, columnspan=10, sticky=tk.EW)

    def multiplot_info(self):
        """
        function outputs labels that give information about the multiple plot functionality of the CSV interface
        :return: informative labels
        """
        multiplot_label = tk.Label(self.parent, text='Plot Multiple Data Files ↓', font='Helvetica 18 bold')
        multiplot_label.grid(row=5, columnspan=10, sticky=tk.W)
        note_label = tk.Label(self.parent, text="Note: for all 'Select Abscissa', select single calculation (e.g. stress, strain, etc.); same for all 'Select Ordinate'")
        note_label.grid(row=6, columnspan=35, sticky=tk.W)

    def program_info(self):
        """
        function outputs labels that give information about the creator, research group, and software
        :return: informative labels
        """
        title_label = tk.Label(self.parent, text='Data Visualization & Calculation GUI', width=30, font='Helvetica 24 bold')
        title_label.grid(row=0, columnspan=20, sticky=tk.W)
        names_label = tk.Label(self.parent, text='By: Colin Kang                                                                ')
        names_label.grid(row=1, columnspan=25, sticky=tk.W)

    def plot_all(self):
        """
        function checks to see if all CSV files have a selected abscissa & ordinate, as well as matching calculations
        being plotted, then outputs a graph containing all CSV files on the same plot
        :return: single plot w/ multiple data sets graphed
        """
        for w in range(0, len(self.a_completed)):
            if self.a_completed[w] is True:
                self.a_ready = True
            else:
                self.a_ready = False
        for x in range(0, len(self.o_completed)):
            if self.o_completed[x] is True:
                self.o_ready = True
            else:
                self.o_ready = False
        if self.a_ready is True and self.o_ready is True:
            self.fig = Figure(figsize=(12, 10), dpi=100) # -temp- 10, 10
            try:
                for i in self.abscissa_values:
                    pa = csv_identities[0].units_list[self.abscissa_values[i]]
                    po = csv_identities[0].units_list[self.ordinate_values[i]]
                    break
            except AttributeError:
                for j in self.abscissa_values:
                    pa = self.units_list[self.abscissa_values[j]]
                    po = self.units_list[self.ordinate_values[j]]
                    break
            for z in self.abscissa_values:
                xl = self.abscissa_values[z]
                yl = self.ordinate_values[z]
                break
            self.fig.subplots_adjust(left=0.1, bottom=0.25, right=0.9, top=0.975)
            self.graph = self.fig.add_subplot(111, xlabel=xl + ' (' + pa + ')', ylabel=yl + ' (' + po + ')')
            self.fig.gca().set_prop_cycle(color=['#8b008b', '#32359a', '#873e41', '#395683', '#573683', '#be00be']) # -temp- RGB cycle for plots
            for i in data_frames:
                df = data_frames[i]
                df = self.reindex(df)
                df = self.re_zero(df)
                self.graph.scatter(df[self.abscissa_values[i]], df[self.ordinate_values[i]], s=7, label='CSV Data File ' + str(i+1)) # -temp- s=0.5
            ax = self.fig.gca()
            ax.xaxis.label.set_size(12.5)
            ax.yaxis.label.set_size(12.5)
            ax.tick_params(axis='x', labelsize=12.5)
            ax.tick_params(axis='y', labelsize=12.5)
            if self.xmin_exists is True and self.xmax_exists is True and self.ymin_exists is True and self.ymax_exists is True:
                ax.set(xlim=(self.xmin_value, self.xmax_value), ylim=(self.ymin_value, self.ymax_value))
            elif self.xmin_exists is True and self.xmax_exists is True:
                ax.set(xlim=(self.xmin_value, self.xmax_value))
            elif self.ymin_exists is True and self.ymax_exists is True:
                ax.set(ylim=(self.ymin_value, self.ymax_value))
            self.graph.legend(loc="upper right", markerscale=2)
            # self.graph.margins(x=0, y=0)
            canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=13, rowspan=36, column=0, columnspan=80, sticky=tk.NW)
            self.can_export_multiplot = True
        else:
            self.create_pop_up("Must have all 'Select Abscissa' and all 'Select Ordinate' selected w/ same calculation for abscissa and ordinate respectively.")

    def save_svg(self):
        """
        function saves the current graph in .svg format
        :return: SVG file
        """
        # TODO: additional export capabilities than just SVG for graphs
        '''
        self.fig.savefig(
            '/Users/colinkang/Desktop/' + self.ordinate + ' (' + self.units_list[self.ordinate] + ') vs. ' + self.abscissa + ' (' +
            self.units_list[self.abscissa] + ')', format='svg')
        '''
        if self.can_export_multiplot is True:
            my_path = os.path.abspath(__file__)
            base = os.path.basename(__file__)
            new_path = my_path.replace(base, '')
            my_file = self.ordinate + ' (' + self.units_list[self.ordinate] + ') vs. ' + self.abscissa + ' (' + \
                      self.units_list[self.abscissa] + ')'
            self.fig.savefig(os.path.join(new_path, my_file), format='svg')
        else:
            self.create_pop_up('First plot.')

    def input_domain(self):
        """
        function has user input a specific domain that is stored into the bounds for plotting
        :return: x-axis bounds for the data being plotted
        """
        self.user_input_label_domain = tk.Label(self.parent, text="Enter domain:")
        self.user_input_label_domain.grid(row=11, column=0, columnspan=4, sticky=tk.E)

        def callback(xmin):
            self.xmin_value = float(xmin.get())
            self.xmin_exists = True

        xmin = tk.DoubleVar()
        self.user_input_xmin = tk.Entry(self.parent, textvariable=xmin)
        self.user_input_xmin.bind('<Return>', (lambda _: callback(self.user_input_xmin)))
        self.user_input_xmin.grid(row=11, column=4, columnspan=10, sticky=tk.W)

        def callback2(xmax):
            self.xmax_value = float(xmax.get())
            self.xmax_exists = True

        xmax = tk.DoubleVar()
        self.user_input_xmax = tk.Entry(self.parent, textvariable=xmax)
        self.user_input_xmax.bind('<Return>',(lambda _: callback2(self.user_input_xmax)))
        self.user_input_xmax.grid(row=11, column=14, columnspan=10, sticky=tk.W)

    def input_range(self):
        """
        function has user input a specific range that is stored into the bounds for plotting
        :return: y-axis bounds for the data being plotted
        """
        self.user_input_label_range = tk.Label(self.parent, text="Enter range:")
        self.user_input_label_range.grid(row=12, column=0, columnspan=4, sticky=tk.E)

        def callback(ymin):
            self.ymin_value = float(ymin.get())
            self.ymin_exists = True

        ymin = tk.DoubleVar()
        self.user_input_ymin = tk.Entry(self.parent, textvariable=ymin)
        self.user_input_ymin.bind('<Return>', (lambda _: callback(self.user_input_ymin)))
        self.user_input_ymin.grid(row=12, column=4, columnspan=10, sticky=tk.W)

        def callback2(ymax):
            self.ymax_value = float(ymax.get())
            self.ymax_exists = True

        ymax = tk.DoubleVar()
        self.user_input_ymax = tk.Entry(self.parent, textvariable=ymax)
        self.user_input_ymax.bind('<Return>', (lambda _: callback2(self.user_input_ymax)))
        self.user_input_ymax.grid(row=12, column=14, columnspan=10, sticky=tk.W)


class WeibullInterface(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """
        function initializes WeibullInterface class upon initializing the call to the interface
        :param parent: reference to main frame of the WeibullInterface class
        :param args: N/A
        :param kwargs: N/A
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.title()
        self.strength_sort: list = []
        self.ln_strength_sort: list = [] # X-axis
        self.probability_sort: list = []
        self.double_ln_probability_sort: list = [] # Y-axis
        self.reorder_failure_stresses()
        self.strength_natural_log()
        self.failure_probability()
        self.double_natural_log()
        self.plot_weibull()
        self.create_header('Weibull Modulus: ' + str("%.4f" % self.weibull_modulus) + ' | Characteristic Strength: ' + str("%.4f" % self.characteristic_strength) + ' (' + csv_identities[0].stress_pascal_unit + ')', 1)

    def title(self):
        """
        function outputs title for weibull distributions interface
        :return: title label
        """
        title_label = tk.Label(self.parent, text='Weibull Distributions', font='Helvetica 24 bold')
        title_label.grid(row=0)

    def create_header(self, title, r):
        """
        function creates headers for the GUI organizing calculation parameters & outputs
        :param title: header's title
        :param r: row
        :return: customized header
        """
        header = tk.Label(self.parent, text=title, font='Helvetica 18 bold')
        header.grid(row=r)

    def reorder_failure_stresses(self):
        """
        function numerically sorts the previously calculated ultimate failure stresses in increasing value
        :return: array of sorted ultimate failure stresses
        """
        s = []
        for i in range(0, len(csv_identities)):
            s.append(csv_identities[i].ultimate_stress_value)
        self.strength_sort = np.sort(s)

    def strength_natural_log(self):
        """
        function elementally calculates the natural log of the strength sort array
        :return: natural log manipulation of the strength sort array
        """
        self.ln_strength_sort = np.log(self.strength_sort)

    def failure_probability(self):
        """
        function calculates the probability of failure using the following datum manipulation:
            P_failure(stress_i) = (i - 0.5) / N
            where the stress values are ranked in increasing order from i = 1, 2, 3, ..., N such that N is the total number of specimens and i is the ith datum
        :return: array of sorted failure probabilities
        """
        for i in range(0, len(csv_identities)):
            self.probability_sort.append(((i + 1) - 0.5) / len(csv_identities))

    def double_natural_log(self):
        """
        function elementally calculates an inverted double log of the sorted failure probabilities array
        :return: inverse probability array one order of natural log different that the natural log manipulation of the strength sort array
        """
        t = []
        for i in range(0, len(self.probability_sort)):
            t.append(1 / (1 - self.probability_sort[i]))
        self.double_ln_probability_sort = np.log(np.log(t))

    def plot_weibull(self):
        """
        functions returns a 4-axis plot with the following features:
            1st-X-axis: ln Stress
            2nd-X-axis: Fracture Stress (MPa)
            1st-Y-axis: ln ln (1 / (1 - Probability of Fracture))
            2nd-Y-axis: Probability of Fracture (%)
        note: we take natural log and a double natural log in order to perform a linear regression
        analysis of the weibull distribution and calculate the characteristic strenght and weibull modulus
        :return: plot w/ aforementioned features
        """
        self.fig = Figure(figsize=(12, 10), dpi=100)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        self.ax3 = self.ax1.twiny()
        self.ax1.scatter(self.ln_strength_sort, self.double_ln_probability_sort)
        self.weibull_modulus, self.b_val = np.polyfit(self.ln_strength_sort, self.double_ln_probability_sort, 1)
        self.ax1.plot(self.ln_strength_sort, self.weibull_modulus*self.ln_strength_sort + self.b_val)
        self.characteristic_strength = math.exp(self.b_val / self.weibull_modulus * -1)
        self.ax1.set_xlabel('ln Stress')
        self.ax1.set_ylabel('ln ln (1 / (1 - Probability of Fracture))')
        self.ax2.set_ylabel('Probability of Fracture (%)')
        self.ax3.set_xlabel('Fracture Stress' + ' (' + csv_identities[0].stress_pascal_unit + ')')
        self.y_manip = lambda y_o: 1 - (1 / math.exp(math.exp(y_o)))
        self.ax1_ymin, self.ax1_ymax = self.ax1.get_ylim()
        self.ax2.set_ylim(self.y_manip(self.ax1_ymin), self.y_manip(self.ax1_ymax))
        self.ax2.plot([], [])
        self.x_manip = lambda x_o: math.exp(x_o)
        self.ax1_xmin, self.ax1_xmax = self.ax1.get_xlim()
        self.ax3.set_xlim(self.x_manip(self.ax1_xmin), self.x_manip(self.ax1_xmax))
        self.ax3.plot([], [])
        canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=2)


class StatisticsInterface(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """
        function initializes StatisticsInterface class upon initializing the program
        :param parent: reference to main frame of the StatisticsInterface class
        :param args: N/A
        :param kwargs: N/A
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.program_info()
        self.one_dimensional_data()
        self.multi_dimensional_data()
        self.calculate_means()
        self.calculate_medians()
        self.calculate_std()
        self.calculate_variance()
        self.calculate_IQR()
        self.calculate_num_outliers()
        self.plot_boxplots(0, "Young's Modulus (Slope)", csv_identities[0].stress_pascal_unit)
        self.plot_boxplots(1, "Young's Modulus (CSM)", csv_identities[0].csm_pascal_unit)
        self.plot_boxplots(2, "Young's Modulus (Sneddon)", csv_identities[0].sneddon_pascal_unit)
        self.plot_boxplots(3, "Energy Dissipation", csv_identities[0].stress_pascal_unit)
        self.plot_boxplots(4, "Burst Events (Size)", "")
        self.plot_boxplots(5, "Burst Events (Number)", "")
        self.plot_boxplots(6, "Ultimate Failure (Stress)", csv_identities[0].stress_pascal_unit)
        self.plot_boxplots(7, "Ultimate Failure (Strain)", "")

    def program_info(self):
        """
        function outputs labels that give information about statistics analysis panel
        :return: informative labels
        """
        title_label = tk.Label(self.parent, text='Statistics Analysis Panel', font='Helvetica 24 bold')
        title_label.grid(row=0, columnspan=14, sticky=tk.W)
        description_label = tk.Label(self.parent, text='Statistical treatment for calculated data sets of all CSV data files observed')
        description_label.grid(row=1, columnspan=28, sticky=tk.W)
        note_label = tk.Label(self.parent, text='*Note*: the units for all statistical values are not labeled, so refer to the data calculation sheet for units')
        note_label.grid(row=2, columnspan=42, sticky=tk.W)

    def one_dimensional_data(self):
        """
        function outputs 1D data labels: E (slope), E (CSM), E(Sneddon), eneryg dissipation
        :return: 1D data labels
        """
        # statistical_measures_label = tk.Label(self.parent, text="          Mean                          Median              Standard Deviation             Variance              Interquartile Range           Outliers (#)")
        # statistical_measures_label.grid(row=3, column=10, columnspan=62, sticky=tk.E)
        types = ["Mean", "Median", "Standard Deviation", "Variance", "Interquartile Range", "Outliers"]
        for i in range(0, len(types)):
            type_label = tk.Label(self.parent, text=types[i], width=15)
            type_label.grid(row=3, column=10 + (6*i), columnspan=6, sticky=tk.NW)
        e_slope_label = tk.Label(self.parent, text="Young's Modulus (Slope)    |  ")
        e_slope_label.grid(row=4, columnspan=10, sticky=tk.E)
        e_csm_label = tk.Label(self.parent, text="Young's Modulus (CSM)      |  ")
        e_csm_label.grid(row=5, columnspan=10, sticky=tk.E)
        e_sneddon_label = tk.Label(self.parent, text="Young's Modulus (Sneddon)  |  ")
        e_sneddon_label.grid(row=6, columnspan=10, sticky=tk.E)
        energy_dissipated_label = tk.Label(self.parent, text="Energy Dissipation         |  ")
        energy_dissipated_label.grid(row=7, columnspan=10, sticky=tk.E)

    def multi_dimensional_data(self):
        """
        function outputs multi-dimensional data labels: burst behavior, stress and strain at failure
        :return: multi-dimensional data labels
        """
        bursts_size_label = tk.Label(self.parent, text="Burst Events (Size)         |  ")
        bursts_size_label.grid(row=8, columnspan=10, sticky=tk.E)
        bursts_number_label = tk.Label(self.parent, text="Burst Events (Number)      |  ")
        bursts_number_label.grid(row=9, columnspan=10, sticky=tk.E)
        u_stress_label = tk.Label(self.parent, text="Ultimate Failure (Stress)  |  ")
        u_stress_label.grid(row=10, columnspan=10, sticky=tk.E)
        u_strain_label = tk.Label(self.parent, text="Ultimate Failure (Strain)  |  ")
        u_strain_label.grid(row=11, columnspan=10, sticky=tk.E)

    def calculate_means(self):
        def mean(n):
            u = 0.0
            for i in range(0, len(csv_identities)):
                if n == 0:
                    u += csv_identities[i].youngs_modulus_value_slope
                if n == 1:
                    u += csv_identities[i].youngs_modulus_value_csm
                if n == 2:
                    u += csv_identities[i].youngs_modulus_value_sneddon
                if n == 3:
                    u += csv_identities[i].energy_dissipated_value
                if n == 4:
                    print("not functional") # -temp-
                if n == 5:
                    u += csv_identities[i].num_bursts_value
                if n == 6:
                    u += csv_identities[i].ultimate_stress_value
                if n == 7:
                    u += csv_identities[i].ultimate_strain_value
            return float("{:.4f}".format(u / len(csv_identities)))

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(mean(i)), width=15)
            output.grid(row=4+i, column=10, columnspan=6, sticky=tk.NW)

    def calculate_medians(self):
        def median(n):
            l = []
            u = 0.0
            if n == 0:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_slope)
                u = np.median(l)
            if n == 1:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_csm)
                u = np.median(l)
            if n == 2:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_sneddon)
                u = np.median(l)
            if n == 3:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].energy_dissipated_value)
                u = np.median(l)
            if n == 4:
                print("not functional") # -temp-
            if n == 5:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].num_bursts_value)
                u = np.median(l)
            if n == 6:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_stress_value)
                u = np.median(l)
            if n == 7:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_strain_value)
                u = np.median(l)
            return float("{:.4f}".format(u))

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(median(i)), width=15)
            output.grid(row=4+i, column=16, columnspan=6, sticky=tk.NW)

    def calculate_std(self):
        def std(n):
            l = []
            u = 0.0
            if n == 0:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_slope)
                u = np.std(l)
            if n == 1:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_csm)
                u = np.std(l)
            if n == 2:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_sneddon)
                u = np.std(l)
            if n == 3:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].energy_dissipated_value)
                u = np.std(l)
            if n == 4:
                print("not functional")  # -temp-
            if n == 5:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].num_bursts_value)
                u = np.std(l)
            if n == 6:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_stress_value)
                u = np.std(l)
            if n == 7:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_strain_value)
                u = np.std(l)
            return float("{:.4f}".format(u))

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(std(i)), width=15)
            output.grid(row=4 + i, column=22, columnspan=6, sticky=tk.NW)

    def calculate_variance(self):
        def variance(n):
            l = []
            u = 0.0
            if n == 0:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_slope)
                u = np.var(l)
            if n == 1:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_csm)
                u = np.var(l)
            if n == 2:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_sneddon)
                u = np.var(l)
            if n == 3:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].energy_dissipated_value)
                u = np.var(l)
            if n == 4:
                print("not functional")  # -temp-
            if n == 5:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].num_bursts_value)
                u = np.var(l)
            if n == 6:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_stress_value)
                u = np.var(l)
            if n == 7:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_strain_value)
                u = np.var(l)
            return float("{:.4f}".format(u))

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(variance(i)), width=15)
            output.grid(row=4 + i, column=28, columnspan=6, sticky=tk.NW)

    def calculate_IQR(self):
        def iqr(n):
            l = []
            u = 0.0
            if n == 0:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_slope)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 1:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_csm)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 2:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_sneddon)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 3:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].energy_dissipated_value)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 4:
                print("not functional")  # -temp-
            if n == 5:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].num_bursts_value)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 6:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_stress_value)
                u = np.subtract(*np.percentile(l, [75, 25]))
            if n == 7:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_strain_value)
                u = np.subtract(*np.percentile(l, [75, 25]))
            return float("{:.4f}".format(u))

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(iqr(i)), width=15)
            output.grid(row=4 + i, column=34, columnspan=6, sticky=tk.NW)

    def calculate_num_outliers(self):
        def num_outliers(n):
            l = []
            u = 0.0
            if n == 0:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_slope)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 1:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_csm)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 2:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].youngs_modulus_value_sneddon)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 3:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].energy_dissipated_value)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 4:
                print("not functional")  # -temp-
            if n == 5:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].num_bursts_value)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 6:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_stress_value)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            if n == 7:
                for i in range(0, len(csv_identities)):
                    l.append(csv_identities[i].ultimate_strain_value)
                l = np.array(l)
                z = l[(l > np.quantile(l, 0.1)) & (l < np.quantile(l, 0.9))].tolist()
                u = len(np.array(l)) - len(np.array(z))
            return u

        for i in range(0, 8):
            output = tk.Label(self.parent, text=str(num_outliers(i)), width=15)
            output.grid(row=4 + i, column=40, columnspan=6, sticky=tk.NW)

    def plot_boxplots(self, n, str, unit):
        l = []
        for i in range(0, len(csv_identities)):
            if n == 0:
                l.append(csv_identities[i].youngs_modulus_value_slope)
            if n == 1:
                l.append(csv_identities[i].youngs_modulus_value_csm)
            if n == 2:
                l.append(csv_identities[i].youngs_modulus_value_sneddon)
            if n == 3:
                l.append(csv_identities[i].energy_dissipated_value)
            if n == 4:
                l.append(csv_identities[i].burst_size)
            if n == 5:
                l.append(csv_identities[i].num_bursts_value)
            if n == 6:
                l.append(csv_identities[i].ultimate_stress_value)
            if n == 7:
                l.append(csv_identities[i].ultimate_strain_value)
        data = np.array(l).astype('float64')

        self.fig = Figure(figsize=(3, 3), dpi=100)
        self.fig.subplots_adjust(left=0.25, bottom=0.25)
        self.graph = self.fig.add_subplot(111, xlabel=str + " (" + unit + ")")
        self.graph.boxplot(data)
        canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        canvas.draw()
        if n == 0 or n == 1 or n == 2 or n == 3:
            canvas.get_tk_widget().grid(row=12, column=0 + (13 * n), columnspan=13, sticky=tk.NW)
        if n == 4 or n == 5 or n == 6 or n == 7:
            canvas.get_tk_widget().grid(row=13, column=-52 + (13 * n), columnspan=13, sticky=tk.NW)


class Scrollable(tk.Frame):
    def __init__(self, parent, **kwargs):
        """
        function initializes a miniature frame that is scrollable for activities like burst events output
        NOTE: adapted from https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
        :param parent: class object inheriting the Scrollable class as it's frame
        :param kwargs: additional keyword arguments in the future
        """
        tk.Frame.__init__(self, parent, **kwargs)
        self.vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.vsb2 = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.vsb2.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.vsb2.set)
        self.vsb.configure(command=self.canvas.yview)
        self.vsb2.configure(command=self.canvas.xview)
        self.scrolled_frame = tk.Frame(self.canvas, background=self.canvas.cget('bg'))
        self.canvas.create_window((4, 4), window=self.scrolled_frame, anchor=tk.NW)
        self.scrolled_frame.bind("<Configure>", self.on_configure)

    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class ScrollableFrame(tk.Frame):
    def __init__(self, container, width, height, *args, **kwargs):
        """
        function initializes a miniature frame that is scrollable for activities like burst events output
        function scrolls in both x-direction & y-direction
        NOTE: adapted from https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
        :param container: widgets being held in frame
        :param width: width of canvas
        :param height: height of canvas
        :param args: additional arguments for future
        :param kwargs: additional keyword arguments for future
        """
        super().__init__(container, *args, **kwargs)
        self.width = width
        self.height = height
        canvas = tk.Canvas(self, bd=-3)
        canvas.config(width=self.width, height=self.height)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        horiz = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=canvas.xview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox(tk.ALL)
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        canvas.configure(xscrollcommand=horiz.set, yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        horiz.grid(row=1, column=0, sticky=tk.EW)


class GraphSoftware(tk.Frame):
    def __init__(self, parent, csv_index, *args, **kwargs):
        """
        function initializes Graph Software class upon creating master parent and selecting a csv file from desktop
        :param parent: reference to the main frame of the Graph Software class
        :param args: N/A
        :param kwargs: N/A
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.csv_index = csv_index
        self.csm_s: bool = False
        self.csm_e: bool = False
        self.ss: bool = False
        self.se: bool = False
        self.a: bool = False
        self.o: bool = False
        self.l: bool = False
        self.d: bool = False
        self.csm: bool = False
        self.s: bool = False
        self.h: bool = False
        self.can_export: bool = False
        self.poisson_exists: bool = False
        self.known_elastic_modulus_exists: bool = False
        self.specimen_area: float = 0.0
        self.specimen_height: float = 0.0
        self.strain_start: float = 0.0
        self.strain_end: float = 0.0
        self.csm_start: float = 0.0
        self.csm_end: float = 0.0
        self.poisson_ratio: float = 0.0
        self.known_elastic_modulus: float = 0.0
        self.youngs_modulus_value_slope: float = 0.0
        self.youngs_modulus_value_csm: float = 0.0
        self.youngs_modulus_value_sneddon: float = 0.0
        self.ultimate_stress_value: float = 0.0
        self.ultimate_strain_value: float = 0.0
        self.energy_dissipated_value: float = 0.0
        self.num_bursts_value: float = 0.0
        self.area_conservation: bool = False
        self.volume_conservation: bool = False
        self.compute_stress: bool = False
        self.compute_strain: bool = False
        self.compute_yms: bool = False
        self.compute_ymcsm: bool = False
        self.compute_true_stress: bool = False
        self.compute_true_strain: bool = False
        self.compute_sneddon: bool = False
        self.compute_uss: bool = False
        self.compute_energy_dissipated: bool = False
        self.compute_bursts: bool = False
        self.abscissa: str = ''
        self.ordinate: str = ''
        self.load_column: str = ''
        self.displacement_column: str = ''
        self.csm_column: str = ''
        self.stress_pascal_unit: str = ''
        self.csm_pascal_unit: str = ''
        self.sneddon_pascal_unit: str = ''
        self.units_list: dict = {}
        self.xmin_value: float = 0.0
        self.xmax_value: float = 0.0
        self.ymin_value: float = 0.0
        self.ymax_value: float = 0.0
        self.xmin_exists: bool = False
        self.ymin_exists: bool = False
        self.xmax_exists: bool = False
        self.ymax_exists: bool = False
        self.large_diff: list = []
        self.burst_stress_strain: list = []
        self.toggle_bursts: bool = False
        self.burst_size: list = []
        self.stress_type: str = ''
        self.strain_type: str = ''
        self.type_exists: bool = False
        self.open_file()

    def idle(self):
        """
        function that maintains current button state while button is idle
        :return: nothing
        """
        return

    def open_file(self):
        """
        function calls the CSV file the user selects to initialize a new Data Calculations sheet
        :return: Data Calculations sheet for specific CSV file
        """
        self.store_units()
        self.select_abscissa_button()
        self.select_ordinate_button()
        self.input_specimen_area()
        self.input_specimen_height()
        self.input_strain_range()
        self.input_csm_range()
        self.input_poisson_ratio()
        self.input_known_elastic_modulus()
        self.check_area_or_volume_conservation()
        self.check_engineering_or_true_stress_strain()
        self.create_button('Refresh Options', self.refresh, 44, 0, 2)
        self.select_load_button()
        self.select_displacement_button()
        self.select_csm_button()
        self.create_header("Stress Calculations (Engineering) ↓", 1, 0, 5)
        self.create_header("Stress Calculations (True) ↓", 1, 7, 5)
        self.create_button('Calculate True Stress', self.can_compute_true_stress, 2, 10, 1)
        self.create_header("Strain Calculations (Engineering) ↓", 4, 0, 5)
        self.create_header("Strain Calculations (True) ↓", 4, 7, 5)
        self.create_button('Calculate True Strain', self.can_compute_true_strain, 5, 10, 1)
        self.create_header("Young's Modulus (Slope Method) ↓", 7, 0, 5)
        self.create_button("Calculate Young's Modulus (Slope)", self.can_compute_yms, 10, 3, 5)
        self.create_header("Young's Modulus (CSM Method) ↓", 12, 0, 5)
        self.create_button("Calculate Young's Modulus (CSM)", self.can_compute_ymcsm, 17, 3, 5)
        self.output_values("Young's Modulus Value (slope):", 11, 0, 4)
        self.output_values("Young's Modulus Value (CSM):", 18, 0, 4)
        self.output_values("Young's Modulus Value (Sneddon):", 23, 0, 4)
        self.create_header("Sneddon's Correction to CSM ↓", 19, 0, 5)
        self.create_button("Calculate Young's Modulus w/ Sneddon Correction", self.can_compute_sneddon, 22, 3, 8)
        self.create_header("Ultimate Failure Stress & Strain ↓", 24, 0, 5)
        self.output_values("Approximated Stress:", 25, 0, 3)
        self.output_values("Approximated Strain:", 26, 0, 3)
        self.create_button("Calculate Ultimate Failure Stress & Strain", self.can_compute_uss, 27, 3, 7)
        self.create_header("Energy Dissipation ↓", 28, 0, 3)
        self.output_values("Energy dissipated:", 29, 0, 3)
        self.create_button("Calculate Energy Dissipated", self.can_compute_energy_dissipated, 30, 3, 5)
        self.create_header("Burst Events ↓", 31, 0, 2)
        self.create_button("Calculate Burst Values", self.can_compute_bursts, 32, 3, 4)
        self.output_values("Number of bursts:", 33, 0, 3)
        self.create_button('Export SVG File', self.save_svg, 45, 0, 2)
        self.input_domain()
        self.input_range()
        self.scrolling_output()

    def scrolling_output(self):
        """
        function gives initial output of the Burst Events category before any burst events are calculated
        :return: empty scrolling frame w/ no values or information
        """
        self.sbf = Scrollable(self.parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sbf.grid(row=34, rowspan=10, column=0, columnspan=5, sticky=tk.E)
        self.frame = self.sbf.scrolled_frame
        tk.Label(self.frame, text='No information available.').grid(row=0, column=0)

    def burst_information(self):
        """
        function outputs the lower & upper bound stress-strain at bursts, size of bursts, for each burst calculated
        :return: scrolling frame with information on each burst event in the material
        """
        self.bs = Scrollable(self.parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.bs.grid(row=34, rowspan=10, column=0, columnspan=5, sticky=tk.E)
        self.hold = self.bs.scrolled_frame
        for r in range(0, len(self.burst_stress_strain), 4):
            tk.Label(self.hold, text= str(int(r/4)+1) + ' | Lower Bound').grid(row=int((5/4)*r), column=0, sticky=tk.W)
            tk.Label(self.hold, text='    Stress (' + self.stress_pascal_unit + '): ' + str(float("{:.3f}".format(self.burst_stress_strain[r]))) + ' Strain: ' + str(float("{:.3f}".format(self.burst_stress_strain[r+1])))).grid(row=int((5/4)*r)+1, sticky=tk.W)
            tk.Label(self.hold, text='    Upper Bound').grid(row=int((5/4)*r)+2, column=0, sticky=tk.W)
            tk.Label(self.hold, text='    Stress: (' + self.stress_pascal_unit + '): ' + str(float("{:.3f}".format(self.burst_stress_strain[r+2]))) + ' Strain: ' + str(float("{:.3f}".format(self.burst_stress_strain[r+3])))).grid(row=int((5/4)*r)+3, sticky=tk.W)
            tk.Label(self.hold, text='    Size (strain range): ' + str(float("{:.3f}".format(self.burst_size[int(r/4)])))).grid(row=int((5/4)*r)+4, sticky=tk.W)

    def both_selected(self):
        """
        functions plots graph if both abscissa and ordinate are selected by user
        :return: plot or idle
        """
        if self.a is True and self.o is True:
            self.plot()
        else:
            self.idle()

    def store_units(self):
        """
        functions adds each unit from each column to units_list
        :return: updated units_list
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        self.unit_storage(data_frames[self.csv_index])

    def unit_storage(self, data: {}):
        """
        function takes the csv data file and iterates through each column and stores the respective unit value for that
        column into units_list; if there is no listed unit, the function leaves it as a visibly null value
        :param data: csv data file user selects from desktop
        :return: list containing corresponding units for each data column entry of csv data file
        """
        num_columns = len(data.columns)
        for x in range(0, num_columns):
            self.units_list[data.columns[x].format(x)] = data.iloc[0, x]
        for i in self.units_list:
            try:
                if math.isnan(self.units_list[i]) is True:
                    self.units_list[i] = 'null'
            except TypeError:
                self.units_list[i] = self.units_list[i]

    def reindex(self, data: {}):
        """
        function takes the csv data file and removes the 0th index of each column (where the unit information is stored
        in the excel file) and changes each value in the data file to float64 (decimal) values because the values are
        previously recognized as strings
        :param data: csv data file user selects from desktop
        :return: data converted to float64 values where each column has its 0th row index removed
        """
        data = data.loc[data.index > 0]
        data = data.reset_index(drop=True)
        for col_name in data.columns:
            try:
                data[col_name] = data[col_name].astype('float64')
            except ValueError:
                data[col_name] = None
        return data

    def re_zero(self, data: {}):
        """
        function takes the csv data file and re-zero displaces it; finds lowest bound to the data, whether it be a
        + or - number, and shifts all data such that the bound is the new zero
        :param data: csv data file user selects from desktop
        :return: data shifted to a new zero value
        """
        for i in data.columns:
            column_edge = data[i].min()
            if column_edge >= 0:
                data[i] = data[i] - column_edge
            elif column_edge < 0:
                data[i] = data[i] + abs(column_edge)
        return data

    def engineering_stress(self, data: {}):
        """
        function calculates engineering stress given the load (in mN) and the initial area cross-sectional area (in nm^2)
        that the user provides
            general calculation: engineering stress = load / initial cross-sectional area
        :param data: csv data file user selects from desktop
        :return: new graphable data column called Stress (Engineerning) and auto-calculated corresponding unit (_Pa)
        appended to units_list
        """
        start = time.time()
        data['Stress (Engineering)'] = data[self.load_column] / self.specimen_area * 1000000000000000
        data['Stress (Engineering)'].astype('float64')
        n = data['Stress (Engineering)'].mean()

        if n > 0.0:
            log_value = int(math.log10(n))
        elif n == 0.0:
            log_value = 0.0
        else:
            log_value = int(math.log10(-n)) + 1

        if 0 <= log_value <= 1:
            self.stress_pascal_unit = 'Pa'
        elif 2 <= log_value <= 4:
            data['Stress (Engineering)'] = data['Stress (Engineering)'] / 1000
            self.stress_pascal_unit = 'kPa'
        elif 5 <= log_value <= 7:
            data['Stress (Engineering)'] = data['Stress (Engineering)'] / 1000000
            self.stress_pascal_unit = 'MPa'
        elif 8 <= log_value <= 10:
            data['Stress (Engineering)'] = data['Stress (Engineering)'] / 1000000000
            self.stress_pascal_unit = 'GPa'
        elif 11 <= log_value <= 13:
            data['Stress (Engineering)'] = data['Stress (Engineering)'] / 1000000000000
            self.stress_pascal_unit = 'TPa'
        else:
            data['Stress (Engineering)'] = data['Stress (Engineering)'] / 1000000000000000
            self.stress_pascal_unit = 'PPa'

        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = self.stress_pascal_unit
        end = time.time()
        print('Engineering stress time: ' + str(end-start))
        return data

    def true_stress(self, data: {}):
        """
        function calculates true stress given initial specimen height (in nm) and displacement (deformation) (in nm)
            calculation: true stress = engineering stress * ((initial height + displacement) / initial height)
        :param data: csv data file user selects from desktop
        :return: new graphable data column called Stress (True) and and _Pa appended to units_list
        """
        start = time.time()
        data['Stress (True)'] = data['Stress (Engineering)'] * (
                (self.specimen_height + data[self.displacement_column]) / self.specimen_height)
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = self.stress_pascal_unit
        end = time.time()
        print('True stress time: ' + str(end-start))
        return data

    def engineering_strain(self, data: {}):
        """
        function calculates engineering strain given the displacement (deformation) (in nm) and the initial specimen height
        (in nm) that the user provides
            general calculation: engineering strain = displacement / initial height
        :param data: csv data file user selects from desktop
        :return: new graphable data column called Strain (Engineering) and % appended to units_list
        """
        # TODO: figure out why strain calculation is off by a decimal (e.g. should be 0.05 but get 0.5)
        start = time.time()
        data['Strain (Engineering)'] = data[self.displacement_column] / self.specimen_height
        data['Strain (Engineering)'].astype('float64')
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = ''
        end = time.time()
        print('Engineering strain time: ' + str(end-start))
        return data

    def true_strain(self, data: {}):
        """
        function calculations true strain given the displacement (deformation) (in nm) and the initial specimen height
        (in nm) that the user provides
            calculation: true strain = ln(displacement / initial height)
        :param data: csv data file user selects from desktop
        :return: new graphable data column called Strain (True) and % appended to units_list
        """
        start = time.time()
        data['Strain (True)'] = np.log((self.specimen_height + data[self.displacement_column]) / self.specimen_height)
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = ''
        end = time.time()
        print('True strain time: ' + str(end-start))
        return data

    def ultimate_stress(self, data: {}):
        """
        function essentially checks size of differences between each strain data point, and finds the index of the
        first difference that meets criteria for a large enough difference to result in failure of the material
        :param data: csv data file user selects from desktop
        :return: ultimate stress value in _Pa
        """
        '''
        idx = data[self.strain_type].diff().idxmax() - 1
        self.ultimate_stress_value = data['Stress (Engineering)'][idx]
        temp_arr = data[self.strain_type].diff()
        idx = temp_arr.index[temp_arr >= 2 * temp_arr.mean()]
        self.ultimate_stress_value = data['Stress (Engineering)'][idx[0]]
        '''
        start = time.time()
        def shift(a):
            a_r = np.roll(a, 1)  # right shift
            a_l = np.roll(a, -1)  # left shift
            return np.stack([a_l, a_r], axis=1)

        z = np.array(data[self.strain_type])
        diff = abs(shift(z) - z.reshape(-1, 1))
        diff = diff[1:-1]
        indices = diff.argmax(axis=0) - 2
        self.ultimate_stress_value = data[self.stress_type][indices[0]]
        end = time.time()
        print('Stress at failure time: ' + str(end-start))
        return data

    def ultimate_strain(self, data: {}):
        """
        function essentially checks size of differences between each strain data point, and finds the index of the
        first difference that meets criteria for a large enough difference to result in failure of the material
        :param data: csv data file user selects from desktop
        :return: ultimate strain value (fractional)
        """
        '''
        idx = data[self.strain_type].diff().idxmax() - 1
        self.ultimate_strain_value = data[self.strain_type][idx]
        temp_arr = data[self.strain_type].diff()
        idx = temp_arr.index[temp_arr >= 2 * temp_arr.mean()]
        self.ultimate_strain_value = data[self.strain_type][idx[0]]
        differences = data[self.strain_type].diff(-1).abs()
        kmeans = KMeans(n_clusters=5).fit(differences.values[:-1].reshape(-1, 1))
        clusters = pd.Series(kmeans.labels_, index=differences.index[:-1])
        idx = clusters.index[clusters.eq(np.squeeze(kmeans.cluster_centers_).argmax())]
        '''
        start = time.time()
        def shift(a):
            a_r = np.roll(a, 1)  # right shift
            a_l = np.roll(a, -1)  # left shift
            return np.stack([a_l, a_r], axis=1)

        z = np.array(data[self.strain_type])
        diff = abs(shift(z) - z.reshape(-1, 1))
        diff = diff[1:-1]
        indices = diff.argmax(axis=0) - 2
        self.ultimate_strain_value = data[self.strain_type][indices[0]]
        end = time.time()
        print('Strain at failure time: ' + str(end-start))
        return data

    def yms(self, data: {}):
        """
        function calculates Young's (elastic) modulus using the slope method given the engineering stress and engineering
        strain calculated and user-input of strain range start and end
            general calculation: instantaneous elastic modulus = instantaneous stress / instantaneous strain
                                 do above calculation for each strain value in the user-input range
                                 average all values along range to obtain value
        :param data: csv data file user selects from desktop
        :return: Young's modulus value (slope method)
        """
        '''
        s1 = data[self.strain_type][data[self.strain_type]==self.strain_start].index
        s2 = data[self.strain_type][data[self.strain_type]==self.strain_end].index
        '''
        start = time.time()
        s1i = min(data[self.strain_type], key=lambda x:abs(x-self.strain_start))
        s2i = min(data[self.strain_type], key=lambda x:abs(x-self.strain_end))
        s1 = data[self.strain_type][data[self.strain_type] == s1i].index
        s2 = data[self.strain_type][data[self.strain_type] == s2i].index
        self.youngs_modulus_value_slope = (data[self.stress_type][s2[0]] - data[self.stress_type][s1[0]]) / (data[self.strain_type][s2[0]] - data[self.strain_type][s1[0]])
        '''
        data.loc[
            (data[self.strain_type]).between(self.strain_start, self.strain_end,
                                                  inclusive=True), "Young's Modulus (Slope)"] = \
            data[self.stress_type] / data[self.strain_type]
        temp = data[data["Young's Modulus (Slope)"].notna()]
        self.youngs_modulus_value_slope = temp["Young's Modulus (Slope)"].mean()
        try:
            data["Young's Modulus (Slope)"] = data["Young's Modulus (Slope)"].astype('float64')
        except ValueError:
            data["Young's Modulus (Slope)"] = None
        '''
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = self.stress_pascal_unit
        end = time.time()
        print('Elastic modulus (slope) time: ' + str(end-start))
        return data

    def ymcsm(self, data: {}):
        """
        function calculates Young's (elastic modulus) using the CSM method given the CSM column, selection of area or
        volume conservation, and CSM start and stop range
            general calculation:
                volume conservation: instantaneous E = CSM * (current height ^ 2) / (initial area * initial height)
                area conservation: instantaneous E = CSM * (current height) / (initial area)
                                     multiply by 1000000000 for units before unit manipulation
                                     average all values along CSM range to obtain value
        :param data: csv data file user selects from desktop
        :return: Young's modulus value (CSM method)
        """
        start = time.time()
        if self.volume_conservation is True:
            data.loc[(data[self.csm_column]).between(self.csm_start, self.csm_end, inclusive=True), "Young's Modulus (CSM)"] = data[
                                                                                                                    self.csm_column] * (
                                                                                                                            (
                                                                                                                                        self.specimen_height +
                                                                                                                                        data[
                                                                                                                                            self.displacement_column]) ** 2) / (
                                                                                                                            self.specimen_area * self.specimen_height) * 1000000000
        elif self.area_conservation is True:
            data.loc[(data[self.csm_column]).between(self.csm_start, self.csm_end, inclusive=True), "Young's Modulus (CSM)"] = data[
                                                                                                                    self.csm_column] * (
                                                                                                                            self.specimen_height +
                                                                                                                            data[
                                                                                                                                self.displacement_column]) / self.specimen_area * 1000000000

        first_temp = data[data["Young's Modulus (CSM)"].notna()]
        c = first_temp["Young's Modulus (CSM)"].mean()
        if math.isnan(c) is True:
            c = 0.0

        if c > 0.0:
            log_value_csm = int(math.log10(c))
        elif c == 0.0:
            log_value_csm = 0.0
        else:
            log_value_csm = int(math.log10(-c)) + 1

        if 0 <= log_value_csm <= 1:
            self.csm_pascal_unit = 'Pa'
        elif 2 <= log_value_csm <= 4:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"] / 1000
            self.csm_pascal_unit = 'kPa'
        elif 5 <= log_value_csm <= 7:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"] / 1000000
            self.csm_pascal_unit = 'MPa'
        elif 8 <= log_value_csm <= 10:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"] / 1000000000
            self.csm_pascal_unit = 'GPa'
        elif 11 <= log_value_csm <= 13:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"] / 1000000000000
            self.csm_pascal_unit = 'TPa'
        else:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"] / 1000000000000000
            self.csm_pascal_unit = 'PPa'

        last_temp = data[data["Young's Modulus (CSM)"].notna()]
        self.youngs_modulus_value_csm = last_temp["Young's Modulus (CSM)"].mean()
        try:
            data["Young's Modulus (CSM)"] = data["Young's Modulus (CSM)"].astype('float64')
        except ValueError:
            data["Young's Modulus (CSM"] = None
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = self.csm_pascal_unit
        end = time.time()
        print('Elastic modulus (CSM) time: ' + str(end-start))
        return data

    def sneddon(self, data: {}):
        """
        function calculates the Sneddon correction to the Young's modulus CSM calculation given the CSM calculation,
        Poisson ratio, and material's known elastic modulus
            general calculation:
                volume conservation: [(1 / k) - C_sneddon] ^ -1
                                     C_sneddon = (sqrt(pi) * (1 - (v ^ 2))) / (2 * E * sqrt(instantaneous area))
                                     calculate Young's modulus w/ new CSM values
                area conservation: [(1 / k) - C_sneddon] ^ -1
                                    C_sneddon = (sqrt(pi) * (1 - (v ^ 2))) / (2 * E * sqrt(initial area))
                                    calculate Young's modulus w/ new CSM values
        :param data: csv data file user selects from desktop
        :return: Young's modulus w/ Sneddon's correction
        """
        start = time.time()
        if self.volume_conservation is True:
            partial_compliance_sneddon = (math.sqrt(math.pi) * (1 - (self.poisson_ratio ** 2))) / (2 * self.known_elastic_modulus)
            data["Sneddon's correction to CSM (volume conservation)"] = np.reciprocal(
                np.reciprocal(data[self.csm_column]) - (partial_compliance_sneddon / np.sqrt(
                    (self.specimen_area * self.specimen_height) / (self.specimen_height + data[self.displacement_column]))))
            self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = 'N/m'
            data.loc[(data[self.csm_column]).between(self.csm_start, self.csm_end,
                                                inclusive=True), "Young's Modulus (CSM w/ Sneddon's correction)"] = \
            data["Sneddon's correction to CSM (volume conservation)"] * (
                        (self.specimen_height + data[self.displacement_column]) ** 2) / (
                        self.specimen_area * self.specimen_height) * 1000000000
        elif self.area_conservation is True:
            area = self.specimen_area
            compliance_sneddon = (math.sqrt(math.pi) * (1 - (self.poisson_ratio ** 2))) / (
                        2 * self.known_elastic_modulus * math.sqrt(area))
            data["Sneddon's correction to CSM (area conservation)"] = np.reciprocal(
                np.reciprocal(data[self.csm_column]) - compliance_sneddon)
            self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = 'N/m'
            data.loc[(data[self.csm_column]).between(self.csm_start, self.csm_end,
                                                inclusive=True), "Young's Modulus (CSM w/ Sneddon's correction)"] = \
            data["Sneddon's correction to CSM (area conservation)"] * (
                        self.specimen_height + data[self.displacement_column]) / self.specimen_area * 1000000000

        first_sneddon_temp = data[data["Young's Modulus (CSM w/ Sneddon's correction)"].notna()]
        c2 = first_sneddon_temp["Young's Modulus (CSM w/ Sneddon's correction)"].mean()

        if math.isnan(c2) is True:
            c2 = 0.0

        if c2 > 0.0:
            log_value_sneddon = int(math.log10(c2))
        elif c2 == 0.0:
            log_value_sneddon = 0.0
        else:
            log_value_sneddon = int(math.log10(-c2)) + 1

        if 0 <= log_value_sneddon <= 1:
            self.sneddon_pascal_unit = 'Pa'
        elif 2 <= log_value_sneddon <= 4:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                                                                        "Young's Modulus (CSM w/ Sneddon's correction)"] / 1000
            self.sneddon_pascal_unit = 'kPa'
        elif 5 <= log_value_sneddon <= 7:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                                                                        "Young's Modulus (CSM w/ Sneddon's correction)"] / 1000000
            self.sneddon_pascal_unit = 'MPa'
        elif 8 <= log_value_sneddon <= 10:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                                                                        "Young's Modulus (CSM w/ Sneddon's correction)"] / 1000000000
            self.sneddon_pascal_unit = 'GPa'
        elif 11 <= log_value_sneddon <= 13:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                                                                        "Young's Modulus (CSM w/ Sneddon's correction)"] / 1000000000000
            self.sneddon_pascal_unit = 'TPa'
        else:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                                                                        "Young's Modulus (CSM w/ Sneddon's correction)"] / 1000000000000000
            self.sneddon_pascal_unit = 'PPa'

        last_sneddon_temp = data[data["Young's Modulus (CSM w/ Sneddon's correction)"].notna()]
        self.youngs_modulus_value_sneddon = last_sneddon_temp["Young's Modulus (CSM w/ Sneddon's correction)"].mean()
        try:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = data[
                "Young's Modulus (CSM w/ Sneddon's correction)"].astype('float64')
        except ValueError:
            data["Young's Modulus (CSM w/ Sneddon's correction)"] = None
        self.units_list[data.columns[len(data.columns) - 1].format(len(data.columns) - 1)] = self.sneddon_pascal_unit
        end = time.time()
        print('Sneddon correction time: ' + str(end-start))
        return data

    def energy_dissipated(self, data: {}):
        """
        function calculates the energy dissipated in a material by using np.trapz() which is a trapezoidal
        approximation for the area under a curve (stress-strain curve)
        :param data: csv data file user selects from desktop
        :return: work energy with the same units as stress
        """
        start = time.time()
        wrk = np.trapz(data[self.stress_type], data[self.strain_type])
        self.energy_dissipated_value = wrk
        end = time.time()
        print('Energy dissipated time: ' + str(end-start))
        return data

    def bursts(self, data: {}):
        """
        function calculates strain differences between each stress-strain point, then sorts the differences and uses
        logarithmic manipulation to find a factor for each unique data set that the differences are compared to; the
        differences greater than the factor times the mean difference represent bursts or material failure
        :param data: csv data file user selects from desktop
        :return: # of bursts & arrays containing information of bursts (index of stress-strain occuring at bursts)
        """
        start = time.time()
        all_diff = data[self.strain_type].diff()
        if all_diff.mean() >= 0.0:
            log_value = math.log10(all_diff.mean())
        else:
            log_value = math.log10(-all_diff.mean()) + 1
        factor = abs(log_value) - 3
        mean_changer = 2 * (10 ** factor)
        large_diff_upper = all_diff.index[
            all_diff >= (mean_changer * all_diff.mean())]  # maybe just make len/100 the value 250
        large_diff_lower = large_diff_upper - 1
        if self.toggle_bursts is True:
            for i in range(0, len(large_diff_lower), 2):
                self.large_diff[i] = large_diff_lower[int(i / 2)]
                self.large_diff[i + 1] = large_diff_upper[int(i / 2)]
            for j in range(0, len(self.large_diff) * 2, 2):
                self.burst_stress_strain[j] = data[self.stress_type][self.large_diff[int(j / 2)]]
                self.burst_stress_strain[j + 1] = data[self.strain_type][self.large_diff[int(j / 2)]]
            for k in range(0, len(self.large_diff), 2):
                self.burst_size[int(k/2)] = data[self.strain_type][self.large_diff[k + 1]] - data[self.strain_type][self.large_diff[k]]
        else:
            for x in range(0, len(large_diff_lower)):
                self.large_diff.append(large_diff_lower[x])
                self.large_diff.append(large_diff_upper[x])
            for w in range(0, len(self.large_diff)):
                self.burst_stress_strain.append(data[self.stress_type][self.large_diff[w]])
                self.burst_stress_strain.append(data[self.strain_type][self.large_diff[w]])
            for z in range(0, len(self.large_diff), 2):
                self.burst_size.append(data[self.strain_type][self.large_diff[z + 1]] - data[self.strain_type][self.large_diff[z]])
            self.toggle_bursts = True
        self.num_bursts_value = len(self.large_diff) / 2
        end = time.time()
        print('Bursts time: ' + str(end - start))
        return data

    def check(self, data: {}):
        """
        function checks if a calculation is completed and updates the data frame accordingly
        :param data: csv data file user selects from desktop
        :return: updated calculation data
        """
        if self.compute_stress is True:
            data = self.engineering_stress(data)
        if self.compute_strain is True:
            data = self.engineering_strain(data)
        if self.compute_yms is True:
            data = self.yms(data)
        if self.compute_ymcsm is True:
            data = self.ymcsm(data)
        if self.compute_true_stress is True:
            data = self.true_stress(data)
        if self.compute_true_strain is True:
            data = self.true_strain(data)
        if self.compute_sneddon is True:
            data = self.sneddon(data)
        if self.compute_uss is True:
            data = self.ultimate_stress(data)
            data = self.ultimate_strain(data)
        if self.compute_energy_dissipated is True:
            data = self.energy_dissipated(data)
        if self.compute_bursts is True:
            data = self.bursts(data)
        return data

    def can_compute_stress(self):
        """
        function checks if software can compute engineering stress; requires load column & initial area
        :return: compute stress availability or idle
        """
        if self.l is True and self.s is True:
            self.compute_stress = True
        else:
            self.idle()

    def can_compute_strain(self):
        """
        function checks if software can compute engineering strain; requires displacement column & initial height
        :return: compute strain availability or idle
        """
        if self.d is True and self.h is True:
            self.compute_strain = True
        else:
            self.idle()

    def can_compute_yms(self):
        """
        function checks if software can compute Young's modulus (slope method); requires engineering stress & strain
        :return: compute Young's modulus (slope method) availability or pop-up w/ potential missing parameters
        """
        if self.compute_stress is True and self.compute_strain is True:
            if self.ss is True and self.se is True:
                if self.type_exists is True:
                    self.compute_yms = True
                else:
                    self.create_pop_up(
                        "Cannot compute Young's modulus (slope method) due to one of the following missing parameters: computed stress, computed strain, strain range, stress-strain type.")
            else:
                self.create_pop_up(
                    "Cannot compute Young's modulus (slope method) due to one of the following missing parameters: computed stress, computed strain, strain range, stress-strain type.")
        else:
            self.create_pop_up(
                "Cannot compute Young's modulus (slope method) due to one of the following missing parameters: computed stress, computed strain, strain range, stress-strain type.")

    def can_compute_ymcsm(self):
        """
        function checks if software can compute Young's modulus (CSM method); requires CSM column, engineering stress &
        strain, area or volume conservation selection
        :return: compute Young's modulus (CSM method) availability or pop-up w/ potential missing parameters
        """
        if self.csm_s is True and self.csm_e is True:
            if self.csm is True:
                if self.compute_stress is True and self.compute_strain is True:
                    if self.area_conservation is True or self.volume_conservation is True:
                        self.compute_ymcsm = True
                    else:
                        self.create_pop_up(
                            "Cannot compute Young's Modulus (CSM method) due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection, CSM start & stop, CSM column, conservation checkbox.")
                else:
                    self.create_pop_up(
                        "Cannot compute Young's Modulus (CSM method) due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection, CSM start & stop, CSM column, conservation checkbox.")
            else:
                self.create_pop_up(
                    "Cannot compute Young's Modulus (CSM method) due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection, CSM start & stop, CSM column, conservation checkbox.")
        else:
            self.create_pop_up(
                "Cannot compute Young's Modulus (CSM method) due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection, CSM start & stop, CSM column, conservation checkbox.")

    def can_compute_sneddon(self):
        """
        function checks if softwre can compute Sneddon's correction to the Young's modulus value (CSM method); requires
        CSM calculation, Poisson ratio, material's known elastic modulus
        :return: compute Sneddon's correction to Young's modulus availability or pop-up w/ potential missing parameters
        """
        if self.compute_ymcsm is True:
            if self.known_elastic_modulus_exists is True and self.poisson_exists is True:
                self.compute_sneddon = True
            else:
                self.create_pop_up(
                    "Cannot compute Sneddon's correction to the Young's Modulus (CSM method) due to one of the following missing parameters: Young's Modulus (CSM method) has not been calculated, Poisson ratio, or material's known elastic modulus (of pillar).")
        else:
            self.create_pop_up(
                "Cannot compute Sneddon's correction to the Young's Modulus (CSM method) due to one of the following missing parameters: Young's Modulus (CSM method) has not been calculated, Poisson ratio, or material's known elastic modulus (of pillar).")

    def can_compute_true_stress(self):
        """
        function checks if software can compute true stress; requires engineering stress & strain
        :return: compute true stress availability or pop-up w/ potential missing parameters
        """
        if self.compute_strain is True and self.compute_stress is True:
            self.compute_true_stress = True
        else:
            self.create_pop_up(
                'Cannot compute true stress or true strain due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection. Try calculating engineering stress or strain first.')

    def can_compute_true_strain(self):
        """
        function checks if software can compute true strain; requires engineering strain
        :return: compute true strain availability or pop-up w/ potential missing parameters
        """
        if self.compute_strain is True:
            self.compute_true_strain = True
        else:
            self.create_pop_up(
                'Cannot compute true stress or true strain due to one of the following missing parameters: specimen height, specimen area, displacement column selection, load column selection. Try calculating engineering stress or strain first.')

    def can_compute_uss(self):
        """
        function checks if software can compute the ultimate stress-strain of a material at failure; requires
        stress-strain (either true or engineering)
        :return: compute ultimate stress-strain availability or pop-up w/ potential missing parameters
        """
        if self.compute_stress is True and self.compute_strain is True:
            if self.type_exists is True:
                self.compute_uss = True
            else:
                self.create_pop_up(
                    'Cannot compute ultimate failure stress and strain due to one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')
        else:
            self.create_pop_up('Cannot compute ultimate failure stress and strain due to one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')

    def can_compute_energy_dissipated(self):
        """
        function checks if software can compute the energy dissipated of a material; requires stress-strain (either
        true or engineering)
        :return: compute energy dissipated availability or pop-up w/ potential missing parameters
        """
        if self.compute_stress is True and self.compute_strain is True:
            if self.type_exists is True:
                self.compute_energy_dissipated = True
            else:
                self.create_pop_up(
                    'Cannot compute energy dissipated because a stress-strain curve cannot be generated due one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')
        else:
            self.create_pop_up('Cannot compute energy dissipated because a stress-strain curve cannot be generated due one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')

    def can_compute_bursts(self):
        """
        function checks if software can compute the burst events occurring in a material; requires stress-strain (either
        true or engineering)
        :return: compute burst events availability or pop-up w/ potential missing parameters
        """
        if self.compute_stress is True and self.compute_strain is True:
            if self.type_exists is True:
                self.compute_bursts = True
            else:
                self.create_pop_up(
                    'Cannot compute bursts because a stress-strain curve cannot be generated due one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')
        else:
            self.create_pop_up('Cannot compute bursts because a stress-strain curve cannot be generated due one of the following missing parameters: stress calculation, strain calculation, stress-strain type.')

    def create_pop_up(self, arg):
        """
        function creates a pop-up 'Help' window that indicates missing parameters or problems
        :param arg: message displayed in the pop-up window
        :return: pop-up 'Help' window
        """
        pop_up = tk.Toplevel()
        pop_up.title('Help')
        msg = tk.Message(pop_up, text=arg)
        msg.grid(row=0)
        remove_button = tk.Button(pop_up, text="Dismiss", command=pop_up.destroy)
        remove_button.grid(row=1)

    def refresh_abscissa_options(self):
        """
        function refreshes the 'Select Abscissa' options to include all up-to-date calculations
        :return: options menu 'Select Abscissa' updated
        """
        self.clicked_abscissa_button.set('Select Abscissa')
        self.drop1['menu'].delete(0, 'end')
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.check(data_frames[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)
        for i in column_names[:]:
            self.drop1['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_abscissa_button, i,
                                                             self.select_abscissa_data))

    def refresh_ordinate_options(self):
        """
        function refreshes the 'Select ORdinate' options to include all up-to-date claculations
        :return: options menu 'Select Ordinate' updated
        """
        self.clicked_ordinate_button.set('Select Ordinate')
        self.drop2['menu'].delete(0, 'end')
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.check(data_frames[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)
        for i in column_names[:]:
            self.drop2['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_ordinate_button, i,
                                                             self.select_ordinate_data))

    def refresh(self):
        """
        function refreshes the software to update 'Select Abscissa', 'Select Ordinate', or display Young's modulus
        slope, CSM, and Sneddon correction methods
        :return: updated software GUI
        """
        self.refresh_abscissa_options()
        self.refresh_ordinate_options()
        if self.compute_yms is True:
            self.display_yms_value()
        if self.compute_ymcsm is True:
            self.display_ymcsm_value()
        if self.compute_sneddon is True:
            self.display_ymsneddon_value()
        if self.compute_energy_dissipated is True:
            self.display_energy_dissipated_value()
        if self.compute_bursts is True:
            self.display_num_bursts_value()
            self.sbf.destroy()
            self.burst_information()
        if self.compute_uss is True:
            self.display_uss_value()
        if self.xmin_exists is True and self.xmax_exists is True and self.ymin_exists is True and self.ymax_exists is True:
            self.plot()
        elif self.xmin_exists is True and self.xmax_exists is True:
            self.plot()
        elif self.ymin_exists is True and self.ymax_exists is True:
            self.plot()

    def save_svg(self):
        """
        function saves the current graph in .svg format
        :return: SVG file
        """
        # TODO: additional export capabilities than just SVG for graphs
        '''
        self.fig.savefig(
            '/Users/colinkang/Desktop/' + self.ordinate + ' (' + self.units_list[self.ordinate] + ') vs. ' + self.abscissa + ' (' +
            self.units_list[self.abscissa] + ')', format='svg')
        '''
        if self.can_export is True:
            my_path = os.path.abspath(__file__)
            base = os.path.basename(__file__)
            new_path = my_path.replace(base, '')
            my_file = self.ordinate + ' (' + self.units_list[self.ordinate] + ') vs. ' + self.abscissa + ' (' + self.units_list[self.abscissa] + ')'
            self.fig.savefig(os.path.join(new_path, my_file), format='svg')
        else:
            self.create_pop_up('First plot.')

    def select_abscissa_data(self, arg):
        """
        function updates the global abscissa parameter to the selected abscissa column
        :param arg: N/A
        :return: updated global abscissa & both_selected()
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.check(data_frames[self.csv_index])
        for col_name in data_frames[self.csv_index].columns:
            if col_name == self.clicked_abscissa_button.get():
                self.abscissa = col_name
                self.a = True
        if self.abscissa != '':
            self.both_selected()

    def select_ordinate_data(self, arg):
        """
        function updates the global ordinate parameter to the selected ordinate column
        :param arg: N/A
        :return: updated global ordinate & both_selected()
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.check(data_frames[self.csv_index])
        for col_name in data_frames[self.csv_index].columns:
            if col_name == self.clicked_ordinate_button.get():
                self.ordinate = col_name
                self.o = True
        if self.ordinate != '':
            self.both_selected()

    def select_load_column(self, arg):
        """
        function updates the global load_column parameter to selected load column
        :param arg: N/A
        :return: updated global load_column & can_compute_stress()
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        for col_name in data_frames[self.csv_index].columns:
            if col_name == self.clicked_load_button.get():
                self.load_column = col_name
                self.l = True
        if self.load_column != '':
            self.can_compute_stress()

    def select_displacement_column(self, arg):
        """
        function updates the global displacement_column parameter to selected displacement column
        :param arg: N/A
        :return: updated global displacement_column & can_compute_strain()
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        for col_name in data_frames[self.csv_index].columns:
            if col_name == self.clicked_displacement_button.get():
                self.displacement_column = col_name
                self.d = True
        if self.displacement_column != '':
            self.can_compute_strain()

    def select_csm_column(self, arg):
        """
        function updates the global csm_column parameter to selected CSM column
        :param arg: N/A
        :return: udpated global csm_column
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        for col_name in data_frames[self.csv_index].columns:
            if col_name == self.clicked_csm_button.get():
                self.csm_column = col_name
                self.csm = True
        if self.csm_column != '':
            return

    def plot(self):
        """
        function takes the selected abscissa and ordinate column, re-zero displaces it, and then plots the data
        accordingly including units
        :return: plot: ordinate vs abscissa
        """
        self.can_export = True
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        data_frames[self.csv_index] = self.reindex(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.re_zero(data_frames[self.csv_index])
        data_frames[self.csv_index] = self.check(data_frames[self.csv_index])

        self.fig = Figure(figsize=(12, 10), dpi=100) # -temp- 10, 10
        self.fig.add_subplot(1, 1, 1, xlabel=self.abscissa + ' (' + self.units_list[self.abscissa] + ')',
                             ylabel=self.ordinate + ' (' + self.units_list[self.ordinate] + ')').scatter(data_frames[self.csv_index][self.abscissa], data_frames[self.csv_index][self.ordinate],
                                                                                          s=7, color='#8b008b') # -temp- s=0.5
        ax = self.fig.gca()
        ax.xaxis.label.set_size(12.5)
        ax.yaxis.label.set_size(12.5)
        ax.tick_params(axis=tk.X, labelsize=12.5)
        ax.tick_params(axis=tk.Y, labelsize=12.5)

        if self.xmin_exists is True and self.xmax_exists is True and self.ymin_exists is True and self.ymax_exists is True:
            ax.set(xlim=(self.xmin_value, self.xmax_value), ylim=(self.ymin_value, self.ymax_value))
        elif self.xmin_exists is True and self.xmax_exists is True:
            ax.set(xlim=(self.xmin_value, self.xmax_value))
        elif self.ymin_exists is True and self.ymax_exists is True:
            ax.set(ylim=(self.ymin_value, self.ymax_value))
        else:
            xbound = data_frames[self.csv_index][self.abscissa].min()
            ybound = data_frames[self.csv_index][self.ordinate].min()
            ax.set(xlim=(xbound, None), ylim=(ybound, None))

        canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, rowspan=44, column=13, columnspan=15, sticky=tk.E)

    def select_abscissa_button(self):
        """
        function creates initial 'Select Abscissa' options from original data set (pre-calculations)
        :return: options menu of raw data selectable data
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)

        self.clicked_abscissa_button = tk.StringVar(self.parent)
        self.clicked_abscissa_button.set("Select Abscissa")

        self.drop1 = tk.OptionMenu(self.parent, self.clicked_abscissa_button, 'Select Abscissa', command=self.idle)
        for i in column_names[:]:
            self.drop1['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_abscissa_button, i,
                                                             self.select_abscissa_data))

        self.drop1.grid(row=0, column=0, columnspan=2)

    def select_ordinate_button(self):
        """
        function creates initial 'Select Ordinate' options from original data set (pre-calculations)
        :return: options menu of raw data selectable data
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)

        self.clicked_ordinate_button = tk.StringVar(self.parent)
        self.clicked_ordinate_button.set("Select Ordinate")

        self.drop2 = tk.OptionMenu(self.parent, self.clicked_ordinate_button, 'Select Ordinate', command=self.idle)
        for i in column_names[:]:
            self.drop2['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_ordinate_button, i,
                                                             self.select_ordinate_data))

        self.drop2.grid(row=0, column=3, columnspan=2)

    def create_header(self, title, r, c, cs):
        """
        function creates headers for the GUI organizing calculation parameters & outputs
        :param title: header's title
        :param r: row
        :param c: column
        :param cs: columnspan
        :return: customized header
        """
        header = tk.Label(self.parent, text=title, font='Helvetica 18 bold')
        header.grid(row=r, column=c, columnspan=cs)

    def create_button(self, title, call, r, c, cs):
        """
        function creates buttons w/ commands for the GUI
        :param title: button's title
        :param call: function called upon mouse-click
        :param r: row
        :param c: column
        :param cs: columnspan
        :return: customized button
        """
        button = tk.Button(self.parent, text=title, command=call)
        button.grid(row=r, column=c, columnspan=cs)

    def input_poisson_ratio(self):
        """
        function that displays a label w/ corresponding entry key for user to input Poisson ratio constant
        :return: Poisson ratio boolean & value
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(uip):
            self.poisson_ratio = float(uip.get())
            self.poisson_exists = True

        uip = tk.DoubleVar()
        self.user_input_label_poisson = tk.Label(self.parent, text="Enter material's Poisson ratio:")
        self.user_input_label_poisson.grid(row=20, column=1, columnspan=3, sticky=tk.E)
        self.user_input_poisson = tk.Entry(self.parent, textvariable=uip)
        self.user_input_poisson.bind('<Return>', (lambda _: callback(self.user_input_poisson)))
        self.user_input_poisson.grid(row=20, column=4, columnspan=3, sticky=tk.W)

    def input_known_elastic_modulus(self):
        """
        function that displays a label w/ corresponding entry key for user to input material's known elastic
        modulus constant
        :return: material's known elastic modulus boolean & value
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(uikem):
            self.known_elastic_modulus = float(uikem.get())
            self.known_elastic_modulus_exists = True

        uikem = tk.DoubleVar()
        self.user_input_label_known_elastic_modulus = tk.Label(self.parent,
                                                               text="Enter material's known elastic modulus (GPa):")
        self.user_input_label_known_elastic_modulus.grid(row=21, columnspan=5, sticky=tk.E)
        self.user_input_known_elastic_modulus = tk.Entry(self.parent, textvariable=uikem)
        self.user_input_known_elastic_modulus.bind('<Return>',
                                                   (lambda _: callback(self.user_input_known_elastic_modulus)))
        self.user_input_known_elastic_modulus.grid(row=21, column=5, columnspan=3, sticky=tk.W)

    def input_specimen_area(self):
        """
        function that displays a label w/ corresponding entry key for user to input specimen's initial area in nm^2
        :return: specimen initial area boolean & value
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(ui):
            self.specimen_area = float(ui.get())
            self.s = True

        ui = tk.DoubleVar()
        self.user_input_label_area = tk.Label(self.parent, text="Enter specimen area ((nm)^2):")
        self.user_input_label_area.grid(row=2, column=1, columnspan=3, sticky=tk.E)
        self.user_input_area = tk.Entry(self.parent, textvariable=ui)
        self.user_input_area.bind('<Return>', (lambda _: callback(self.user_input_area)))
        self.user_input_area.grid(row=2, column=4, columnspan=3, sticky=tk.W)

    def input_specimen_height(self):
        """
        function that displays a label w/ corresponding entry key for user to input specimen's initial height in nm
        :return: specimen initial height boolean & value
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(uih):
            self.specimen_height = float(uih.get())
            self.h = True

        uih = tk.DoubleVar()
        self.user_input_label_height = tk.Label(self.parent, text="Enter specimen height (nm):")
        self.user_input_label_height.grid(row=5, column=1, columnspan=3, sticky=tk.E)
        self.user_input_height = tk.Entry(self.parent, textvariable=uih)
        self.user_input_height.bind('<Return>', (lambda _: callback(self.user_input_height)))
        self.user_input_height.grid(row=5, column=4, columnspan=3, sticky=tk.W)

    def input_strain_range(self):
        """
        function that displays a label w/ corresponding entry key for user to input strain range (frac. start & end)
        :return: strain range boolean & values
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(uisrs):
            self.strain_start = float(uisrs.get())
            self.ss = True

        uisrs = tk.DoubleVar()
        self.user_input_label_strain_s = tk.Label(self.parent, text="Enter strain start:")
        self.user_input_label_strain_s.grid(row=8, column=1, columnspan=2, sticky=tk.E)
        self.user_input_strain_s = tk.Entry(self.parent, textvariable=uisrs)
        self.user_input_strain_s.bind('<Return>', (lambda _: callback(self.user_input_strain_s)))
        self.user_input_strain_s.grid(row=8, column=3, columnspan=3, sticky=tk.W)

        def callback2(uisre):
            self.strain_end = float(uisre.get())
            self.se = True

        uisre = tk.DoubleVar()
        self.user_input_label_strain_e = tk.Label(self.parent, text="Enter strain end:")
        self.user_input_label_strain_e.grid(row=9, column=1, columnspan=2, sticky=tk.E)
        self.user_input_strain_e = tk.Entry(self.parent, textvariable=uisre)
        self.user_input_strain_e.bind('<Return>', (lambda _: callback2(self.user_input_strain_e)))
        self.user_input_strain_e.grid(row=9, column=3, columnspan=3, sticky=tk.W)

    def input_csm_range(self):
        """
        function that displays a label w/ corresponding entry key for user to input csm range (N/m start & N/m end)
        :return: csm range boolean & values
        """
        # TODO: make it so inputs do not need to be invoked by <Return> key

        def callback(uicsm_s):
            self.csm_start = float(uicsm_s.get())
            self.csm_s = True
            # self.can_compute_ymcsm()

        uicsm_s = tk.DoubleVar()
        self.user_input_label_csm_s = tk.Label(self.parent, text="Enter CSM start (N/m):")
        self.user_input_label_csm_s.grid(row=13, column=0, columnspan=3, sticky=tk.E)
        self.user_input_csm_s = tk.Entry(self.parent, textvariable=uicsm_s)
        self.user_input_csm_s.bind('<Return>', (lambda _: callback(self.user_input_csm_s)))
        self.user_input_csm_s.grid(row=13, column=3, columnspan=3, sticky=tk.W)

        def callback2(uicsm_e):
            self.csm_end = float(uicsm_e.get())
            self.csm_e = True
            # self.can_compute_ymcsm()

        uicsm_e = tk.DoubleVar()
        self.user_input_label_csm_e = tk.Label(self.parent, text="Enter CSM end (N/m):")
        self.user_input_label_csm_e.grid(row=14, column=0, columnspan=3, sticky=tk.E)
        self.user_input_csm_e = tk.Entry(self.parent, textvariable=uicsm_e)
        self.user_input_csm_e.bind('<Return>', (lambda _: callback2(self.user_input_csm_e)))
        self.user_input_csm_e.grid(row=14, column=3, columnspan=3, sticky=tk.W)

    def input_domain(self):
        """
        function has user input a specific domain that is stored into the bounds for plotting
        :return: x-axis bounds for the data being plotted
        """
        self.user_input_label_domain = tk.Label(self.parent, text="Enter domain:")
        self.user_input_label_domain.grid(row=45, column=13, columnspan=2, sticky=tk.E)

        def callback(xmin):
            self.xmin_value = float(xmin.get())
            self.xmin_exists = True

        xmin = tk.DoubleVar()
        self.user_input_xmin = tk.Entry(self.parent, textvariable=xmin)
        self.user_input_xmin.bind('<Return>', (lambda _: callback(self.user_input_xmin)))
        self.user_input_xmin.grid(row=45, column=15, columnspan=3, sticky=tk.W)

        def callback2(xmax):
            self.xmax_value = float(xmax.get())
            self.xmax_exists = True

        xmax = tk.DoubleVar()
        self.user_input_xmax = tk.Entry(self.parent, textvariable=xmax)
        self.user_input_xmax.bind('<Return>',(lambda _: callback2(self.user_input_xmax)))
        self.user_input_xmax.grid(row=45, column=18, columnspan=3, sticky=tk.W)

    def input_range(self):
        """
        function has user input a specific range that is stored into the bounds for plotting
        :return: y-axis bounds for the data being plotted
        """
        self.user_input_label_range = tk.Label(self.parent, text="Enter range:")
        self.user_input_label_range.grid(row=46, column=13, columnspan=2, sticky=tk.E)

        def callback(ymin):
            self.ymin_value = float(ymin.get())
            self.ymin_exists = True

        ymin = tk.DoubleVar()
        self.user_input_ymin = tk.Entry(self.parent, textvariable=ymin)
        self.user_input_ymin.bind('<Return>', (lambda _: callback(self.user_input_ymin)))
        self.user_input_ymin.grid(row=46, column=15, columnspan=3, sticky=tk.W)

        def callback2(ymax):
            self.ymax_value = float(ymax.get())
            self.ymax_exists = True

        ymax = tk.DoubleVar()
        self.user_input_ymax = tk.Entry(self.parent, textvariable=ymax)
        self.user_input_ymax.bind('<Return>', (lambda _: callback2(self.user_input_ymax)))
        self.user_input_ymax.grid(row=46, column=18, columnspan=3, sticky=tk.W)

    def check_area_or_volume_conservation(self):
        """
        function allows user to select either volume conservation or area conservation for Young's modulus CSM method
        and Sneddon's correction; if both or none are selected, user is prompted to change checkmarks
        :return: either area or volume conservation toggled
        """

        def determine_conservation():
            if (area_select.get() == 1) & (volume_select.get() == 0):
                self.area_conservation = True
                self.volume_conservation = False
            elif (area_select.get() == 0) & (volume_select.get() == 1):
                self.volume_conservation = True
                self.area_conservation = False
            elif (area_select.get() == 1) & (volume_select.get() == 1):
                self.area_conservation = False
                self.volume_conservation = False
                self.create_pop_up(
                    'You have selected both area conservation and volume conservation. Please select only one.')
            else:
                self.area_conservation = False
                self.volume_conservation = False
                self.create_pop_up(
                    'You have selected neither area conservation nor volume conservation. Please select one.')

        area_select = tk.IntVar()
        volume_select = tk.IntVar()
        checkbox_area = tk.Checkbutton(self.parent, text='Area Conservation', variable=area_select, onvalue=1,
                                       offvalue=0, command=determine_conservation)
        checkbox_area.grid(row=16, column=1, columnspan=3)
        checkbox_volume = tk.Checkbutton(self.parent, text='Volume Conservation', variable=volume_select, onvalue=1,
                                         offvalue=0, command=determine_conservation)
        checkbox_volume.grid(row=16, column=4, columnspan=3)

    def check_engineering_or_true_stress_strain(self):
        """
        function allows user to select either engineering stress-strain or true stress-strain for latter calculations
        :return: engineering or truee stress-strain selection
        """
        def determine_type():
            if (engineering_select.get() == 1) & (true_select.get() == 0):
                if self.compute_stress is True and self.compute_strain is True:
                    self.stress_type = 'Stress (Engineering)'
                    self.strain_type = 'Strain (Engineering)'
                    self.type_exists = True
                else:
                    self.create_pop_up('First calculate engineering stress-strain.')
            elif (engineering_select.get() == 0) & (true_select.get() == 1):
                if self.compute_true_stress is True and self.compute_true_strain is True:
                    self.stress_type = 'Stress (True)'
                    self.strain_type = 'Strain (True)'
                    self.type_exists = True
                else:
                    self.create_pop_up('First calculate true stress-strain.')
            elif (engineering_select.get() == 1) & (true_select.get() == 1):
                self.create_pop_up('You have selected both engineering and true. Please select only one.')
                self.type_exists = False
            else:
                self.create_pop_up('You have selected neither engineering nor true. Please select one.')
                self.type_exists = False

        engineering_select = tk.IntVar()
        true_select = tk.IntVar()
        checkbox_engineering = tk.Checkbutton(self.parent, text='Engineering Stress-Strain', variable=engineering_select, onvalue=1, offvalue=0, command=determine_type)
        checkbox_engineering.grid(row=7, column=8, columnspan=4, sticky=tk.W)
        checkbox_true = tk.Checkbutton(self.parent, text='True Stress-Strain', variable=true_select, onvalue=1, offvalue=0, command=determine_type)
        checkbox_true.grid(row=8, column=8, columnspan=4, sticky=tk.W)

    def output_values(self, title, r, c, cs):
        """
        function creates labels corresponding to the three different Young's modulus calculations
        :param title: Young's modulus type title
        :param r: row
        :param c: column
        :param cs: columnspan
        :return: Young's modulus output label
        """
        output_label = tk.Label(self.parent, text=title)
        output_label.grid(row=r, column=c, columnspan=cs, sticky=tk.E)

    def display_yms_value(self):
        """
        function displays Young's modulus value (slope method) & destroys previous labels each time label is updated
        :return: display label for Young's modulus value (slope)
        """
        try:
            if self.display_yms:
                self.display_yms.destroy()
        except AttributeError:
            lambda *args: None
        self.display_yms = tk.Label(self.parent, text=str(self.youngs_modulus_value_slope) + " (" + self.stress_pascal_unit + ")")
        self.display_yms.grid(row=11, column=4, columnspan=2, sticky=tk.W)

    def display_ymcsm_value(self):
        """
        function displays Young's modulus value (CSM method) & destroys previous labels each time label is updated
        :return: display label for Young's modulus value (CSM)
        """
        try:
            if self.display_ymcsm:
                self.display_ymcsm.destroy()
        except AttributeError:
            lambda *args: None
        self.display_ymcsm = tk.Label(self.parent, text=str(self.youngs_modulus_value_csm) + " (" + self.csm_pascal_unit + ")")
        self.display_ymcsm.grid(row=18, column=4, columnspan=3, sticky=tk.W)

    def display_ymsneddon_value(self):
        """
        function displays Young's modulus value (Sneddon correction to CSM) & destroys previous labels each time label
        is updated
        :return: display label for Young's modulus value (Sneddon)
        """
        try:
            if self.display_ymsneddon:
                self.display_ymsneddon.destroy()
        except AttributeError:
            lambda *args: None
        self.display_ymsneddon = tk.Label(self.parent, text=str(self.youngs_modulus_value_sneddon) + " (" + self.sneddon_pascal_unit + ")")
        self.display_ymsneddon.grid(row=23, column=4, columnspan=3, sticky=tk.W)

    def display_uss_value(self):
        """
        function displays the stress-strain values of the material at failure & destroys previous labels each time
        label is updated
        :return: display label for Ultimate Stress-Strain at failure
        """
        try:
            if self.display_ustress:
                self.display_ustress.destroy()
        except AttributeError:
            lambda *args: None
        self.display_ustress = tk.Label(self.parent, text=str(self.ultimate_stress_value) + " (" + self.stress_pascal_unit + ")")
        self.display_ustress.grid(row=25, column=3, columnspan=3, sticky=tk.W)

        try:
            if self.display_ustrain:
                self.display_ustrain.destroy()
        except AttributeError:
            lambda *args: None
        self.display_ustrain = tk.Label(self.parent, text=str(self.ultimate_strain_value))
        self.display_ustrain.grid(row=26, column=3, columnspan=3, sticky=tk.W)

    def display_energy_dissipated_value(self):
        """
        function displays the energy dissipated value & destroys previous labels each time label is updated
        :return: display label for Energy Dissipated
        """
        try:
            if self.display_energy_dissipated:
                self.display_energy_dissipated.destroy()
        except AttributeError:
            lambda *args: None
        self.display_energy_dissipated = tk.Label(self.parent, text=str(self.energy_dissipated_value) + " (" + self.stress_pascal_unit + ")")
        self.display_energy_dissipated.grid(row=29, column=3, columnspan=3, sticky=tk.W)

    def display_num_bursts_value(self):
        """
        function displays the number of bursts occurring & destroys previous labels each time label is updated
        :return: display label for number of bursts
        """
        try:
            if self.display_num_bursts:
                self.display_num_bursts.destroy()
        except AttributeError:
            lambda *args: None
        self.display_num_bursts = tk.Label(self.parent, text=str(self.num_bursts_value))
        self.display_num_bursts.grid(row=33, column=3, columnspan=1, sticky=tk.W)

    def select_csm_button(self):
        """
        function creates the 'Select CSM Column' option menu for user to select corresponding column
        :return: updated option menu w/ CSM column selected
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)

        self.clicked_csm_button = tk.StringVar(self.parent)
        self.clicked_csm_button.set("Select CSM Column")

        self.drop5 = tk.OptionMenu(self.parent, self.clicked_csm_button, 'Select CSM Column', command=self.idle)
        for i in column_names[:]:
            self.drop5['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_csm_button, i,
                                                             self.select_csm_column))  # + ' (' + units_list[i] + ')'
        self.drop5.grid(row=15, column=4, columnspan=3, sticky=tk.W)

    def select_load_button(self):
        """
        function creates the 'Select Load Column' option menu for user to select corresponding column
        :return: updated option menu w/ load column selected
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)

        self.clicked_load_button = tk.StringVar(self.parent)
        self.clicked_load_button.set("Select Load Column")

        self.drop3 = tk.OptionMenu(self.parent, self.clicked_load_button, 'Select Load Column', command=self.idle)
        for i in column_names[:]:
            self.drop3['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_load_button, i,
                                                             self.select_load_column))  # + ' (' + units_list[i] + ')'
        self.drop3.grid(row=3, column=4, columnspan=3, sticky=tk.W)

    def select_displacement_button(self):
        """
        function creates the 'Select Displacement Column' option menu for user to select corresponding column
        :return: updated option menu w/ displacement column selected
        """
        if csv_list[self.csv_index] != 'parse':
            data_frames[self.csv_index] = pd.read_csv(csv_list[self.csv_index])
        column_names = []
        for col_name in data_frames[self.csv_index].columns:
            column_names.append(col_name)

        self.clicked_displacement_button = tk.StringVar(self.parent)
        self.clicked_displacement_button.set("Select Displacement Column")

        self.drop4 = tk.OptionMenu(self.parent, self.clicked_displacement_button, 'Select Displacement Column',
                                   command=self.idle)
        for i in column_names[:]:
            self.drop4['menu'].add_command(label=i + ' (' + self.units_list[i] + ')',
                                           command=tk._setit(self.clicked_displacement_button, i,
                                                             self.select_displacement_column))  # + ' (' + units_list[i] + ')'
        self.drop4.grid(row=6, column=4, columnspan=3, sticky=tk.W)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        frame = ScrollableFrame(self, 1175, 1350) # -temp- 975, 750
        frame.grid()
        self.csv_interface = CSVInterface(frame.scrollable_frame)
        self.csv_interface.grid()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('DVaC GUI')
    MainApplication(root).grid()
    root.mainloop()