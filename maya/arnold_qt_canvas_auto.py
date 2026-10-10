"""Install the validated Qt canvas when Arnold RenderView is opened."""
from pathlib import Path
from PySide6 import QtCore,QtWidgets
import shiboken6,traceback
_timer=None
_instances=[]
_failed=set()
def _check():
 global _instances
 _instances=[ns for ns in _instances if shiboken6.isValid(ns['arnold_qt_viewer_test'])]
 for window in QtWidgets.QApplication.allWidgets():
  if window.metaObject().className()!='CRenderViewWindow' or not window.isVisible():continue
  if window.findChild(QtWidgets.QWidget,'ArnoldQtCanvas') is not None:continue
  key=shiboken6.getCppPointer(window)[0]
  if key in _failed:continue
  try:
   path=Path(__file__).with_name('arnold_qt_canvas_impl.py')
   ns={'__file__':str(path),'__name__':'arnold_qt_canvas_runtime'}
   exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),ns)
   _instances.append(ns)
  except StopIteration:
   pass # The native GL window may not yet be initialized.
  except Exception:
   _failed.add(key)
   traceback.print_exc()
def start():
 global _timer
 if _timer is not None:return
 _timer=QtCore.QTimer(QtWidgets.QApplication.instance())
 _timer.timeout.connect(_check);_timer.start(500)
def stop():
 if _timer is not None:_timer.stop()
