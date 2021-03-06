############
# Standard #
############
import time
import threading

############
# External #
############
import pytest
from ophyd import Device
from ophyd.status import Status
from unittest.mock import Mock

###########
# Package #
###########
from .conftest import show_widget
from typhon.func import FunctionPanel, FunctionDisplay, TyphonMethodButton

kwargs = dict()


@pytest.fixture(scope='function')
def func_display(qtbot):
    # Create mock function
    def foo(first, second: float=3.14, hide: bool=True, third=False):
        kwargs.update({"first": first, "second": second,
                       "hide": hide, "third": third})
    # Create display
    func_dis = FunctionDisplay(foo, annotations={'first': int},
                               hide_params=['hide'])
    qtbot.addWidget(func_dis)
    return func_dis


class MyDevice(Device):

    def __init__(self, *args, **kwargs):
        self.mock = Mock()
        super().__init__(*args, **kwargs)

    def my_method(self):
        self.mock()
        status = Status()

        def sleep_and_finish():
            time.sleep(3)
            status._finished()

        self._thread = threading.Thread(target=sleep_and_finish)
        self._thread.start()
        return status


@pytest.fixture(scope='function')
def method_button(qtbot):
    dev = MyDevice(name='test')
    button = TyphonMethodButton.from_device(dev)
    qtbot.addWidget(button)
    button.method_name = 'my_method'
    return button


@show_widget
def test_func_display_creation(func_display, qtbot):
    # Check we made the proper number of control widgets
    assert len(func_display.param_controls) == 3
    # Check our hidden parameter is not available
    assert 'hide' not in [widget.parameter
                          for widget in func_display.param_controls]
    # Check that we sorted our parameters correctly
    assert 'first' in func_display.required_params
    assert all([key in func_display.optional_params
                for key in ['second', 'third']])
    return func_display


def test_func_execution(func_display):
    # Configure parameters
    func_display.param_controls[0].param_edit.setText('1')
    func_display.param_controls[1].param_edit.setText('3.14159')
    func_display.param_controls[2].param_control.setChecked(True)
    # Check function execution
    func_display.execute()
    assert kwargs['first'] == 1
    assert kwargs['second'] == 3.14159
    assert kwargs['hide']
    assert kwargs['third']


def test_func_exceptions(func_display):
    # Clear our cache
    kwargs.clear()
    # Configure parameters
    # Improper typing
    func_display.param_controls[0].param_edit.setText('Invalid')
    func_display.param_controls[1].param_edit.setText('3.14159')
    func_display.param_controls[2].param_control.setChecked(True)
    # Check function execution
    func_display.execute()
    # Check our function was not run
    assert kwargs == {}


@show_widget
def test_func_panel(qtbot):
    # Mock functions
    def foo(a: int, b: bool=False, c: bool=True):
        pass

    def foobar(a: float, b: str, c: float=3.14, d: bool=False):
        pass
    # Create Panel
    fp = FunctionPanel([foo, foobar])
    qtbot.addWidget(fp)
    # Check that all our methods made it in
    assert 'foo' in fp.methods
    assert 'foobar' in fp.methods
    return fp


def test_method_button_execute(method_button):
    assert method_button.method_name == 'my_method'
    method_button.execute()
    dev = method_button.devices[0]
    assert dev.mock.called


def test_method_button_use_status(qtbot, method_button):
    method_button.use_status = True
    assert method_button.use_status == True
    method_button.execute()
    assert not method_button._status_thread is None
    qtbot.waitUntil(lambda : not method_button.isEnabled(), timeout=5000)
    qtbot.waitUntil(method_button.isEnabled, timeout=5000)
