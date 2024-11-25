import asyncio
import io 
import sys

from ttboard.demoboard import DemoBoard

def start_soon(c):
    pass

_RunnerSingleton = None 
class Runner:
    
    @classmethod 
    def get(cls):
        global _RunnerSingleton
        if _RunnerSingleton is None:
            _RunnerSingleton = cls()
            
        return _RunnerSingleton
    
    @classmethod 
    def clear_all(cls):
        global _RunnerSingleton
        # clear the singleton 
        _RunnerSingleton = None
    
    def __init__(self):
        self.tests_to_run = dict()
        self.test_names = []
        self.skipped_names = []
        
    def add_test(self, func, name:str=None):
        if name is None:
            name = f'test_{func.__name__}'
        self.test_names.append(name)
        self.tests_to_run[name] = func
        
    def add_skipped(self, name:str):
        self.skipped_names.append(name)
        
    def test(self, dut):
        from ttboard.cocotb.time.system import SystemTime
        from ttboard.cocotb.clock import Clock
        
        ttdb = DemoBoard.get()
        if ttdb.is_auto_clocking:
            dut._log.debug("Stopping ttdb auto-clocking")
            ttdb.clock_project_stop()
        
        num_failures = 0
        num_tests = len(self.test_names)
        failures = dict()
        for test_count in range(num_tests):
            nm = self.test_names[test_count]
            SystemTime.reset()
            Clock.clear_all()
            failures[nm] = None
            try:
                dut._log.info(f"*** Running Test {test_count+1}/{num_tests}: {nm} ***") 
                self.tests_to_run[nm](dut)
                dut._log.warn(f"*** Test '{nm}' PASS ***")
            except Exception as e:
                buf = io.StringIO()
                sys.print_exception(e, buf)
                dut._log.error(buf.getvalue())
                if len(e.args):
                    dut._log.error(f"T*** Test '{nm}' FAIL: {e.args[0]} ***")
                    if e.args[0] is None or not e.args[0]:
                        failures[nm] = " "
                    else:
                        failures[nm] = e.args[0]
                        
                else:
                    failures[nm] = " "
                    
                num_failures += 1
            
                
        if num_failures:
            dut._log.warn(f"{num_failures}/{len(self.test_names)} tests failed")
        else:
            dut._log.info(f"All {len(self.test_names)} tests passed")
        
        dut._log.info("*** Summary ***")
        for nm in self.test_names:
            if failures[nm]:
                dut._log.error(f"\tFAIL\t{nm}\t{failures[nm]}")
            else:
                if nm in self.skipped_names:
                    dut._log.warn(f"\tSKIP\t{nm}")
                else:
                    dut._log.warn(f"\tPASS\t{nm}")
        
        
        
def get_runner(sim=None):
    return Runner.get()


def test(func=None, *,
    timeout_time: float = None,
    timeout_unit: str = "step",
    expect_fail: bool = False,
    expect_error:Exception = None,
    skip: bool = False,
    stage: int = 0,
    name: str = None):
    
    def my_decorator_func(func):
        runner = Runner.get() 
        test_name = func.__name__ if name is None else name
        def wrapper_func(dut):  
            asyncio.run(func(dut))
        
        def skipper_func(dut):
            dut._log.warn(f"{test_name} skip=True")
        
        if skip:
            runner.add_skipped(test_name)
            runner.add_test(skipper_func, test_name)
            return skipper_func
        runner.add_test(wrapper_func, test_name)
        return wrapper_func
    
    return my_decorator_func
