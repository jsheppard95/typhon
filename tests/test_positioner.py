from unittest.mock import Mock

import pytest
from ophyd import Component as Cpt, Signal
from ophyd.sim import SynAxis, SignalRO

from typhon.positioner import TyphonPositionerWidget

from .conftest import show_widget


class SimMotor(SynAxis):
    low_limit_switch = Cpt(SignalRO, value=0)
    high_limit_switch = Cpt(SignalRO, value=0)
    low_limit = Cpt(Signal, value=-10)
    high_limit = Cpt(Signal, value=10)
    stop = Mock()


@pytest.fixture(scope='function')
def motor_widget(qtbot):
    motor = SimMotor(name='test')
    setwidget = TyphonPositionerWidget.from_device(motor)
    qtbot.addWidget(setwidget)
    yield motor, setwidget
    if setwidget._status_thread and setwidget._status_thread.isRunning():
        setwidget._status_thread.wait()


def test_positioner_widget_no_limits(qtbot, motor):
    setwidget = TyphonPositionerWidget.from_device(motor)
    qtbot.addWidget(setwidget)
    for widget in ('low_limit', 'low_limit_switch',
                   'high_limit', 'high_limit_switch'):
        assert getattr(setwidget.ui, widget).isHidden()


def test_positioner_widget_fixed_limits(qtbot, motor):
    motor.limits = (-10, 10)
    widget = TyphonPositionerWidget.from_device(motor)
    qtbot.addWidget(widget)
    assert widget.ui.low_limit.text() == '-10'
    assert widget.ui.high_limit.text() == '10'


@show_widget
def test_positioner_widget_with_signal_limits(motor_widget):
    motor, widget = motor_widget
    # Check limit switches
    low_limit_chan = widget.ui.low_limit_switch.channel
    assert motor.low_limit_switch.name in low_limit_chan
    high_limit_chan = widget.ui.high_limit_switch.channel
    assert motor.high_limit_switch.name in high_limit_chan
    motor.delay = 3.  # Just for visual testing purposes
    return widget


def test_positioner_widget_readback(motor_widget):
    motor, widget = motor_widget
    assert motor.readback.name in widget.ui.user_readback.channel


def test_positioner_widget_stop(motor_widget):
    motor, widget = motor_widget
    widget.stop()
    assert motor.stop.called


def test_positioner_widget_set(motor_widget):
    motor, widget = motor_widget
    # Check motion
    widget.ui.set_value.setText('4')
    widget.ui.set()
    assert motor.position == 4


def test_positioner_widget_positive_tweak(motor_widget):
    motor, widget = motor_widget
    widget.ui.tweak_value.setText('1')
    widget.positive_tweak()
    assert widget.ui.set_value.text() == '1.0'
    assert motor.position == 1


def test_positioner_widget_negative_tweak(motor_widget):
    motor, widget = motor_widget
    widget.ui.tweak_value.setText('1')
    widget.negative_tweak()
    assert widget.ui.set_value.text() == '-1.0'
    assert motor.position == -1


def test_positioner_widget_moving_property(motor_widget, qtbot):
    motor, widget = motor_widget
    assert not widget.moving
    motor.delay = 1.
    widget.ui.set_value.setText('34')
    widget.set()
    qtbot.waitUntil(lambda: widget.moving, timeout=500)
    qtbot.waitUntil(lambda: not widget.moving, timeout=1000)


def test_positioner_widget_last_move(motor_widget, qtbot):
    motor, widget = motor_widget
    assert not widget.successful_move
    assert not widget.failed_move
    widget.done_moving(True)
    assert widget.successful_move
    assert not widget.failed_move
    widget.done_moving(False)
    assert not widget.successful_move
    assert widget.failed_move
