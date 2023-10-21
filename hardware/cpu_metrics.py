from cpuinfo import get_cpu_info
import psutil
import time
import subprocess
import re
import os
import pandas as pd
import numpy as np
import warnings
import platform
from pkg_resources import resource_stream


CONSTANT_CONSUMPTION = 100.1
# FROM_WATTs_TO_kWATTh = 1000*3600
NUM_CALCULATION = 200
# CPU_TABLE_NAME = "../data/gpu.csv"


class NoCPUinTableWarning(Warning):
    pass


class NoNeededLibrary(Warning):
    pass

# This class is the interface for tracking CPU power consumption.


class CPU():
    def __init__(self, cpu_processes="current", ignore_warnings=False):
        self._ignore_warnings = ignore_warnings
        self._cpu_processes = cpu_processes         # get no of cpu processes
        self._cpu_dict = get_cpu_info()             # cpu info function
        self._name = self._cpu_dict["brand_raw"]    # get cpu name
        self._tdp = find_tdp_value(
            self._name, "cpu_power.csv", self._ignore_warnings)  # find tdp
        self._consumption = 0                                # cpu consumption
        self._cpu_num = number_of_cpu(
            self._ignore_warnings)  # user defined function
        self._start = time.time()                            # calculation start time
        self._operating_system = platform.system()           # get os name

    def tdp(self):          # get tdp
        return self._tdp

    def name(self,):      # get cpu name
        return self._name

    def cpu_num(self,):     # get number of cpus
        return self._cpu_num

    def set_consumption_zero(self):
        self._consumption = 0

    def get_consumption(self):       # get cpu consumption
        self.calculate_consumption()
        return self._consumption

    def get_cpu_percent(self,):
        # cpu_percent:float - cpu utilizationin [0, 1], The current cpu utilization from python processes
        os_dict = {
            # 'Linux': get_cpu_percent_linux,
            'Windows': get_cpu_percent_windows,
            # 'Darwin': get_cpu_percent_mac_os
        }
        cpu_percent = os_dict[self._operating_system](self._cpu_processes)
        return cpu_percent

    # float value - calculates CPU power consumption.
    def calculate_consumption(self):
        time_period = time.time() - self._start
        self._start = time.time()
        # consumption = self._tdp * self.get_cpu_percent() * self._cpu_num * time_period / FROM_WATTs_TO_kWATTh
        consumption = self._tdp * self.get_cpu_percent() * self._cpu_num * time_period
        if consumption < 0:
            consumption = 0
        self._consumption += consumption
        return consumption


"""
    This function prints all seeable CPU devices
    All the CPU devices are intended to be of the same model
        
    Parameters
    ----------
    No parameters
        
    Returns
    -------
    No returns

"""


def all_available_cpu():  # This function prints all seeable CPU devices
    try:
        cpu_dict = get_cpu_info()
        string = f"""Seeable cpu device(s):
        {cpu_dict["brand_raw"]}: {number_of_cpu()} device(s)"""
        print(string)
    except:
        print("There is no any available cpu device(s)")


"""
    This function returns number of CPU sockets(physical CPU processors)
    If the body of the function runs with error, number of available cpu devices will be set to 1
        
    Parameters
    ----------
    ignore_warnings: bool   
    Returns
    -------
    cpu_num: int
     Number of CPU sockets(physical CPU processors)

"""


def number_of_cpu(ignore_warnings=True):
    operating_system = platform.system()
    cpu_num = None

    if operating_system == "Linux":
        try:
            # running terminal command, getting output
            string = os.popen("lscpu")
            output = string.read()
            output
            # dictionary creation
            dictionary = dict()
            for i in output.split('\n'):
                tmp = i.split(':')
                if len(tmp) == 2:
                    dictionary[tmp[0]] = tmp[1]
            cpu_num = min(int(dictionary["Socket(s)"]), int(
                dictionary["NUMA node(s)"]))
        except:
            if not ignore_warnings:
                warnings.warn(
                    message="\nYou probably should have installed 'util-linux' to deretmine cpu number correctly\nFor now, number of cpu devices is set to 1\n\n",
                    category=NoNeededLibrary
                )
            cpu_num = 1
    elif operating_system == "Windows":
        try:
            # running cmd command, getting output
            string = os.popen("systeminfo")
            output = string.read()
            output
            # dictionary creation
            dictionary = dict()
            for i in output.split('\n'):
                tmp = i.split(':')
                if len(tmp) == 2:
                    dictionary[tmp[0]] = tmp[1]
            processor_string = 'something'
            if 'Processor(s)' in dictionary:
                processor_string = dictionary['Processor(s)']
            cpu_num = int(re.findall('- (\d)\.', processor_string)[0])
        except:
            cpu_num = 1
    else:
        cpu_num = 1
    return cpu_num


'''
drops all the waste tokens and patterns
Parameters
----------
cpu_name: str
A string, containing CPU name, taken from psutil library

Returns
-------
cpu_name: str

'''


def transform_cpu_name(cpu_name):
    # dropping all the waste tokens and patterns:
    cpu_name = re.sub(
        '(\(R\))|(®)|(™)|(\(TM\))|(@.*)|(\S*GHz\S*)|(\[.*\])|( \d-Core)|(\(.*\))', '', cpu_name)

    # dropping all the waste words:
    array = re.split(" ", cpu_name)
    for i in array[::-1]:
        if ("CPU" in i) or ("Processor" in i) or (i == ''):
            array.remove(i)
    cpu_name = " ".join(array)
    patterns = re.findall("(\S*\d+\S*)", cpu_name)
    for i in re.findall(
        "(Ryzen Threadripper)|(Ryzen)|(EPYC)|(Athlon)|(Xeon Gold)|(Xeon Bronze)|(Xeon Silver)|(Xeon Platinum)|(Xeon)|(Core)|(Celeron)|(Atom)|(Pentium)",
        cpu_name
    ):
        patterns += i
    patterns = list(set(patterns))
    if '' in patterns:
        patterns.remove('')
    return cpu_name, patterns


def get_patterns(cpu_name):  # find patterns
    patterns = re.findall("(\S*\d+\S*)", cpu_name)
    for i in re.findall(
        "(Ryzen Threadripper)|(Ryzen)|(EPYC)|(Athlon)|(Xeon Gold)|(Xeon Bronze)|(Xeon Silver)|(Xeon Platinum)|(Xeon)|(Core)|(Celeron)|(Atom)|(Pentium)",
        cpu_name
    ):
        patterns += i
    patterns = list(set(patterns))
    if '' in patterns:
        patterns.remove('')
    return patterns


def find_max_tdp(elements):  # finds and returns element with maximum TDP
    if len(elements) == 1:
        return float(elements[0][1])

    max_value = 0
    for index in range(len(elements)):
        if float(elements[index][1]) > max_value:
            max_value = float(elements[index][1])
    return max_value


# searching cpu name in cpu table
def find_tdp_value(cpu_name, f_table_name, constant_value=CONSTANT_CONSUMPTION, ignore_warnings=True):
    # firstly, we try to find transformed cpu name in the cpu table:
    f_table = pd.read_csv('.\data\cpu_names.csv')
    cpu_name, patterns = transform_cpu_name(cpu_name)
    f_table = f_table[["Model", "TDP"]].values
    suitable_elements = f_table[f_table[:, 0] == cpu_name]
    if suitable_elements.shape[0] > 0:
        # if there are more than one suitable elements, return one with maximum TDP value
        return find_max_tdp(suitable_elements)
    # secondly, if needed element isn't found in the table,
    # then we try to find patterns in cpu names and return suitable values:
    # if there is no any patterns in cpu name, we simply return constant consumption value
    if len(patterns) == 0:
        if not ignore_warnings:
            warnings.warn(
                message="\n\nYour CPU device is not found in our database\nCPU TDP is set to constant value 100\n",
                category=NoCPUinTableWarning
            )
        return constant_value
    # appending to array all suitable for at least one of the patterns elements
    suitable_elements = []
    for element in f_table:
        flag = 0
        tmp_patterns = get_patterns(element[0])
        for pattern in patterns:
            if pattern in tmp_patterns:
                flag += 1
        if flag:
            # suitable_elements.append(element)
            suitable_elements.append((element, flag))

    # if there is only one suitable element, we return this element.
    # If there is no suitable elements, we return constant value
    # If there are more than one element, we check existence of elements suitable for all the patterns simultaneously.
    # If there are such elements(one or more), we return the value with maximum TDP among them.
    # If there is no, we return the value with maximum TDP among all the suitable elements
    if len(suitable_elements) == 0:
        if not ignore_warnings:
            warnings.warn(
                message="\n\nYour CPU device is not found in our database\nCPU TDP is set to constant value 100\n",
                category=NoCPUinTableWarning
            )
        return CONSTANT_CONSUMPTION
    elif len(suitable_elements) == 1:
        return float(suitable_elements[0][0][1])
    else:
        suitable_elements.sort(key=lambda x: x[1], reverse=True)
        max_coincidence = suitable_elements[0][1]

        tmp_elements = []
        for element in suitable_elements:
            if element[1] == max_coincidence:
                tmp_elements.append(element[0])
        return find_max_tdp(tmp_elements)


# function to get cpu percent for windows
def get_cpu_percent_windows(cpu_processes="current"):
    cpu_percent = 0
    if cpu_processes == "current":
        current_pid = os.getpid()
        sum_all = 0
        # Iterate over the all running processes
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['name', 'cpu_percent', 'pid'])
            # Check if process pid equals to the current one.
                if pinfo['cpu_percent'] is not None:
                    sum_all += pinfo['cpu_percent']
                    if pinfo['pid'] == current_pid:
                        cpu_percent = pinfo['cpu_percent']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if sum_all != 0:
            cpu_percent /= sum_all
        else:
            cpu_percent = 0
    elif cpu_processes == "all":
        cpu_percent = psutil.cpu_percent()/100
    return cpu_percent
