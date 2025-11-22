# cupom dallanese: DLN10

from collections.abc import Iterable
from dataclasses import dataclass
import sys
from typing import Any, SupportsIndex
import numpy as np                                                  
import matplotlib.pyplot as plt                                     
from matplotlib.axes import Axes                                    
from matplotlib.lines import Line2D                                 
from matplotlib.text import Text                                    
from matplotlib.legend import Legend                                
from matplotlib.widgets import TextBox                              
from matplotlib.backend_bases import KeyEvent as mplKeyEvent        
from matplotlib.backend_bases import MouseEvent as mplMouseEvent    
from matplotlib.backend_bases import PickEvent as mplPickEvent      
from matplotlib.backend_bases import CloseEvent as mplCloseEvent    
import copy
import math

from overrides import override


def submit(text:str):
    global axbox, text_box, dct
    label:str = copy.deepcopy(text.capitalize())
    print(f'submit:{text=}, {label=}, {dct=}')
    if not len(text): return
    ax.set_ylabel(label, fontsize=12)
    text_box.set_val('')
    text_box.disconnect(dct)
    axbox.set_visible(False)
    fig.canvas.draw_idle()
    fig.canvas.flush_events()


def on_pick(event:mplPickEvent) -> None:
    """Pick event dispatcher for lines, legends and text annotations."""
    global fig, axbox, text_box, dct
    if isinstance(event.artist, Line2D):
        line=event.artist
        xdata, ydata=line.get_data()
        w:int=len(event.ind)
        idx=event.ind[w//2]
        text_box.label = 'Enter text'
        dct = text_box.on_submit(submit)
        axbox.set_visible(True)
        print(f'{line.get_label()=}, {len(xdata)=}, {idx=}, {dct=}')
    elif isinstance(event.artist, Text):
        text=event.artist
        print(f'{text.get_label()=}, {text.get_text()=}')
    else:
        print(f'on_pick:{event.artist=}')
    fig.canvas.draw_idle()
    fig.canvas.flush_events()


global fig, ax, axbox, text_box, dct
ax:Axes
fig, ax = plt.subplots()

plt.subplots_adjust(bottom=0.1)
t = np.arange(-2.0, 2.0, 0.001)
s = t ** 2
l, = plt.plot(t, s, lw=2, label='data')
l.set_picker(5.0)

fig.canvas.mpl_connect('pick_event', on_pick)

axbox:Axes = plt.axes([0.15, 0.01, 0.75, 0.03])
axbox.set_visible(False)
text_box:TextBox = TextBox(axbox, 'Enter text', initial='')
dct = 0


plt.show()


# 'H2 100ppm,0.297776V,CH4 100ppm,0.339803V,CH4 50ppm,0.221848V'

# 'H2 100ppm,0.297776V,0.644141V,136.376127s,0.941917V,233.431199s,CH4 100ppm,0.339803V,0.611488V,564.066857s,0.951291V,696.198096s,CH4 50ppm,0.221848V,0.620237V,871.772930s,0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.221848V,0.842085V,1028.243342s'
# '0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.221848V'
# '0.842085V,1028.243342s,0.221848V,0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s'
# '0.951291V,696.198096s,0.842085V,1028.243342s,0.951291V,696.198096s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s,0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.842085V,1028.243342s,0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.951291V,696.198096s,0.842085V,1028.243342s,0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.842085V,1028.243342s'
# '0.842085V,1028.243342s'
# '0.941917V,233.431199s,0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.941917V,233.431199s,0.951291V,696.198096s,0.842085V,1028.243342s'
# '0.941917V,233.431199s,0.951291V,696.198096s,0.842085V,1028.243342s,,H2: 100ppm,,CH4: 100ppm,,CH4: 50ppm'
# ',CH4: 50ppm'
# '0.842085V,1028.243342s,,CH4: 50ppm'
# '0.297776V'
# '0.297776V,0.941917V,233.431199s,0.339803V,0.951291V,696.198096s,0.221848V,Final Baseline,0.617347V,'
# '0.297776V,0.339803V,0.221848V'
# '0.297776V,0.339803V,0.221848V,0.214895V,0.333944V,0.842085V,1028.243342s,Final Baseline,0.617347V,,Artifact'
# ''



# text_measurements=
# [
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1028.24334236, y=0.620237), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1028.24334236, y=0.842085), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1028.24334236, y=0.22184799999999993), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(1028.243342_0.221848)', _MeasAnnotation__text='0.221848V', _MeasAnnotation__ymin=0.620237, _MeasAnnotation__ymax=0.842085, _MeasAnnotation__color='tab:blue', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=10.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '0.221848V'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=696.19809644, y=0.611488), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=696.19809644, y=0.951291), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=696.19809644, y=0.33980299999999997), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(696.198096_0.339803)', _MeasAnnotation__text='0.339803V', _MeasAnnotation__ymin=0.611488, _MeasAnnotation__ymax=0.951291, _MeasAnnotation__color='tab:blue', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=10.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '0.339803V'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=233.43119859, y=0.644141), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=233.43119859, y=0.941917), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=233.43119859, y=0.29777600000000004), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(233.431199_0.297776)', _MeasAnnotation__text='0.297776V', _MeasAnnotation__ymin=0.644141, _MeasAnnotation__ymax=0.941917, _MeasAnnotation__color='tab:blue', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=10.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '0.297776V'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=799.0902751, y=0.633986), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=799.0902751, y=0.951291), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=799.0902751, y=0.31730499999999995), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(799.090275_0.317305)', _MeasAnnotation__text='\nCH4: 50ppm', _MeasAnnotation__ymin=0.633986, _MeasAnnotation__ymax=0.951291, _MeasAnnotation__color='red', _MeasAnnotation__linewidth=2.0, _MeasAnnotation__fontsize=20.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '\nCH4: 50ppm'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=428.28280322, y=0.624612), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=428.28280322, y=0.941917), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=428.28280322, y=0.31730500000000006), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(428.282803_0.317305)', _MeasAnnotation__text='\nCH4: 100ppm', _MeasAnnotation__ymin=0.624612, _MeasAnnotation__ymax=0.941917, _MeasAnnotation__color='red', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=20.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '\nCH4: 100ppm'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=60.42868382, y=0.699681), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=60.42868382, y=0.850287), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=60.42868382, y=0.15060600000000002), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(60.428684_0.150606)', _MeasAnnotation__text='\nH2: 100ppm', _MeasAnnotation__ymin=0.699681, _MeasAnnotation__ymax=0.850287, _MeasAnnotation__color='r', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=20.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '\nH2: 100ppm'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1321.80051711, y=0.62719), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1321.80051711, y=0.842085), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1321.80051711, y=0.21489499999999995), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(1321.800517_0.214895)', _MeasAnnotation__text='0.214895V', _MeasAnnotation__ymin=0.62719, _MeasAnnotation__ymax=0.842085, _MeasAnnotation__color='tab:blue', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=10.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '0.214895V'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>), 
#     MeasAnnotation(_MeasAnnotation__point0=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1660.38352255, y=0.617347), _MeasAnnotation__point1=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1660.38352255, y=0.951291), _MeasAnnotation__point=Point(line=<matplotlib.lines.Line2D object at 0x158c57170>, x=1660.38352255, y=0.333944), _MeasAnnotation__textlabel='_measurement_ch0 V MQ-4 #2(1660.383523_0.333944)', _MeasAnnotation__text='0.333944V', _MeasAnnotation__ymin=0.617347, _MeasAnnotation__ymax=0.951291, _MeasAnnotation__color='r', _MeasAnnotation__linewidth=1.0, _MeasAnnotation__fontsize=10.0, _MeasAnnotation__obj=Text(-12.0, 0.0, '0.333944V'), _MeasAnnotation__vlines=<matplotlib.collections.LineCollection object at 0x158c84e30>)]


# def v(xytext):
#     if not isinstance(xytext, tuple): return False
#     if len(xytext) != 2: return False
#     if not isinstance(xytext[0], float): return False
#     if not isinstance(xytext[1], float): return False
#     return True

# '0.842085V,1028.243342s'
# '0.842085V,1028.243342s,Final Baseline,0.617347V,,,CH4: 50ppm'
# 'Final Baseline
# 0.617347V
# ,CH4: 50ppm'
# 'CH4: 50ppm'
# 'Final Baseline
# 0.617347V
# '
# 'Final Baseline,0.617347V,,CH4: 50ppm,CH4: 100ppm'
# 'Final Baseline,0.617347V,'
# 'Final Baseline,0.617347V,0.842085V,1028.243342s,CH4: 50ppm,CH4: 100ppm,H2: 100ppm'
# '0.214895V'
# '0.214895V,test'
# '0.214895,,,V'

# >>> @dataclass
# ... class Ann(list):
# ...     def __contains__(self, item):
# ...         if super().__contains__(item): return True
# ...         x:float = None
# ...         name:str = None
# ...         if isinstance(item, float): 
# ...             x = item
# ...         if isinstance(item, str):
# ...             name = item
# ...         if getattr(item, 'get_label', None) and callable(item.get_label):
# ...             name = item.get_label()
# ...         if not name and getattr(item, 'x', None):
# ...             x = item.x
# ...         for ann in list(self):
# ...             if name is ann.name: return True
# ...             if x == ann.x: return True
# ...         return False
# ...     def __str__(self):
# ...         return str(super())
# ... 
# >>



@dataclass
class Point:
    line: str
    x: float=0.0
    y: float=0.0

@dataclass
class ann():
    l:list
    def __init__(self):
        self.l=[]
    def __contains__(self, item):
        if item in self.l: return True
        if isinstance(item, float):
            for i in self.l:
                if i.x == item: return True
                if i.y == item: return True
        return False


from collections.abc import Iterable
from dataclasses import dataclass
from overrides import override
from typing import Any, SupportsIndex
import time
import random
import sys


@dataclass
class Anno():
    name: str
    x: float
    y: float
    text: str
    visible: bool = True
    def hide(self):
        self.visible=False
    def show(self):
        self.visible=True

@dataclass
class Meas(Anno):
    textsize: float = 10.0
    linewidth: float = 1.0
    def __init__(self, name: str, x: float, y: float, text: str, textsize: float = 10.0, linewidth: float = 1.0) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.text = text
        self.textsize = textsize
        self.linewidth = linewidth

@dataclass
class Text(Anno):
    textsize: float = 12.0

@dataclass
class Event(Anno):
    textsize: float = 25.0
    linewidth: float = 3.0

class Ann(list):
    def __init__(self, iterable:Iterable[Any] | None=None) -> None:
        if iterable is None:
            iterable = []
        if any([x for x in iterable if not issubclass(type(x), Anno)]):
            raise TypeError(f'Invalid element type. Accepts only (Meas | Text | Event).')
        super().__init__(iterable)
    def __index(self, item):
        if super().__contains__(item): return list.index(self, item)
        x:float = None
        name:str = None
        if isinstance(item, float): 
            x = item
        if isinstance(item, str):
            name = item
        if getattr(item, 'get_label', None) and callable(item.get_label):
            name = item.get_label()
        if not name and getattr(item, 'x', None):
            x = item.x
        for idx, ann in enumerate(list(self)):
            if name == ann.name: return idx
            if x == ann.x: return idx
        return None
    @override
    def __contains__(self, item):
        return self.__index(item) is not None
    @override
    def __setitem__(self, key: SupportsIndex | slice, value: Any | Iterable[Any]) -> None:
        if value is None: raise ValueError('value None is invalid.')
        if any([x for x in value if not issubclass(type(x), Anno)]):
            raise TypeError(f'Invalid type. Accepted only (Meas | Text | Event).')
        super().__setitem__(key, value)
    @override
    def __str__(self):
        return str(list(self))
    @override
    def __repr__(self):
        return f'Ann({list(self)})'
    @override
    def index(self, value: Any, start: SupportsIndex = 0, stop: SupportsIndex = sys.maxsize, /) -> int:
        idx = self.__index(value)
        if idx is None: raise ValueError(f'{value} is not in list')
        return idx
    @override
    def append(self, object: Any, /) -> None:
        if not issubclass(type(object), Anno):
            raise TypeError(f'{object}: wrong type {type(object)}.')
        super().append(object)
    @override
    def extend(self, iterable: Iterable[Any], /) -> None:
        if any([x for x in iterable if not issubclass(type(x), Anno)]):
            raise TypeError(f'Invalid type. Accepted only (Meas | Text | Event).')
        super().extend(iterable)
    @override
    def insert(self, index: SupportsIndex, object: Any, /) -> None:
        if not issubclass(type(object), Anno):
            raise TypeError(f'{object}: wrong type {type(object)}.')
        super().insert(index, object)



ann=Ann()
m0:Meas=Meas('meas', 1.0, 2.5, 'meas text')
t0:Text=Text('text', 1.1, 2.5, 'text text')
e0:Event=Event('event', 1.4, 2.5, 'event text')
m1:Meas=Meas('meas', 2.0, 2.5, 'meas text')
t1:Text=Text('text', 2.5, 2.5, 'text text')
e1:Event=Event('event', 3.0, 2.5, 'event text')

ann.append(m0)
ann.sort(key=lambda a: a.x)
ann.append(m1)
ann.sort(key=lambda a: a.x)
ann.append(t0)
ann.sort(key=lambda a: a.x)
ann.append(t1)
ann.sort(key=lambda a: a.x)
ann.append(e0)
ann.sort(key=lambda a: a.x)
ann.append(e1)
ann.sort(key=lambda a: a.x)

ann


ann[2:4]=(Meas('meas1', 2.5, 'meas text'), Event('event1', 3.0, 'event text'), Text('text2', 2.8, 'text text', 1.0))


import time
import random

def add(l,x):
    lo = 0
    hi = len(l)
    while True:
        # print(f'{lo=},{hi=}')
        if hi-lo == 0:
            l.append(x)
            # print(f'{l}')
            return
        if hi-lo == 1:
            l.insert(hi-1 if l[hi-1]>x else hi, x)
            # print(f'{l}')
            return
        t = lo + ((hi - lo) // 2)
        if l[t] > x:
            hi = t
        if l[t] <= x:
            lo = t


c=1_000_000
t0=time.perf_counter_ns()
for x in range(c):
    pass


t1=time.perf_counter_ns()
elapsed_for = (t1-t0)/c
print(f'{elapsed_for=}')


c=1_000
l1=[]
t0=time.perf_counter_ns()
for _ in range(c):
    x = random.random()*c
    add(l1, x)


t1=time.perf_counter_ns()
elapsed_add = (t1-t0)/c
print(f'{elapsed_add=}')
print(f'{len(l1)=}')


c=1_000_000
l1=[]
t0=time.perf_counter_ns()
for _ in range(c):
    x = random.random()*c
    l1.append(x)


t1=time.perf_counter_ns()
elapsed_append = (t1-t0)/c
print(f'{elapsed_append=}')
print(f'{len(l1)=}')

t0=time.perf_counter_ns()
l1.sort()
t1=time.perf_counter_ns()
elapsed_sort = (t1-t0)/c
print(f'{elapsed_sort=}')
print(f'{len(l1)=}')


c=30_000
def bench_append_sort(c):
    l1=[]
    t0=time.perf_counter_ns()
    for _ in range(c):
        x = random.random()*c
        l1.append(x)
        l1.sort()
    t1=time.perf_counter_ns()
    elapsed_appsort = (t1-t0)/c
    print(f'elapsed_appsort={round(elapsed_appsort,1):_}ns')
    print(f'{len(l1)=}')
    return elapsed_appsort




l1=[]
add(l1,2.5)
add(l1,5.0)
add(l1,3.5)


c=1_000

def bench_add(c):
    l1=[]
    t0=time.perf_counter_ns()
    for _ in range(c):
        x = random.random()*c
        add(l1, x)
    t1=time.perf_counter_ns()
    elapsed_add = (t1-t0)/c
    print(f'elapsed_add={round(elapsed_add,1):_}ns')
    print(f'{len(l1)=:_}')
    return elapsed_add


l1=bench_add(100_000)

l1=bench_append_sort(50_000)



import math

@dataclass
class Sensors():
    _plot: str
    _name: str
    _legend: str
    _unit: str
    _format: str
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def legend(self): return self._legend
    @legend.setter
    def legend(self, legend: str): self._legend = legend
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    def __init__(self, plot: str, name: str, legend: str, unit: str, format: str = '{:.6f}'):
        self._plot = plot
        self._name = name
        self._legend = legend
        self._unit = unit
        self._format = format
        if not hasattr(Sensors, '_sensors'):
            Sensors._sensors = []
        Sensors._sensors.append(self)
    def val(self, vadc: float):
        return vadc
    def strval(self, vadc: float):
        return (self._format + '{}').format(self.val(vadc), self._unit)
    @classmethod
    def count(cls, plotname:str = None):
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(Sensors, '_sensors') else 0
    @classmethod
    def sensors(cls, plotname:str = None):
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(Sensors, '_sensors') else []
    @classmethod
    def names(cls, plotname:str = None):
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname))  if hasattr(Sensors, '_sensors') else []
    @classmethod
    def legends(cls, plotname:str = None):
        return (x.legend for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(Sensors, '_sensors') else []
    def __repr__(self):
        return f'Sensor({self._plot}, {self._name}, {self._legend}, {self._unit})'

@dataclass
class Sensor_T10k(Sensors):
    __beta: float
    __t0: float
    __v0: float
    __vref: float
    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    def __init__(self, plot: str, name: str, legend: str, unit: str):
        super().__init__(plot, name, legend, unit)
        self.set_beta()
    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.__v0 * math.exp(-self.__beta / self.__t0)
    @override
    def val(self, vadc: float):
        return (self.__beta / math.log((vadc + 1e-6) / self.__vref)) - 273.15

@dataclass
class Sensor_O2(Sensors):
    __v0: float
    __v1: float
    __ref_o2: float
    @property
    def baseline(self): return self.__v1
    @baseline.setter
    def baseline(self, baseline: float): self.__v1 = baseline
    def __init__(self, plot: str, name: str, legend: str, unit: str):
        super().__init__(plot, name, legend, unit)
        self.__ref_o2 = 20.9
        self.__v0 = 1.151e-3
        self.__v1 = .960
    def baseline(self, val: float):
        self.a1 = val
    @override
    def val(self, vadc: float):
        return ((vadc - self.__v0) * self.__ref_o2) / (self.__v1 - self.__v0)


from matplotlib.typing import ColorType, LineStyleType, MarkerType



@dataclass
class Sensor():
    _name: str
    _plot: str
    _legend: str
    _unit: str
    _fmt: str
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def legend(self): return self._legend
    @legend.setter
    def legend(self, legend: str): self._legend = legend
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    @property
    def fmt(self): return self._fmt
    @fmt.setter
    def fmt(self, fmt: str): self._fmt = fmt
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.6f}'):
        self.name = name
        self.plot = plot
        self.legend = legend
        self.unit = unit
        self.fmt = fmt
        if not hasattr(Sensor, '_sensors'):
            Sensor._sensors = []
    def val(self, vadc: float):
        return vadc
    def strval(self, vadc: float):
        return (self._fmt + '{}').format(self.val(vadc), self._unit)
    @classmethod
    def clear(cls):
        if hasattr(cls, '_sensors'):
            del cls._sensors
    @classmethod
    def count(cls, plotname:str = None):
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_sensors') else 0
    @classmethod
    def sensors(cls, plotname:str = None):
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def names(cls, plotname:str = None):
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def legends(cls, plotname:str = None):
        return (x.legend for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

@dataclass
class Sensor_H2(Sensor):
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, legend, unit, fmt)
        super()._sensors.append(self)

@dataclass
class Sensor_CH4(Sensor):
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, legend, unit, fmt)
        super()._sensors.append(self)

@dataclass
class Sensor_T10k(Sensor):
    __beta: float       # thermistor Beta
    __vref: float       # Fixed Vref term at R0, T0
    __t0: float         # reference temperature in Kelvins
    __v0: float         # reference voltage (R0 * 100uA)
    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    @property
    def vref(self): return self.__vref
    @property
    def t0(self): return self.__t0
    @property
    def v0(self): return self.__v0
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, legend, unit, fmt)
        self.set_beta()
        super()._sensors.append(self)
    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.v0 * math.exp(-self.beta / self.t0)
    @override
    def val(self, vadc: float):
        return (self.beta / math.log((vadc + 1e-6) / self.vref)) - 273.15

@dataclass
class Sensor_PT100(Sensor):
    __A: float          # RTD A coefficient
    __B: float          # RTD B coefficient
    @property
    def a(self): return self.__A
    @property
    def b(self): return self.__B
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_coeffs()
        super()._sensors.append(self)
    def set_coeffs(self, A: float = 3.9083e-3, B: float = -5.775e-7):
        """Set the transfer function polynomial coefficients."""
        self.__A = A
        self.__B = B
    @override
    def val(self, vadc: float):
        """Return the temperature in Celsius for a given RTD volts reading."""
        return (-self.a + math.sqrt(self.a**2 - (4 * self.b * (1.0 - vadc)))) / (2 * self.b)

@dataclass
class Sensor_O2(Sensor):
    __offset: float     # voltage offset with the sensor shorted
    __baseline: float   # sensor baseline reading in Air
    __ref_o2: float     # percent of O2 in Air
    @property
    def offset(self): return self.__offset
    @offset.setter
    def offset(self, offset: float): self.__offset = offset
    @property
    def baseline(self): return self.__baseline
    @baseline.setter
    def baseline(self, baseline: float): self.__baseline = baseline
    @property
    def ref_o2(self): return self.__ref_o2
    @ref_o2.setter
    def ref_o2(self, ref_o2: float): self.__ref_o2 = ref_o2
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, legend, unit, fmt)
        self.ref_o2 = 20.9      # average O2 concentration in Air
        self.offset = 1.151e-3  # measured voltage offset in the prototype
        self.baseline = 1.00    # set default typical baseline value
        super()._sensors.append(self)
    @override
    def val(self, vadc: float):
        return ((vadc - self.offset) * self.ref_o2) / (self.baseline - self.offset)

@dataclass
class Sensor_AHT(Sensor):
    def __init__(self, name: str, plot: str, legend: str, unit: str, fmt: str = '{:.2f}'):
        super().__init__(name, plot, legend, unit, fmt)
        super()._sensors.append(self)


def create_sensors() -> tuple[Sensor]:
    Sensor.clear()
    Sensor_H2('ch0','main','H2','V','{:.6f}')
    Sensor_CH4('ch1','main','CH4','V','{:.6f}')
    Sensor_O2('ch2','rhum','O2','% O2','{:.2f}')
    Sensor_T10k('ch3','temp','CH4 temp','C','{:.2f}')
    Sensor_AHT('temp','temp','temp','C','{:.2f}')
    Sensor_AHT('rhum','rhum','rhum','%','{:.2f}')
    return tuple(Sensor.sensors())


from matplotlib.typing import ColorType, LineStyleType, MarkerType


@dataclass
class Sensor():
    _name: str
    _plot: str
    _label: str
    _unit: str
    _color: ColorType
    _fmt: str
    @property
    def type(self): return f'{type(self)}'.split('.')[-1].split("'")[0]
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def label(self): return self._label
    @label.setter
    def label(self, label: str): self._label = label
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    @property
    def color(self): return self._color
    @color.setter
    def color(self, color: ColorType): self._color = color
    @property
    def fmt(self): return self._fmt
    @fmt.setter
    def fmt(self, fmt: str): self._fmt = fmt
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        self.name = name
        self.plot = plot
        self.label = label
        self.unit = unit
        self.fmt = fmt
        self.color = color
        if not hasattr(Sensor, '_sensors'):
            Sensor._sensors = []
    def val(self, vadc: float):
        return vadc
    def strval(self, vadc: float):
        return (self._fmt + '{}').format(self.val(vadc), self._unit)
    @classmethod
    def clear(cls):
        if hasattr(cls, '_sensors'):
            del cls._sensors
    @classmethod
    def count(cls, plotname:str = None):
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_sensors') else 0
    @classmethod
    def sensors(cls, plotname:str = None):
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def names(cls, plotname:str = None):
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def labels(cls, plotname:str = None):
        return (x.label for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

@dataclass
class Sensor_H2(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

@dataclass
class Sensor_CH4(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

@dataclass
class Sensor_T10k(Sensor):
    __beta: float       # thermistor Beta
    __vref: float       # Fixed Vref term at R0, T0
    __t0: float         # reference temperature in Kelvins
    __v0: float         # reference voltage (R0 * 100uA)
    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    @property
    def vref(self): return self.__vref
    @property
    def t0(self): return self.__t0
    @property
    def v0(self): return self.__v0
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_beta()
        super()._sensors.append(self)
    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.v0 * math.exp(-self.beta / self.t0)
    @override
    def val(self, vadc: float):
        return (self.beta / math.log((vadc + 1e-6) / self.vref)) - 273.15

@dataclass
class Sensor_PT100(Sensor):
    __A: float          # RTD A coefficient
    __B: float          # RTD B coefficient
    @property
    def a(self): return self.__A
    @property
    def b(self): return self.__B
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_coeffs()
        super()._sensors.append(self)
    def set_coeffs(self, A: float = 3.9083e-3, B: float = -5.775e-7):
        self.__A = A
        self.__B = B
    @override
    def val(self, vadc: float):
        return (-self.a + math.sqrt(self.a**2 - (4 * self.b * (1.0 - vadc)))) / (2 * self.b)

@dataclass
class Sensor_O2(Sensor):
    __offset: float     # voltage offset with the sensor shorted
    __baseline: float   # sensor baseline reading in Air
    __ref_o2: float     # percent of O2 in Air
    @property
    def offset(self): return self.__offset
    @offset.setter
    def offset(self, offset: float): self.__offset = offset
    @property
    def baseline(self): return self.__baseline
    @baseline.setter
    def baseline(self, baseline: float): self.__baseline = baseline
    @property
    def ref_o2(self): return self.__ref_o2
    @ref_o2.setter
    def ref_o2(self, ref_o2: float): self.__ref_o2 = ref_o2
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.ref_o2 = 20.9      # average O2 concentration in Air
        self.offset = 1.151e-3  # measured voltage offset in the prototype
        self.baseline = 1.02    # set default typical baseline value
        super()._sensors.append(self)
    @override
    def val(self, vadc: float):
        return ((vadc - self.offset) * self.ref_o2) / (self.baseline - self.offset)

@dataclass
class Sensor_AHT(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

def create_sensors() -> tuple[Sensor]:
    Sensor.clear()
    Sensor_H2('ch0','main','H2','V','{:.6f}')
    Sensor_CH4('ch1','main','CH4','V','{:.6f}')
    Sensor_O2('ch2','rhum','O2','% O2','{:.2f}')
    Sensor_PT100('ch3','temp','H2 temp','C','{:.2f}')
    Sensor_T10k('ch4','temp','CH4 temp','C','{:.2f}')
    Sensor_AHT('temp','temp','temp','C','{:.2f}')
    Sensor_AHT('rhum','rhum','rhum','%','{:.2f}')
    return tuple(Sensor.sensors())

from matplotlib.typing import ColorType, LineStyleType, MarkerType


@dataclass
class Sensor():
    _name: str
    _plot: str
    _label: str
    _unit: str
    _fmt: str
    _color: ColorType
    @property
    def type(self): return f'{type(self)}'.split('.')[-1].split("'")[0]
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def label(self): return self._label
    @label.setter
    def label(self, label: str): self._label = label
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    @property
    def fmt(self): return self._fmt
    @fmt.setter
    def fmt(self, fmt: str): self._fmt = fmt
    @property
    def color(self): return self._color
    @color.setter
    def color(self, color: ColorType): self._color = color
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        self.name = name
        self.plot = plot
        self.label = label
        self.unit = unit
        self.fmt = fmt
        self.color = color
        if not hasattr(Sensor, '_sensors'):
            Sensor._sensors = []
    def val(self, vadc: float):
        return vadc
    def format(self, vadc: float):
        return (self._fmt + '{}').format(self.val(vadc), self._unit)
    @classmethod
    def clear(cls):
        if hasattr(cls, '_sensors'):
            del cls._sensors
    @classmethod
    def count(cls, plotname:str = None):
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_sensors') else 0
    @classmethod
    def sensors(cls, plotname:str = None):
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def names(cls, plotname:str = None):
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def labels(cls, plotname:str = None):
        return (x.label for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []

@dataclass
class Sensor_H2(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

@dataclass
class Sensor_CH4(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

@dataclass
class Sensor_T10k(Sensor):
    __beta: float       # thermistor Beta
    __vref: float       # Fixed Vref term at R0, T0
    __t0: float         # reference temperature in Kelvins
    __v0: float         # reference voltage (R0 * 100uA)
    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    @property
    def vref(self): return self.__vref
    @property
    def t0(self): return self.__t0
    @property
    def v0(self): return self.__v0
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_beta()
        super()._sensors.append(self)
    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.v0 * math.exp(-self.beta / self.t0)
    @override
    def val(self, vadc: float):
        return (self.beta / math.log((vadc + 1e-6) / self.vref)) - 273.15

@dataclass
class Sensor_PT100(Sensor):
    __A: float          # RTD A coefficient
    __B: float          # RTD B coefficient
    __vref: float       # adc voltage at 0 degrees Celsius
    __Ex: float         # total calibration gain error for Vadc
    __Eo: float         # total offset voltage error (Voffs * 100) for Vadc
    @property
    def a(self): return self.__A
    @property
    def b(self): return self.__B
    @property
    def vref(self): return self.__vref
    @property
    def Ex(self): return self.__Ex
    @property
    def Eo(self): return self.__Eo
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_coeffs()
        super()._sensors.append(self)
    def set_coeffs(self, A: float = 3.9083e-3, B: float = -5.775e-7, vref: float = 1.0, Ex: float = 0.997663, Eo: float = 555e-6):
        self.__A = A
        self.__B = B
        self.__vref = vref
        self.__Ex = Ex
        self.__Eo = Eo
    @override
    def val(self, vadc: float):
        vrtd = vadc * self.Ex + self.Eo
        return (-self.a + math.sqrt(self.a**2 - (4 * self.b * (1.0 - vrtd/self.vref)))) / (2 * self.b)

@dataclass
class Sensor_O2(Sensor):
    __offset: float     # voltage offset with the sensor shorted
    __baseline: float   # sensor baseline reading in Air
    __ref_o2: float     # percent of O2 in Air
    @property
    def offset(self): return self.__offset
    @offset.setter
    def offset(self, offset: float): self.__offset = offset
    @property
    def baseline(self): return self.__baseline
    @baseline.setter
    def baseline(self, baseline: float): self.__baseline = baseline
    @property
    def ref_o2(self): return self.__ref_o2
    @ref_o2.setter
    def ref_o2(self, ref_o2: float): self.__ref_o2 = ref_o2
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.ref_o2 = 20.9      # average O2 concentration in Air
        self.offset = 1.151e-3  # measured voltage offset in the prototype
        self.baseline = 1.02    # set default typical baseline value
        super()._sensors.append(self)
    @override
    def val(self, vadc: float):
        return ((vadc - self.offset) * self.ref_o2) / (self.baseline - self.offset)

@dataclass
class Sensor_H2_Fuel_Cell(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)

@dataclass
class Sensor_AHT(Sensor):
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType = None):
        super().__init__(name, plot, label, unit, fmt, color)
        super()._sensors.append(self)


def create_sensors() -> tuple[Sensor]:
    Sensor.clear()
    Sensor_H2('ch0','main','H2','V','{:.6f}', "tab:blue")
    Sensor_PT100('ch1','temp','PT100','C','{:.2f}', "tab:green")
    Sensor_CH4('ch2','main','CH4','V','{:.6f}', "tab:green")
    Sensor_O2('ch3','rhum','O2','%','{:.2f}', "tab:orange")
    Sensor_H2_Fuel_Cell('ch4','main','H2 Cell','V','{:.6f}', "tab:purple")
    Sensor_AHT('temp','temp','AHT10','C','{:.2f}', "tab:pink")
    Sensor_AHT('rhum','rhum','rhum','%','{:.2f}', "tab:cyan")
    return tuple(Sensor.sensors())



def t(v, ec=0.998193, eo=300e-6, a=3.9083e-3, b=-5.775e-7):
   vc = (v - eo) * ec
   return (-a + math.sqrt(a**2 - (4 * b * (1.0 - vc)))) / (2 * b)



from argparse import Namespace

default = Namespace()
default.quiet           = None                              # suppress status messages but display measurement records
default.silent          = None                              # suppress interactive plot graph and all stdout messages
default.verbose         = None                              # verbose mode, write all messages to stdout
default.interactive     = True                              # internal state for interactive plot mode
default.debug           = None                              # show SCPI messages
default.plotfromfile    = None                              # plot mode, do not perform data acquisition
default.nosave          = None                              # do not save plot file
default.save            = None                              # force overwrite plot file
default.noannotations   = None                              # suppress plot annotations
default.cont            = True                              # continuous sampling
default.timestamp       = time.time()                       # defaults to program execution time
default.xhigh           = +600.0                            # upper x plot value in seconds 
default.maxp            = 5000.0                            # max points per X viewport
default.wavetime        = 0.0                               # init xmax boundary
default.max_channels    = 6                                 # number of channels


arg=Namespace()
channels = []
suffixes = ('_name','_leg','_plot','_color','_fmt','_unit')

def p(ln):
    fields = ln.split(",")
    if fields[0].startswith("ch") and fields[0].endswith(suffixes):
        arg.__dict__.update({fields[0]:fields[1].strip()})
        arg.__dict__.update({fields[0][:fields[0].index('_')]:True})
        ch = int(fields[0][2:fields[0].index('_')])
        if len(channels) <= ch:
            channels.insert(ch, dict())
        channels[ch].update({fields[0].split('_')[1]:fields[1].strip()})


def v(ln):
    fields = ln.split(",")
    if (fields[0].endswith('s')):
        # match data line pattern 
        for i in range(1,len(fields)):
            if not fields[i].endswith(channels[i-1]['unit']):
                break
        else:
            bufidx.append(float(fields[0].replace("s", "")))
            for i in range(1,len(fields)):
                bufval[i-1].append(float(fields[i].strip().replace(channels[i-1]['unit'], "")))


p('ch0_name, ch0, ')
p('ch0_leg, H2, ')
p('ch0_plot, main, ')
p('ch0_color, tab:blue, ')
p('ch0_fmt, {:.6f}, ')
p('ch0_unit, V, ')
p('ch1_name, ch1, ')
p('ch1_leg, PT100, ')
p('ch1_plot, temp, ')
p('ch1_color, tab:green, ')
p('ch1_fmt, {:.2f}, ')
p('ch1_unit, C, ')
p('ch2_name, ch2, ')
p('ch2_leg, CH4, ')
p('ch2_plot, main, ')
p('ch2_color, tab:green, ')
p('ch2_fmt, {:.6f}, ')
p('ch2_unit, V, ')
p('ch3_name, ch3, ')
p('ch3_leg, O2, ')
p('ch3_plot, rhum, ')
p('ch3_color, tab:orange, ')
p('ch3_fmt, {:.2f}, ')
p('ch3_unit, %, ')
p('ch4_name, ch4, ')
p('ch4_leg, H2 Cell, ')
p('ch4_plot, main, ')
p('ch4_color, tab:purple, ')
p('ch4_fmt, {:.6f}, ')
p('ch4_unit, V, ')
p('ch5_name, temp, ')
p('ch5_leg, AHT10, ')
p('ch5_plot, temp, ')
p('ch5_color, tab:pink, ')
p('ch5_fmt, {:.2f}, ')
p('ch5_unit, C, ')
p('ch6_name, rhum, ')
p('ch6_leg, rhum, ')
p('ch6_plot, rhum, ')
p('ch6_color, tab:cyan, ')
p('ch6_fmt, {:.2f}, ')
p('ch6_unit, %, ')

bufidx = []
bufval = [[] for x in range(12)]

fields='0.10559260s, 0.90561100V, 35.71963846C, 1.62413900V, 20.49588712%, 1.00160500V, 35.22000000C, 39.12000000%'.split(',')

v('0.10559260s, 0.90561100V, 35.71963846C, 1.62413900V, 20.49588712%, 1.00160500V, 35.22000000C, 39.12000000%')
v('0.17700333s, 0.90576200V, 35.72531427C, 1.62431400V, 20.49562045%, 1.00200800V, 35.22000000C, 39.12000000%')
v('0.26099361s, 0.90616600V, 35.72454030C, 1.62440700V, 20.49646150%, 1.00177200V, 35.21000000C, 39.10000000%')
v('0.34494948s, 0.90633300V, 35.71731654C, 1.62461700V, 20.49748716%, 1.00167700V, 35.22000000C, 39.09000000%')
v('0.42887322s, 0.90654500V, 35.72505628C, 1.62488500V, 20.49851283%, 1.00170400V, 35.22000000C, 39.09000000%')
v('0.51286472s, 0.90665300V, 35.72221837C, 1.62505500V, 20.49882053%, 1.00178800V, 35.23000000C, 39.09000000%')
v('0.59680573s, 0.90679400V, 35.71293070C, 1.62528200V, 20.49851283%, 1.00190700V, 35.23000000C, 39.10000000%')
v('0.68218394s, 0.90707800V, 35.71189874C, 1.62558900V, 20.49960004%, 1.00201300V, 35.23000000C, 39.07000000%')
v('0.76463518s, 0.90714700V, 35.71396266C, 1.62565400V, 20.50060519%, 1.00201400V, 35.23000000C, 39.07000000%')
v('0.84862888s, 0.90739600V, 35.70648094C, 1.62590300V, 20.50284115%, 1.00184700V, 35.22000000C, 39.10000000%')




import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as lines

class HighlightSelected(lines.VertexSelector):
    def __init__(self, line, fmt='ro', **kwargs):
        super().__init__(line)
        self.markers, = self.axes.plot([], [], fmt, **kwargs)
    def process_selected(self, ind, xs, ys):
        self.markers.set_data(xs, ys)
        self.canvas.draw()

fig, ax = plt.subplots()
x, y = np.random.rand(2, 30)
line, = ax.plot(x, y, 'bs-', picker=5)
selector = HighlightSelected(line)
# plt.show()

ln=[]
for n,l in enumerate(ax.get_lines()):
    print(n,l, l.get_label())
    x,y = l.get_data()
    ln.append(list(zip(x,y)))


for n,v in enumerate(l):
    print(n,v)


def search(val,l):
    if val <= l[0][0]:
        return 0
    for n,v in enumerate(l):
        if n > 0:
            if val > l[n-1][0] and val <= l[n][0]:
                return n
    else:
        return len(l)-1


from collections.abc import Iterable
from dataclasses import dataclass
from overrides import override
from typing import Any, SupportsIndex
import time
import random
import sys
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle
from matplotlib.path import Path
from matplotlib.typing import ColorType, LineStyleType, MarkerType
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as tick
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import LinearLocator
from matplotlib.ticker import ScalarFormatter
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.text import Annotation, Text
from matplotlib.legend import Legend
from matplotlib.widgets import TextBox
from matplotlib.colors import is_color_like
from matplotlib.collections import LineCollection
from matplotlib.backend_bases import KeyEvent as mplKeyEvent
from matplotlib.backend_bases import MouseEvent as mplMouseEvent
from matplotlib.backend_bases import PickEvent as mplPickEvent
from matplotlib.backend_bases import CloseEvent as mplCloseEvent
import numpy as np
from scipy.signal import find_peaks

@dataclass
class Point:
    line: Line2D
    x: float = 0.0
    y: float = 0.0

@dataclass
class Waveform():
    _ax:Axes
    _plot:str
    _label:str
    _baseline:list
    _T0:list
    _peak:list
    _t105:list
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def label(self): return self._label
    @label.setter
    def label(self, label: str): self._label = label
    def __init__(self, ax:Axes, label:str) -> None:
        self._baseline = []
        self._peak = []
        self._t105 = []
        self._T0 = []
        self._label = label
        self._ax = ax
        self._plot = str(ax.get_label())
        if not hasattr(Waveform, '_waveforms'):
            Waveform._waveforms = []
        Waveform._waveforms.append(self)
    def set_baseline(self, p: Point) -> None:
        self._baseline.append(tuple([p.x,p.y]))
        self._baseline.sort()
    def set_t0(self, p: Point) -> None:
        self._T0.append(tuple([p.x,p.y]))
        self._T0.sort()
    def find_peak(self, p: Point) -> None:
        pass
    def find_t105(self, p: Point) -> None:
        pass
    def get_baseline_values(self) -> list:
        return self._baseline
    def get_t105_values(self) -> list:
        return self._t105
    def get_peak_values(self) -> list:
        return self._peak
    @classmethod
    def count(cls, plotname: str | None = None):
        return len([x for x in cls._waveforms if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_waveforms') else 0
    @classmethod
    def waveforms(cls, plotname: str | None = None):
        return (x for x in cls._waveforms if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_waveforms') else []
    @classmethod
    def labels(cls, plotname: str | None = None):
        return (x.label for x in cls._waveforms if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_waveforms') else []


# DIO interface opcodes:
# D6 D5 D4 D3 D2 D1
# 
# 00 xxxx   - IN LOW        Input low nibble
# 01 xxxx   - IN HI         Input high nibble
# 11 0LLL   - OUT LOW n     Output 3 low bits
# 11 1HHH   - OUT HI  n     Output 3 high bits
# 10 0000   - MOT OFF       All motors OFF
# 10 0001   - MOT FWD 01    Motor 01 FWD
# 10 0010   - MOT REV 01    Motor 01 REV
# 10 0101   - MOT FWD 02    Motor 02 FWD
# 10 0110   - MOT REV 02    Motor 02 REV
# 10 1001   - MOT FWD 03    Motor 03 FWD
# 10 1010   - MOT REV 03    Motor 03 REV
# 10 0111   - MOT BRK       All motors BRAKE
# 10 1100   - MEAS          DMM measuring
# 10 1101   - TRIG ON       Trigger motor ON
# 10 1110   - TRIG OFF      Trigger motor OFF
# 10 1011   - NOP           available for definition
# 10 1000   - NOP           available for definition
# 10 0011   - NOP           available for definition
# 10 1111   - NOP           available for definition
# 10 0100   - NOP           available for definition
# 
# Inputs are 5V to 28V.
# Outputs are 1500V isolated Solid State Relay contacts (60V, 700mA), closed when output is ON.
# 
# Digital Inputs: 7  (generic for PLC synchronization)
# 
# Digital Outputs: 8
#           - PASSED        DUT at last position PASSED
#           - REJECT        DUT at last position REJECTED
#           - RDY           Ready for next cycle
#           - OUT4          ...
#           - OUT5          ...
#           - OUT6          ...
#           - OUT7          ...
#           - OUT8          ...
# 
# Motor state outputs: 6
#           - FWD1, REV1    Indicate MOT1 is in FORWARD or REVERSE
#           - FWD2, REV2    Indicate MOT2 is in FORWARD or REVERSE
#           - FWD3, REV3    Indicate MOT3 is in FORWARD or REVERSE
# 
# Analog outputs: 4 
#           - Master Current Monitor (BNC)
#           - Current shunt 1
#           - Current shunt 2
#           - Current shunt 3
# 
# 15A Power Outputs: 3, SSRs for 12V, 15A for motor control. 
#           - Mot1 A,B
#           - Mot2 A,B
#           - Mot3 A,B
# 
# 
# FPGA I/O:
#
#   - 6 pins: in/out shift registers:
#           MOSI/MISO/SCK/RCLKI/RCLKO/CLR
#
#   - 2 UART RX/TX
#
#   - 7 DMM DIO pins: 6 data + OE
#   - 4 bitstream flash
#   - DONE led
#   - clock oscillator
#   - 
# 
############################################################
# Circuit:
#
#   - 4 motor H bridges: 2 PMOS + 2 NMOS + 1 dual driver
#   - 1 high side current monitor w/ overcurrent detection
#   - 1 PMOS high side switch
#   - 1 FFD control for HS switch
#   - isolated digital inputs:
#       - transistor optocouplers PC817
#       - 24V digital inputs
#
#   - isolated digital outputs:
#       - 24V outputs
#       - PC817 NPN outputs
#
#   - analog switch matrix:
#       - IXYS CPC2019 SSR
#       - 4 pts motor current shunt voltage
#       - 1 pt top voltage
#       - 4 pts 2W resistance
#
#
#
#
#




from collections.abc import Iterable
from dataclasses import dataclass
from overrides import override
from typing import Any, SupportsIndex
import time
import random
import sys
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle
from matplotlib.path import Path
from matplotlib.typing import ColorType, LineStyleType, MarkerType
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as tick
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import LinearLocator
from matplotlib.ticker import ScalarFormatter
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.text import Annotation, Text
from matplotlib.legend import Legend
from matplotlib.widgets import TextBox
from matplotlib.colors import is_color_like
from matplotlib.collections import LineCollection
from matplotlib.backend_bases import KeyEvent as mplKeyEvent
from matplotlib.backend_bases import MouseEvent as mplMouseEvent
from matplotlib.backend_bases import PickEvent as mplPickEvent
from matplotlib.backend_bases import CloseEvent as mplCloseEvent
import numpy as np
from scipy.signal import find_peaks
import copy
import math

@dataclass
class Sensor():
    _name: str
    _plot: str
    _label: str
    _unit: str
    _fmt: str
    _color: ColorType | None
    @property
    def type(self): return f'{type(self)}'.split('.')[-1].split("'")[0]
    @property
    def name(self): return self._name
    @name.setter
    def name(self, name: str): self._name = name
    @property
    def plot(self): return self._plot
    @plot.setter
    def plot(self, plot: str): self._plot = plot
    @property
    def label(self): return self._label
    @label.setter
    def label(self, label: str): self._label = label
    @property
    def unit(self): return self._unit
    @unit.setter
    def unit(self, unit: str): self._unit = unit
    @property
    def fmt(self): return self._fmt
    @fmt.setter
    def fmt(self, fmt: str): self._fmt = fmt
    @property
    def color(self): return self._color
    @color.setter
    def color(self, color: ColorType): self._color = color
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.6f}', color: ColorType | None = None):
        self.name = name
        self.plot = plot
        self.label = label
        self.unit = unit
        self.fmt = fmt
        self.color = color
        if not hasattr(Sensor, '_sensors'):
            Sensor._sensors = []
    def val(self, vadc: float):
        """Return the sensor float value from the raw adc volts reading."""
        return vadc
    def format(self, vadc: float):
        """Return a string formatted with the sensor value from the raw adc reading."""
        return (self._fmt + '{}').format(self.val(vadc), self._unit)
    @classmethod
    def clear(cls):
        """Remove all Sensor instances."""
        if hasattr(cls, '_sensors'):
            del cls._sensors
    @classmethod
    def count(cls, plotname: str = None):
        """Return the number of sensors instances for the axes plot, if the plotname is specified, or of all sensors if not."""
        return len([x for x in cls._sensors if (plotname is None) or (x.plot == plotname)]) if hasattr(cls, '_sensors') else 0
    @classmethod
    def sensors(cls, plotname: str = None):
        """Return an iterator for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def names(cls, plotname: str = None):
        """Return an iterator of SCPI names for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x.name for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []
    @classmethod
    def labels(cls, plotname: str = None):
        """Return an iterator of label strings for the sensors defined for the axes plot, if the plotname is specified, or of all sensors if not."""
        return (x.label for x in cls._sensors if (plotname is None) or (x.plot == plotname)) if hasattr(cls, '_sensors') else []


@dataclass
class Sensor_T10k(Sensor):
    __beta: float       # thermistor Beta
    __vref: float       # Fixed Vref term at R0, T0
    __t0: float         # reference temperature in Kelvins
    __v0: float         # reference voltage (R0 * 100uA)
    @property
    def beta(self): return self.__beta
    @beta.setter
    def beta(self, beta: float): self.set_beta(beta)
    @property
    def vref(self): return self.__vref
    @property
    def t0(self): return self.__t0
    @property
    def v0(self): return self.__v0
    def __init__(self, name: str, plot: str, label: str, unit: str, fmt: str = '{:.2f}', color: ColorType | None = None):
        super().__init__(name, plot, label, unit, fmt, color)
        self.set_beta()
        super()._sensors.append(self)
    def set_beta(self, beta: float = 4010.0, t0: float = 298.15, v0: float = 1.0):
        self.__beta = beta
        self.__t0 = t0
        self.__v0 = v0
        self.__vref = self.v0 * math.exp(-self.beta / self.t0)
    def vadc(self, temp: float):
        K0 = 273.15
        vadc = self.v0 * math.exp(self.beta * (1/(temp + K0) - 1/self.t0))
        return vadc
    @override
    def val(self, vadc: float):
        if vadc <= 0.0: vadc = 1e-6     # saturate zero/negative values to avoid domain errors
        return (self.beta / math.log(vadc / self.vref)) - 273.15




s=Sensor_T10k('ch0','temp','Thermistor','C','{:.2f}')




#                _               _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _  
#   50%         / \_            / \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_
#               
#                _   __          _   __   _   __   _   __   _   __   _   __   _   __   _   __   _   __   _   _   _  
#   60%         / \_/  \_       / \_/  \_/ \_/  \_/ \_/  \_/ \_/  \_/ \_/  \_/ \_/  \_/ \_/  \_/ \_/  \_/ \_/ \_/ \_
#               
#                _   ___   _   __         _   ___   _   ___   _   ___   _   ___   _   ___   _   ___   _   ___   _   ___  
#   63.63%      / \_/   \_/ \_/  \_      / \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_
#               
#                _   ___         _   ___   _   ___   _   ___   _   ___   _   ___   _   ___   _   ___   _   ___  
#   66.66%      / \_/   \_      / \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_/ \_/   \_
#               
#                __   ___        __   ___   __   ___   __   ___   __   ___   __   ___   __   ___   __   ___   __   ___  
#   72%         /  \_/   \_     /  \_/   \_/  \_/   \_/  \_/   \_/  \_/   \_/  \_/   \_/  \_/   \_/  \_/   \_/  \_/   \_
#               
#                __   ____       __   ____   __   ____   __   ____   __   ____   __   ____   __   ____   __   ____  
#   75%         /  \_/    \_    /  \_/    \_/  \_/    \_/  \_/    \_/  \_/    \_/  \_/    \_/  \_/    \_/  \_/    \_
#               
#                _   _   _    _   _    _   _    _   _    _   _    _   _    _   _    _   _   _    _   _   
#   47%         / \_/ \_/ \__/ \_/ \__/ \_/ \__/ \_/ \__/ \_/ \__/ \_/ \__/ \_/ \__/ \_/ \_/ \__/ \_/ \__




def pwm(v,c):
    l=[]
    e = v + 1.0 if v > 0.5 else v
    while c > 0:
        if e < 1.0:
            l.append(0)
        else:
            l.append(1)
            e -= 1.0
        e += v
        c -= 1.0
    return l

def gen(v,c=100000):
    l=pwm(v,c)
    ones=float(l.count(1))
    total=float(len(l))
    x=ones/total
    print(l[:25])
    print('ones={}, total={}'.format(ones,total))
    print('v={}, x={}'.format(v,x))
    

gen(0.52)
gen(0.48)
gen(0.6)
gen(0.4)
gen(0.65)
gen(0.35)
gen(0.95)
gen(0.05)


def pwm(v,c):
    l=[]
    e = v + 100.0 if v > 50.0 else v
    while c > 0:
        if e < 100.0:
            l.append(0)
        else:
            l.append(1)
            e -= 100.0
        e += v
        c -= 1.0
    return l

def gen(v,c=10000):
    l=pwm(v,c)
    ones=l.count(1)
    total=len(l)
    x=(ones/total)*100.0
    print(l)
    print(f'{ones=}, {total=}')
    print(f'{v=}, {x=}')



gen(52)
gen(48)
gen(60)
gen(40)
gen(65)
gen(35)
gen(95)
gen(5)


from math import *

def pwm(v,c):
    global delta
    l=[]
    v = int(v)
    e = int(((v<<7) + (255<<7)) if (v > 127) else (v<<7))
    while c > 0:
        if e < (255<<7):
            l.append(0)
        else:
            l.append(1)
            e -= (255<<7)
        e += (v<<7)
        c -= 1
    return l


from math import *

delta:int
delta = 0

def pwm(v,c):
    global delta
    l=[]
    v = int(v)
    while c > 0:
        delta += (v<<7)
        if delta < (255<<7):
            l.append(0)
        else:
            l.append(1)
            delta -= (255<<7)
        c -= 1
    return l

def gen(v,c=100000):
    l=pwm(ceil(v*2.55),c)
    ones=float(l.count(1))
    total=float(len(l))
    x=(ones/total)*100.0
    print(l[:100])
    print('ones={}, total={}'.format(ones,total))
    print('v={}, x={}'.format(v,x))



gen(50.)
gen(52.)
gen(48.)
gen(60.)
gen(40.)
gen(65.)
gen(35.)
gen(75.)
gen(25.)
gen(95.)
gen(5.)


# ----------------------------------------------------------------------


import os, time

pname = '/Users/jonnydoin/Dropbox/develop/python-amp10/python/tests/waveforms_cmds'

def create(p):
    try:
        os.mkfifo(pname)
        print(f"Named pipe '{pname}' created.")
    except OSError as e:
        print(f"Error creating named pipe: {e}")

def writer(p):
    create(p)
    time.sleep(.1)
    pipe_out = os.open(p, os.O_WRONLY)
    print(f"{pipe_out=}")
    for i in range(5):
        message = f"Message {i}\n".encode()
        os.write(pipe_out, message)
        print(f"Writer sent: Message {i}")
    time.sleep(.1)
    os.close(pipe_out)

def remove(p):
    os.remove(p)
    print(f"Named pipe '{p}' removed.")


# ----------------------------------------------------------------------

import os

pname = '/Users/jonnydoin/Dropbox/develop/python-amp10/python/tests/waveforms_cmds'

def reader(p):
    with open(p, 'r') as pipe_in:
        for line in pipe_in:
            print(f"Reader received: {line.strip()}")


def remove(p):
    os.remove(p)
    print(f"Named pipe '{p}' removed.")

# ----------------------------------------------------------------------


from multiprocessing.connection import Listener

listener = Listener(('localhost', 6000), authkey=b'secret password')
running = True
while running:
    conn = listener.accept()
    print('connection accepted from', listener.last_accepted)
    while True:
        msg = conn.recv()
        print(msg)
        if msg == 'close connection':
            conn.close()
            break
        if msg == 'close server':
            conn.close()
            running = False
            break
listener.close()

# ----------------------------------------------------------------------


from multiprocessing.connection import Client
import time

# Client 1
conn = Client(('127.0.0.1', 10000))
conn.send('foo')

conn.send('close connection')
time.sleep(1)
conn.close()

time.sleep(1)



# Client 2
conn = Client(('localhost', 6000), authkey=b'secret password')
conn.send('bar')
conn.send('close server')
conn.close()


# ----------------------------------------------------------------------

import asyncio

async def handle_client(reader, writer):
    """
    Coroutine to handle a single client connection.
    """
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")
    try:
        while True:
            data = await reader.read(100)  # Read up to 100 bytes
            if not data:
                print(f"Client {addr} disconnected.")
                break
            message = data.decode().strip()
            print(f"Received from {addr}: {message}")
            response = f"Echo: {message}\n"
            writer.write(response.encode())
            await writer.drain() # Ensure data is sent
    except asyncio.CancelledError:
        print(f"Handler for {addr} cancelled.")
    finally:
        print(f"Closing connection for {addr}")
        writer.close()
        await writer.wait_closed() # Wait for the writer to fully close

async def main():
    """
    Main function to start the asynchronous server.
    """
    host = '127.0.0.1'
    port = 8888
    server = await asyncio.start_server(handle_client, host, port)
    server_address = server.sockets[0].getsockname()
    print(f"Serving on {server_address}")
    async with server:
        server.serve_forever()



asyncio.run(main())

# ----------------------------------------------------------------------

import threading
import socket 
import asyncio

# def run_server():
#     host = '127.0.0.1'
#     port = 8888
#     server = asyncio.start_server(handle_client, host, port)
#     server_address = server.sockets[0].getsockname()
#     print(f"Serving on {server_address}")
#     with server:
#         server.serve_forever()


async def handle_client(reader, writer):
    """
    Coroutine to handle a single client connection.
    """
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")
    try:
        while True:
            data = await reader.read(100)  # Read up to 100 bytes
            if not data:
                print(f"Client {addr} disconnected.")
                break
            message = data.decode().strip()
            print(f"Received from {addr}: {message}")
            response = f"Echo: {message}\n"
            writer.write(response.encode())
            await writer.drain() # Ensure data is sent
    except asyncio.CancelledError:
        print(f"Handler for {addr} cancelled.")
    finally:
        print(f"Closing connection for {addr}")
        writer.close()
        await writer.wait_closed() # Wait for the writer to fully close

async def run_server():
    """
    Main function to start the asynchronous server.
    """
    host = '127.0.0.1'
    port = 8888
    server = await asyncio.start_server(handle_client, host, port)
    server_address = server.sockets[0].getsockname()
    print(f"Serving on {server_address}")
    async with server:
        await server.serve_forever()


# Start the server in a new thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True  # Allow the main program to exit even if the server thread is running
server_thread.start()


# ----------------------------------------------------------------------


import socket
import time 

host = '127.0.0.1'
port = 57000

def send(server, msg):
    try: 
        server.send(msg.encode())
        response = server.recv(1024).decode()
        return response
    except BrokenPipeError as e:
        return str(e)

def conn(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    return server


server = conn(host, port)

send(server, "Hello World")

server.close()



def collect_droplets(dir='right', step=2.0):
    min = float(send(server, ":pwm1:min?"))
    max = float(send(server, ":pwm1:max?"))
    if any(x in dir for x in ('both', 'right')):
        send(server, ":pwm1:val min")
        x = min
        while x <= max:
            send(server, f':pwm1:val {x}')
            x += step
    if any(x in dir for x in ('both', 'left')):
        send(server, ":pwm1:val max")
        x = max
        while x >= min:
            send(server, f':pwm1:val {x}')
            x -= step
    send(server, ":pwm1:val min")


def collect_droplets(step=2.0):
    min = float(send(server, ":pwm1:min?"))
    max = float(send(server, ":pwm1:max?"))
    send(server, ":pwm1:val min")
    x = min
    while x <= max:
        send(server, f':pwm1:val {x}')
        x += step
    send(server, ":pwm1:val min")
    send(server, ":pwm1:sav")



collect_droplets()



# ----------------------------------------------------------------------

import socket
import threading

def handle_client(client_socket, address):
    print(f"Accepted connection from {address}")
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f"Client {address} disconnected.")
                break
            message = data.decode().strip()
            print(f"Received from {address}: {message}")
            response = f"Echo: {message}\n"
            client_socket.sendall(response.encode())
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection with {address} closed.")


def server_listener(server_socket):
    while True:
        client_socket, address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
        client_handler.start()

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows immediate reuse of the address
    server_socket.bind((host, port))
    server_socket.listen(5) # Max 5 queued connections
    print(f"Server listening on {host}:{port}")
    server_thread = threading.Thread(target=server_listener, args=(server_socket,))
    server_thread.start()


host = '127.0.0.1'
port = 8888
start_server(host, port)


# ----------------------------------------------------------------------


import socket
import time 


host = '127.0.0.1'
cmd_port = 57000
data_port = 58000


bufidx=[]
bufadc=[]


# 18.050957s,1.038759V,49.82C,20.90%,1.004530V,22.40C,26.68C,22.59C,22.60C,27.20C,40.13%,-17.99%,33.33%,0.00%,0.00%


def conn(host, port) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    return server

def capture(count):
    data = conn(host, data_port)
    recno = 0
    wavetime = 0.0
    try:
        while count:
            l = data.recv(1024).decode()
            if not l:
                break
            print(f'{l}')
            (wavetime,*record)=l.replace('V','').replace('%','').replace('C','').replace('s','').split(',')
            bufidx.append([recno,float(wavetime)])
            bufadc.append((float(x) for x in record))
            recno += 1
            count -= 1
    except Exception as e:
        print(f'Exception {e}.')
        data.close()


def listen():
    data = conn(host, data_port)
    try:
        data.send(":DATA:LISTEN".encode())
        while True:
            l = data.recv(1024).decode()
            if not l:
                break
            print(f'{l}')
            #if any(x in l for x in ("ERR", "OK")):
            if "ERR" in l or "OK" in l:
                break
    except Exception as e:
        print(f'Exception {e}.')
    finally:
        data.close()

def read(t0=None, t1=None):
    data = conn(host, data_port)
    try:
        arg = "" if not t0 else f'{t0}'
        arg += "" if not t1 else f', {t1}'
        data.send(f":DATA:READ? {arg}".encode())
        while True:
            l = data.recv(8192).decode(encoding="ascii",errors="replace").replace("\n\n", "\n")
            if not l:
                break
            print(f'{l}')
            if any(x in l for x in("ERR", "OK")):
                break
    except Exception as e:
        print(f'Exception {e}.')
    finally:
        data.close()



def send(server, msg):
    try: 
        server.send(msg.encode())
        response = server.recv(1024).decode()
        return response
    except BrokenPipeError as e:
        return str(e)


def find_time_index(t:float):
    try:
        while len(bufidx[0]) < 2:
            bufidx.pop(0)
        while len(bufidx[-1]) < 2:
            bufidx.pop(-1)
        if (t >= bufidx[0][1]) and (t <= bufidx[-1][1]):
            for p in range(len(bufidx)):
                if len(bufidx[p]) > 1:
                    if t <= bufidx[p][1]:
                        return p
                else:
                    bufidx.pop(p)
            else:
                return len(bufidx)-1
        elif t < bufidx[0][1]:
            return 0
        else:
            return len(bufidx)-1
    except IndexError:
        return 0



def boot():
    cmd = conn(host, cmd_port)
    try:
        print(f'{send(cmd, "*idn?")}')
        send(cmd, ":dout0.0:write 1")
        send(cmd, ":dout0.1:write 1")
        send(cmd, ":pwm3:outp:ena")
        send(cmd, ":pwm4:outp:ena")
    except Exception as e:
        print(f'ERROR: Exception {e}')
    finally:
        cmd.close()


def shutdown():
    cmd = conn(host, cmd_port)
    try:
        send(cmd, ":cmd:hmc:shutdown")
    except Exception as e:
        print(f'ERROR: Exception {e}')
    finally:
        cmd.close()


data = conn(host, data_port)
cmd = conn(host, cmd_port)


import collections

d = collections.deque(maxlen=10)

print(d)

for i in range(20):
    d.append(i)

print(d)





pip install overrides
pip install python-usbtmc
pip install pyusb
pip install serial
sudo usermod -a -G dialout $USER
cd <parent DAQ>
source DAQ/bin/activate



host = '127.0.0.1'
cmd_port = 57000
data_port = 58000


def sock_connect(host, port) -> socket.socket:
    """Create a TCP stream connection, and returns the handler."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    return server



def set_valve(name, state):
    """Control the valves solenoids."""
    try:
        if any(x == state.upper() for x in("ON", "OFF")):
            val = 1 if state.upper() == "ON" else 0
            print(f'set_valve, {name}, {state}, {val=}')
            with sock_connect(host, cmd_port) as cmd:
                match name.upper():
                    case 'SYRINGE':
                        send(cmd, f':dout0.7:write {val}')       # SYRINGE valve
                    case 'SENSORS':
                        send(cmd, f':dout0.6:write {val}')       # SENSORS valve
                    case 'INTAKE':
                        send(cmd, f':dout0.5:write {val}')       # INTAKE valve
                    case 'PURGE':
                        send(cmd, f':dout0.4:write {val}')       # PURGE valve
                    case 'STILL':
                        send(cmd, f':dout0.3:write {val}')       # STILL valve
                    case 'COOLING2':
                        send(cmd, f':dout0.2:write {val}')       # COOLING2 fan
                    case 'COOLING1':
                        send(cmd, f':dout0.1:write {val}')       # COOLING1 fan
                    case 'PUMP':
                        send(cmd, f':dout0.0:write {val}')       # PUMP fan
    except:
        pass


bufadc=[]


def capture():
    with sock_connect(host, data_port) as data:
        while True:
            record = data.recv(1024)
            if not record:
                break
            print(record.decode())
            bufadc.append([float(x.replace('s','').replace('V','').replace('C','').replace('%','')) for x in s.split(',')[1:]])







CH4 T105 = 0.40488499999999994
CH4 T105 = 0.4052859999999999



TGS: 1.041503-0.957352 := 0.08415100000000009
H2:  1.665618 - 1.0021 :=  0.663518

TGS: 1.036445-0.955879 := 0.08056600000000003
H2:  1.650373-0.997746  := 0.6526270000000001

TGS: 1.04164-0.960535 := 0.08110499999999987
H2:  1.655589-0.986585 := 0.6690039999999999

TGS: 1.035797-0.954145 := 0.08165200000000006
H2:  1.643058-0.984746 := 0.6583119999999999

TGS: 1.032293-0.951502 := 0.08079099999999995
H2:  1.642112-0.98233 := 0.659782

ch4_drift=[-0.0006485000000000518]
h2_drift=[-0.0007550000000000612]








def median_avg(s, p1, period):
    """Compute the median average for a buffer slice. s = sensor index, pos = ending position, period = integration length."""
    p0 = find_time_index(bufidx[p1][1] - period)
    if p0 == -1:
        p0 = 0
    # extract the tuple of sensors values from the slice, and index the sensor tuple to extract only the value of that sensor. 
    X = tuple(t[s] for t in bufadc[p0:p1+1])
    m = np.median(X)
    return m



if any(x == fields[0] for x in(":CMD:BASE:DRIFT?",)):
    # ":CMD:BASE:DRIFT? <fieldname>[, <interval>]"
    # Request the specified channel baseline drift for the specified period or for the last minute, and report in units/minute.
    response = "ERR"
    try:
        if fields[1] in Sensor.labels():
            sns = tuple(Sensor.labels()).index(fields[1])
            print(f'{sns=}')
            if len(fields) > 2:
                interval = conv_float(fields[2])
            else:
                interval = 60.0
            print(f'{interval=}')
            if interval == 0.0: interval = 60.0
            with buf_lock:
                # get the time interval
                t1 = bufidx[-1][1]
                t0 = t1 - interval
                if (t0 < bufidx[0][1]): t0 = bufidx[0][1]
                print(f'{t0=},{t1=}')
                # find the datapoints indexes for the time coordinates
                p0 = find_time_index(t0)
                p1 = find_time_index(t1)
                print(f'{p0=},{p1=}')
                # compute the median baseline value at the 2 interval ends with 1.0s of integration time
                b0 = tuple(Sensor.sensors())[sns].val(median_avg(sns, p0, 1.0))
                b1 = tuple(Sensor.sensors())[sns].val(median_avg(sns, p1, 1.0))
                print(f'{b0=},{b1=}')
                # compute the drift and differentiate in 1 minute
                drift = b1 - b0
                diff = drift / interval * 60.0
                response = f'{diff}'
    except Exception as e:
        response = f'ERR: {e}'
    finally:
        client_socket.sendall(response.encode())




# binary search for buf[p][1]
# remove defective records
# recursive top down binary tree search



# ---- clipboard -----

import numpy as np
from numpy.polynomial import polynomial as P
import matplotlib.pyplot as plt

h2_100ppmh2 =   [0.663689,0.664437,0.678313,0.690776,0.678403,0.673957,0.676527]
h2_50ppmh2 =    [0.326102,0.299127,0.339004,0.339721,0.343372]

tgs_100ppmh2 =  [0.129414,0.100118,0.100013,0.101356,0.104388,0.102372]
tgs_50ppmh2 =   [0.061276,0.052155,0.059119,0.060538,0.059565]

tgs_100ppm_ch4= [0.388063,0.388313,0.383713,0.387988,0.393117,0.391238,0.384869,0.392897,0.385253,0.396225,0.392278]
tgs_50ppm_ch4 = [0.209040,0.205494,0.206212,0.207439]

cell_adc_h2 = [0.0, np.mean(h2_50ppmh2), np.mean(h2_100ppmh2)]
cell_ppm_h2 = [0.0, 50.0, 100.0]

tgs_adc_h2 = [0.0, np.mean(tgs_50ppmh2)+20e-3, np.mean(tgs_100ppmh2)+20e-3]
tgs_ppm_h2 = [0.0, 50.0, 100.0]

tgs_adc_ch4 = [0.0, np.mean(tgs_50ppm_ch4)+20e-3, np.mean(tgs_100ppm_ch4)+20e-3]
tgs_adc_ch4_min = [0.0, np.min(tgs_50ppm_ch4)+20e-3, np.min(tgs_100ppm_ch4)+20e-3]
tgs_adc_ch4_max = [0.0, np.max(tgs_50ppm_ch4)+20e-3, np.max(tgs_100ppm_ch4)+20e-3]
tgs_ppm_ch4 = [0.0, 50.0, 100.0]

z_cell_adc2h2 = np.polyfit(cell_adc_h2,cell_ppm_h2,deg=1)
z_tgs_adc2h2 = np.polyfit(tgs_adc_h2,tgs_ppm_h2,deg=2)
z_tgs_h2_2adc = np.polyfit(tgs_ppm_h2,tgs_adc_h2,deg=2)
z_tgs_adc2ch4 = np.polyfit(tgs_adc_ch4,tgs_ppm_ch4,deg=2)
z_tgs_adc2ch4_min = np.polyfit(tgs_adc_ch4_min,tgs_ppm_ch4,deg=2)
z_tgs_adc2ch4_max = np.polyfit(tgs_adc_ch4_max,tgs_ppm_ch4,deg=2)

x1 = np.arange(0.0, 800e-3, .001)
plt.plot(x1, np.polyval(z_cell_adc2h2, x1))
plt.title('Linear, H2 Fuel Cell, ADC -> H2')
plt.text(0.1, 50.0, f'{np.poly1d(z_cell_adc2h2)}')
plt.xlabel('ADC (V)')
plt.ylabel('ppm H2')
plt.show()

x2 = np.arange(0.0, 150e-3, .001)
plt.plot(x2, np.polyval(z_tgs_adc2h2, x2))
plt.title('Quadratic, TGS ADC -> H2')
plt.text(0.01, 80.0, f'{np.poly1d(z_tgs_adc2h2)}')
plt.xlabel('ADC (V)')
plt.ylabel('ppm H2')
plt.show()


x3 = np.arange(0.0, 120.0, 1.0)
plt.plot(x3, np.polyval(z_tgs_h2_2adc, x3))
plt.title('Quadratic, TGS H2 -> ADC')
plt.text(10, 0.12, f'{np.poly1d(z_tgs_h2_2adc)}')
plt.xlabel('ppm H2')
plt.ylabel('ADC (V)')
plt.show()


x4 = np.arange(0.0, 400e-3, 1e-3)
plt.plot(x4, np.polyval(z_tgs_adc2ch4, x4))
plt.plot(x4, np.polyval(z_tgs_adc2ch4_min, x4))
plt.plot(x4, np.polyval(z_tgs_adc2ch4_max, x4))
axes = plt.gca()
axes.fill_between(x=x4, y1=z_tgs_adc2ch4_min, y2=z_tgs_adc2ch4_max, alpha=0.7)
plt.title('Quadratic, TGS ADC -> CH4')
plt.text(0.05, 80.0, f'{np.poly1d(z_tgs_adc2ch4)}')
plt.xlabel('ADC (V)')
plt.ylabel('ppm CH4')
plt.show()




def calc(h2adc, ch4adc):
    h2ppm = np.polyval(z_cell_adc2h2, [h2adc])
    h2adj = np.polyval(z_tgs_h2_2adc, h2ppm)
    tgs_adjusted = (ch4adc + 20e-3) - h2adj[0]
    ch4ppm = np.polyval(z_tgs_adc2ch4, [tgs_adjusted])
    return (h2ppm[0], ch4ppm[0])

from collections import namedtuple

Calib = namedtuple('Calib', ['tgs_comp', 'cell_h2_100ppm', 'cell_h2_50ppm', 'tgs_h2_100ppm', 'tgs_h2_50ppm', 'tgs_ch4_100ppm', 'tgs_ch4_50ppm'])

calib = Calib(19e-3, .66, .32, .34, .15,  .54, .23)


import os
import sys
import time
import numpy as np


def save_calib_file(txtfname: str, calibdata: dict) -> None:
    """Save the calibration dictionary to the caibration file."""
    if not txtfname.endswith('.txt'):
        raise ValueError("Invalid filename")
    if os.path.exists(txtfname):
        os.remove(txtfname)
    with open(txtfname, "x") as f:
        # identify measurement file in the first line as comment
        f.write(f'# HMC Calibration data generated by {sys.argv[0]}, {time.strftime("%d/%m/%Y %H:%M:%S")}\r\n')
        print("Writing calibration data ...", flush=True)
        for k,v in calibdata.items():
            record = f'{k},{v} \r\n'
            f.write(record)
    print(f'\nData file {txtfname} saved', flush=True)

def read_calib_file(txtfname: str) -> dict:
    """Read the calibration file, and return a dictionary with the read fields."""
    if not txtfname.endswith('.txt'):
        raise ValueError("Invalid filename")
    calibdata = {}
    with open(txtfname, "r") as f:
        for ln in f:
            ln = ln.replace("\r", "").replace("\n", "")
            fields = ln.split(",")
            if fields[0][0]  == '#':
                continue
            if len(fields) > 1:
                calibdata[fields[0]] = fields[1]
    return calibdata



tgs_comp = 19e-3
cell_h2_100ppm = np.mean([0.663689,0.664437,0.678313,0.690776,0.678403,0.673957,0.676527])
cell_h2_50ppm = np.mean([0.326102,0.299127,0.339004,0.339721,0.343372])
tgs_h2_100ppm = np.mean([0.129414,0.100118,0.100013,0.101356,0.104388,0.102372])
tgs_h2_50ppm = np.mean([0.061276,0.052155,0.059119,0.060538,0.059565])
tgs_ch4_100ppm= np.mean([0.388063,0.388313,0.383713,0.387988,0.393117,0.391238,0.384869,0.392897,0.385253,0.396225,0.392278])
tgs_ch4_50ppm = np.mean([0.209040,0.205494,0.206212,0.207439])

calib = dict(tgs_comp = tgs_comp, cell_h2_100ppm = cell_h2_100ppm, cell_h2_50ppm = cell_h2_50ppm, tgs_h2_100ppm = tgs_h2_100ppm, tgs_h2_50ppm = tgs_h2_50ppm, tgs_ch4_100ppm = tgs_ch4_100ppm, tgs_ch4_50ppm = tgs_ch4_50ppm)

