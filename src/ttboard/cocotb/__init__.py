import asyncio
import io 
import sys

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
        
    def add_test(self, func, name:str=None):
        if name is None:
            name = f'test_{func.__name__}'
        self.test_names.append(name)
        self.tests_to_run[name] = func
        
    def test(self, dut):
        from ttboard.cocotb.time.system import SystemTime
        failures = 0
        for nm in self.test_names:
            SystemTime.reset()
            try:
                self.tests_to_run[nm](dut)
                dut._log.warn(f"Test '{nm}': PASS")
            except Exception as e:
                if len(e.args):
                    dut._log.error(f"FAIL: {e.args[0]}")
                else:
                    buf = io.StringIO()
                    sys.print_exception(e, buf)
                    dut._log.error(buf.getvalue())
                failures += 1
            
                
        if failures:
            dut._log.warn(f"{failures}/{len(self.test_names)} tests failed")
        else:
            dut._log.info(f"All {len(self.test_names)} tests passed")
        
        
        
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
            dut._log.info(f"Running Test: {test_name}")   
            asyncio.run(func(dut))
        
        def skipper_func(dut):
            dut._log.warn(f"{test_name} skipped")
            
        if skip:
            return skipper_func
        
        runner.add_test(wrapper_func, func.__name__)
        return wrapper_func
    
    return my_decorator_func
