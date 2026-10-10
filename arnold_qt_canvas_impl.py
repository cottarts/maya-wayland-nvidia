# Qt canvas embedded in Arnold; Maya viewport and plugin binaries are unchanged.
# Refresh requested every 50 ms; viewer gestures briefly suspend copying.
if 'arnold_qt_viewer_test' in globals():
 try:arnold_qt_viewer_test.source.show()
 except RuntimeError:pass
import maya.cmds as cmds
from PySide6 import QtCore,QtGui,QtWidgets,QtOpenGL
import shiboken6,ctypes
if 'arnold_qt_viewer_test' in globals():arnold_qt_viewer_test.close()
class ArnoldQtViewerTest(QtWidgets.QGraphicsView):
 def __init__(self,source):
  super().__init__()
  self.source=source
  self.setWindowTitle('Arnold — Qt canvas')
  self.resize(1000,650)
  self.setToolTip('Left drag: pan • Wheel: zoom • F: frame. Rendering controls remain in Arnold RenderView.')
  self.setScene(QtWidgets.QGraphicsScene(self));self.item=self.scene().addPixmap(QtGui.QPixmap())
  self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
  self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
  self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
  self.setBackgroundBrush(QtGui.QColor(45,45,45));self.first=True;self.frames=0;self.dirty=True
  self.source.frameSwapped.connect(self.markDirty)
  self.gl=ctypes.CDLL('libGL.so.1');self.gl.glReadPixels.argtypes=[ctypes.c_int]*4+[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p]
  self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.capture);self.timer.setTimerType(QtCore.Qt.TimerType.PreciseTimer);self.timer.start(33)
 def markDirty(self):self.dirty=True
 def capture(self):
  if not self.dirty or QtWidgets.QApplication.mouseButtons()!=QtCore.Qt.MouseButton.NoButton:return
  try:
   if not self.source.isVisible():return
   prior=QtGui.QOpenGLContext.currentContext();surface=prior.surface() if prior else None
   self.source.makeCurrent()
   if not self.source.context():return
   width=int(self.source.width()*self.source.devicePixelRatio());height=int(self.source.height()*self.source.devicePixelRatio())
   if width<=0 or height<=0:return
   old=ctypes.c_int();self.gl.glGetIntegerv(0x0C02,ctypes.byref(old));self.gl.glReadBuffer(0x0404)
   buf=ctypes.create_string_buffer(width*height*4)
   self.gl.glReadPixels(0,0,width,height,0x1908,0x1401,buf);self.gl.glReadBuffer(old.value)
   self.source.doneCurrent()
   if prior and surface:prior.makeCurrent(surface)
   img=QtGui.QImage(buf.raw,width,height,width*4,QtGui.QImage.Format.Format_RGBA8888).copy().mirrored(False,True)
   self.item.setPixmap(QtGui.QPixmap.fromImage(img));self.scene().setSceneRect(self.item.boundingRect())
   self.frames+=1;self.dirty=False
   if self.first:self.fitInView(self.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio);self.first=False
  except RuntimeError:self.timer.stop()
 def wheelEvent(self,event):
  factor=1.15 if event.angleDelta().y()>0 else 1/1.15;self.scale(factor,factor);event.accept()
 def keyPressEvent(self,event):
  if event.key()==QtCore.Qt.Key.Key_F:self.fitInView(self.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio)
  else:super().keyPressEvent(event)
 def closeEvent(self,event):
  self.timer.stop()
  try:self.source.frameSwapped.disconnect(self.markDirty)
  except (RuntimeError,TypeError):pass
  super().closeEvent(event)
w=next(w for w in QtGui.QGuiApplication.allWindows() if w.metaObject().className()=='CRenderGLWidget' and w.isVisible())
source=shiboken6.wrapInstance(shiboken6.getCppPointer(w)[0],QtOpenGL.QOpenGLWindow)
arnold_qt_viewer_test=ArnoldQtViewerTest(source)

from PySide6 import QtCore,QtWidgets
import maya.cmds as c
v=arnold_qt_viewer_test
arv=next(w for w in QtWidgets.QApplication.allWidgets() if w.metaObject().className()=='CRenderViewWindow' and w.isVisible())
container=next(w for w in arv.findChildren(QtWidgets.QWidget) if w.metaObject().className()=='QWindowContainer')
v.hide();v.setObjectName('ArnoldQtCanvas');v.setParent(container,QtCore.Qt.WindowType.Widget)
v.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow,True)
v.setGeometry(container.rect());v.winId();v.show();v.raise_();v.setFocus()
class ArnoldCanvasSize(QtCore.QObject):
 def eventFilter(self,obj,event):
  if event.type()==QtCore.QEvent.Type.Resize:
   v.setGeometry(obj.rect());v.dirty=True;v.raise_()
  return False
arnold_canvas_size=ArnoldCanvasSize(container);container.installEventFilter(arnold_canvas_size)

from PySide6 import QtCore,QtWidgets
v=arnold_qt_viewer_test
if 'arnold_alt_pan' in globals():
 try:
  v.viewport().removeEventFilter(arnold_alt_pan);v.removeEventFilter(arnold_alt_pan)
 except RuntimeError:pass
class ArnoldAltPan(QtCore.QObject):
 def __init__(self,view):
  super().__init__(view);self.view=view;self.last=None;self.mode=None;self.zoom_anchor=None
 def eventFilter(self,obj,event):
  typ=event.type()
  if typ==QtCore.QEvent.Type.KeyPress and event.key()==QtCore.Qt.Key.Key_F:
   self.view.fitInView(self.view.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio);event.accept();return True
  if typ==QtCore.QEvent.Type.MouseButtonPress and event.button() in (QtCore.Qt.MouseButton.LeftButton,QtCore.Qt.MouseButton.MiddleButton,QtCore.Qt.MouseButton.RightButton):
   if event.button() in (QtCore.Qt.MouseButton.MiddleButton,QtCore.Qt.MouseButton.RightButton) or event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier:
    self.view.setFocus();self.view.viewport().setFocus();self.zoom_anchor=self.view.mapToScene(event.position().toPoint());self.last=event.position();self.mode='zoom' if event.button()==QtCore.Qt.MouseButton.RightButton else 'pan';self.view.viewport().setCursor(QtCore.Qt.CursorShape.SizeHorCursor if self.mode=='zoom' else QtCore.Qt.CursorShape.ClosedHandCursor)
   return True
  if typ==QtCore.QEvent.Type.MouseMove and self.last is not None:
   point=event.position();delta=point-self.last;self.last=point
   if self.mode=='zoom':
    factor=2.0**(delta.x()/300.0)
    scale=self.view.transform().m11()
    if 0.01<scale*factor<100:
     self.view.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.NoAnchor)
     anchor_pixel=self.view.mapFromScene(self.zoom_anchor)
     self.view.scale(factor,factor)
     after=self.view.mapFromScene(self.zoom_anchor)
     h=self.view.horizontalScrollBar();vertical=self.view.verticalScrollBar()
     h.setValue(h.value()+after.x()-anchor_pixel.x());vertical.setValue(vertical.value()+after.y()-anchor_pixel.y())
   else:
    h=self.view.horizontalScrollBar();vertical=self.view.verticalScrollBar()
    h.setValue(h.value()-round(delta.x()));vertical.setValue(vertical.value()-round(delta.y()))
   return True
  if typ==QtCore.QEvent.Type.MouseButtonRelease and event.button() in (QtCore.Qt.MouseButton.LeftButton,QtCore.Qt.MouseButton.MiddleButton,QtCore.Qt.MouseButton.RightButton):
   self.last=None;self.mode=None;self.view.viewport().unsetCursor();return True
  return False
v.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
# Give the fitted image room to move, preserving the current center and zoom.
center=v.mapToScene(v.viewport().rect().center())
v.scene().setSceneRect(v.item.boundingRect().adjusted(-100000,-100000,100000,100000));v.centerOn(center)
arnold_alt_pan=ArnoldAltPan(v);v.viewport().installEventFilter(arnold_alt_pan)
v.installEventFilter(arnold_alt_pan)
v.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
v.viewport().setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
v.setFocus()
v.setToolTip('Middle drag or Alt + left drag: pan • Right drag or wheel: zoom • F: frame.')
if 'arnold_frame_shortcut' in globals():
 try:arnold_frame_shortcut.setEnabled(False);arnold_frame_shortcut.deleteLater()
 except RuntimeError:pass
from PySide6 import QtGui
arnold_frame_shortcut=QtGui.QShortcut(QtGui.QKeySequence('F'),v)
arnold_frame_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
arnold_frame_shortcut.activated.connect(lambda: v.fitInView(v.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio))
v.setFocus();v.viewport().setFocus()

from PySide6 import QtCore,QtGui,QtWidgets
v=arnold_qt_viewer_test
if 'arnold_plain_f' in globals():
 for target in (v,v.viewport()):
  try:target.removeEventFilter(arnold_plain_f)
  except RuntimeError:pass
class ArnoldPlainF(QtCore.QObject):
 def eventFilter(self,obj,event):
  if event.type() in (QtCore.QEvent.Type.ShortcutOverride,QtCore.QEvent.Type.KeyPress) and event.key()==QtCore.Qt.Key.Key_F and event.modifiers()==QtCore.Qt.KeyboardModifier.NoModifier:
   if event.type()==QtCore.QEvent.Type.KeyPress:v.fitInView(v.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio)
   event.accept();return True
  return False
arnold_plain_f=ArnoldPlainF(v)
v.installEventFilter(arnold_plain_f);v.viewport().installEventFilter(arnold_plain_f)
v.setFocus();v.viewport().setFocus()

from PySide6 import QtCore,QtGui,QtWidgets
import maya.cmds as cmds,time,json
v=arnold_qt_viewer_test
v.timer.stop()
try:v.timer.timeout.disconnect()
except RuntimeError:pass
v.source.hide();v.last_input=0.0;v.live_updates=0;v.live_last_ms=0.0;v.crop_first=True;v.crop_size=None;v.resolution_checked=0.0
class ArnoldLiveInput(QtCore.QObject):
 def eventFilter(self,obj,event):
  if event.type() in (QtCore.QEvent.Type.MouseButtonPress,QtCore.QEvent.Type.MouseButtonRelease,QtCore.QEvent.Type.Wheel,QtCore.QEvent.Type.KeyPress) or (event.type()==QtCore.QEvent.Type.MouseMove and event.buttons()!=QtCore.Qt.MouseButton.NoButton):v.last_input=time.monotonic()
  return False
if 'arnold_live_input' in globals():
 try:v.viewport().removeEventFilter(arnold_live_input);v.removeEventFilter(arnold_live_input)
 except RuntimeError:pass
arnold_live_input=ArnoldLiveInput(v);v.viewport().installEventFilter(arnold_live_input);v.installEventFilter(arnold_live_input)
def update_hidden_arnold():
 # Only viewer interactions suspend copying. Camera navigation in Maya stays live.
 if not v.isVisible() or time.monotonic()-v.last_input<0.08:return
 previous=QtGui.QOpenGLContext.currentContext();surface=previous.surface() if previous else None
 start=time.perf_counter()
 try:
  v.source.makeCurrent();v.source.paintEvent(QtGui.QPaintEvent(QtCore.QRect(0,0,v.source.width(),v.source.height())))
  image=v.source.grabFramebuffer()
  if not image.isNull():
   if time.monotonic()-v.resolution_checked>1:
    v.native_resolution=(int(cmds.getAttr('defaultResolution.width')),int(cmds.getAttr('defaultResolution.height')));v.resolution_checked=time.monotonic()
   width,height=v.native_resolution
   if width<=image.width() and height<=image.height():
    image=image.copy((image.width()-width)//2,(image.height()-height)//2,width,height)
   size=(image.width(),image.height())
   v.item.setPixmap(QtGui.QPixmap.fromImage(image));v.scene().setSceneRect(v.item.boundingRect().adjusted(-100000,-100000,100000,100000))
   if v.crop_first or v.crop_size!=size:
    v.fitInView(v.item,QtCore.Qt.AspectRatioMode.KeepAspectRatio);v.crop_first=False;v.crop_size=size
   v.live_updates+=1
 finally:
  v.source.doneCurrent()
  if previous and surface:previous.makeCurrent(surface)
 v.live_last_ms=(time.perf_counter()-start)*1000
v.timer.timeout.connect(update_hidden_arnold);v.timer.start(50)
v.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
v.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff);v.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
v.setBackgroundBrush(QtGui.QColor(38,38,38))
cmds.arnoldRenderView(option=('Scene Updates','1'))
v.show();v.raise_();v.setFocus()
v.setToolTip('Live IPR • Middle drag or Alt + left drag: pan • Horizontal right drag: zoom • F: frame')
