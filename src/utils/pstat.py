from utils.utils import pprint
import time
from munch import DefaultMunch
import psutil
import resource
from pymirror.pmlogger import _print

def get_pid_by_name(process_name):
    """Find PID by process name"""
    for proc in psutil.process_iter(['pid', 'name']):
        if process_name in proc.info['name']:
            return proc.pid
    return None

def get_pids_by_cli(process_name):
    """Find Multiple PIDs by process name"""
    pids = []
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if proc.info["cmdline"] and process_name in " ".join(proc.info['cmdline']):
            _print(">>>", proc.info["cmdline"])
            pids.append(proc.pid)
    return pids

def get_pstat_by_pid(pid):
    """Get resource usage for a specific PID"""
    try:
        process = psutil.Process(pid)
        cpu_times = process.cpu_times()
        memory_info = process.memory_info()
        
        result = DefaultMunch()
        result.pid = pid
        result.user_cpu = cpu_times.user
        result.sys_cpu = cpu_times.system
        result.total_cpu = cpu_times.user + cpu_times.system
        result.memory_rss = memory_info.rss  # Resident Set Size
        result.memory_vms = memory_info.vms  # Virtual Memory Size
        result.cpu_percent = process.cpu_percent()
        result.name = process.name()
        result.cmdline = process.cmdline()  
        result.exe = process.exe()
        result.cwd = process.cwd()
        result.status = process.status() 
        return result
    except psutil.NoSuchProcess:
        return None

def get_pstat_delta(pid, last_pstat):
    """Get resource usage difference from last measurement"""
    current_pstat = get_pstat_by_pid(pid)
    if not current_pstat:
        return DefaultMunch()
    current_pstat.delta = DefaultMunch()
    if not last_pstat:
        current_pstat.delta.user_cpu = 0
        current_pstat.delta.sys_cpu = 0
        current_pstat.delta.total_cpu = 0
        current_pstat.delta.memory_rss = 0
    else:
        current_pstat.delta.user_cpu = current_pstat.user_cpu - last_pstat.user_cpu
        current_pstat.delta.sys_cpu = current_pstat.sys_cpu - last_pstat.sys_cpu
        current_pstat.delta.total_cpu = current_pstat.total_cpu - last_pstat.total_cpu
        current_pstat.delta.memory_rss = current_pstat.memory_rss - last_pstat.memory_rss
    return current_pstat

if __name__ == "__main__":
    pids = get_pids_by_cli("pmtaskmgr")
    pstat = None
    while pids:
        pstat = get_pstat_delta(pids[0], pstat)    
        pprint(pstat)
        time.sleep(2)
        pstat = get_pstat_delta(pids[0], pstat)
        pprint(pstat)
        pids = get_pids_by_cli("pmtaskmgr")
