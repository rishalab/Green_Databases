import psutil
import time
import os


# FROM_WATTs_TO_kWATTh = 1000*3600

# This class is the interface for tracking RAM power consumption.
class RAM():
    def __init__(self, ignore_warnings=False):
        # This class method initializes RAM object.
        self._consumption = 0
        self._ignore_warnings = ignore_warnings
        self._start = time.time()

    def get_consumption(self):  # This class method initializes RAM object.

        self.calculate_consumption()
        return self._consumption

    def _get_memory_used(self,):
        # This class method calculates amount of virtual memory(RAM) used.
        # Total amount of virtual memory(RAM) used in gigabytes.
        current_pid = os.getpid()
        memory_percent = 0

        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['name', 'pid', 'memory_percent'])

                if pinfo['pid'] == current_pid:
                    # print(pinfo['pid'])
                    memory_percent = float(pinfo['memory_percent'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        total_memory = psutil.virtual_memory().total / (1024 ** 3)
        # print(memory_percent * total_memory / 100)
        return memory_percent * total_memory / 100

    def calculate_consumption(self):
        # This class method calculates RAM power consumption.
        # RAM power consumption: float
        time_period = time.time() - self._start
        self._start = time.time()
        # consumption = self._get_memory_used() * (3 / 8) * time_period / FROM_WATTs_TO_kWATTh
        consumption = self._get_memory_used() * (3 / 8) * time_period
        self._consumption += consumption
        # print(self._consumption)
        return consumption
