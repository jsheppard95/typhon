############
# Standard #
############

############
# External #
############
from ophyd import Signal
from pydm.widgets.base import PyDMWritableWidget
from qtpy.QtWidgets import QWidget

###########
# Package #
###########
from ..conftest import DeadSignal, RichSignal
from typhon.plugins.core import (SignalPlugin, SignalConnection,
                                 register_signal)



class WritableWidget(QWidget, PyDMWritableWidget):
    """Simple Testing Widget"""
    pass




def test_signal_connection(qapp, qtbot):
    # Create a signal and attach our listener
    sig = Signal(name='my_signal', value=1)
    register_signal(sig)
    widget = WritableWidget()
    qtbot.addWidget(widget)
    widget.channel = 'sig://my_signal'
    listener = widget.channels()[0]
    # If PyDMChannel can not connect, we need to connect it ourselves
    # In PyDM > 1.5.0 this will not be neccesary as the widget will be
    # connected after we set the channel name
    if not hasattr(listener, 'connect'):
        qapp.establish_widget_connections(widget)
    # Check that our widget receives the initial value
    qapp.processEvents()
    assert widget._write_access
    assert widget._connected
    assert widget.value == 1
    # Check that we can push values back to the signal which in turn causes the
    # internal value at the widget to update
    widget.send_value_signal[int].emit(2)
    qapp.processEvents()
    qapp.processEvents()  # Must be called twice. Multiple rounds of signals
    assert sig.get() == 2
    assert widget.value == 2
    # Try changing types
    qapp.processEvents()
    qapp.processEvents()  # Must be called twice. Multiple rounds of signals
    # In PyDM > 1.5.0 we will not need the application to disconnect the
    # widget, but until then we have to check for the attribute
    if hasattr(listener, 'disconnect'):
        listener.disconnect()
    else:
        qapp.close_widget_connections(widget)
    # Check that our signal is disconnected completely and maintains the same
    # value as the signal updates in the background
    sig.put(3)
    qapp.processEvents()
    assert widget.value == 2
    widget.send_value_signal.emit(1)
    qapp.processEvents()
    assert sig.get() == 3


def test_metadata(qapp, qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)
    widget.channel = 'sig://md_signal'
    listener = widget.channels()[0]
    # Create a signal and attach our listener
    sig = RichSignal(name='md_signal', value=1)
    register_signal(sig)
    sig_conn = SignalConnection(listener, 'md_signal')
    qapp.processEvents()
    # Check that metadata the metadata got there
    assert widget.enum_strings == ('a', 'b', 'c')
    assert widget._unit == 'urad'
    assert widget._prec == 2


def test_disconnection(qtbot):
    widget = WritableWidget()
    qtbot.addWidget(widget)
    widget.channel = 'sig://invalid'
    listener = widget.channels()[0]
    plugin = SignalPlugin()
    # Non-existant signal doesn't raise an error
    plugin.add_connection(listener)
    # Create a signal that will raise a TimeoutError
    sig = DeadSignal(name='broken_signal', value=1)
    register_signal(sig)
    listener.address = 'sig://broken_signal'
    # This should fail on the subscribe
    plugin.add_connection(listener)
    # This should fail on the get
    sig.subscribable = True
    sig_conn = SignalConnection(listener, 'broken_signal')
