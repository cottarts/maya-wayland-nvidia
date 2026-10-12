# Full-resolution Qt canvas for Arnold. Maya viewport and plugin binaries are unchanged.
# Active refresh: 50 ms; repeated identical previews back off to 250 ms.
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
  self.setToolTip('Wheel: cursor-centered zoom • F: frame. Rendering controls remain in Arnold RenderView.')
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
  delta=event.angleDelta().y()
  if not delta:event.accept();return
  factor=1.15 if delta>0 else 1/1.15
  if not 0.01<self.transform().m11()*factor<100:event.accept();return
  point=event.position().toPoint();anchor=self.mapToScene(point)
  self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.NoAnchor)
  self.scale(factor,factor)
  after=self.mapFromScene(anchor)
  h=self.horizontalScrollBar();vertical=self.verticalScrollBar()
  h.setValue(h.value()+after.x()-point.x());vertical.setValue(vertical.value()+after.y()-point.y())
  event.accept()
 def pickMesh(self,position,modifiers,pressed):
  point=self.mapToScene(position.toPoint())
  if pressed and not self.item.boundingRect().contains(point):return
  width=self.item.pixmap().width();height=self.item.pixmap().height()
  dpr=self.source.devicePixelRatio()
  offset=QtCore.QPointF((self.source.width()*dpr-width)/2,(self.source.height()*dpr-height)/2)
  local=(point+offset)/dpr
  global_pos=QtCore.QPointF(self.source.mapToGlobal(local.toPoint()))
  typ=QtCore.QEvent.Type.MouseButtonPress if pressed else QtCore.QEvent.Type.MouseButtonRelease
  buttons=QtCore.Qt.MouseButton.LeftButton if pressed else QtCore.Qt.MouseButton.NoButton
  click=QtGui.QMouseEvent(typ,local,global_pos,QtCore.Qt.MouseButton.LeftButton,buttons,modifiers)
  QtCore.QCoreApplication.sendEvent(self.source,click)
  self.pick_held=pressed
  if pressed:QtCore.QTimer.singleShot(20,self.capturePicking)
  else:
   self.last_input=0.0
   QtCore.QTimer.singleShot(20,update_hidden_arnold)
 def capturePicking(self):
  if not getattr(self,'pick_held',False):return
  saved=self.last_input;self.last_input=0.0
  try:update_hidden_arnold()
  finally:self.last_input=saved
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
   elif event.button()==QtCore.Qt.MouseButton.LeftButton:
    self.view.pick_press=event.position()
    self.view.pickMesh(event.position(),event.modifiers(),True)
   return True
  if typ==QtCore.QEvent.Type.MouseMove and self.last is None and getattr(self.view,'pick_press',None) is not None:
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
   if event.button()==QtCore.Qt.MouseButton.LeftButton and self.mode is None:
    press=getattr(self.view,'pick_press',None);self.view.pick_press=None
    if press is not None:
     self.view.pickMesh(event.position(),event.modifiers(),False)
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
 if not shiboken6.isValid(v.item):v.item=v.scene().items()[0]
 # Only viewer interactions suspend copying. Camera navigation in Maya stays live.
 if not v.isVisible() or time.monotonic()-v.last_input<0.08:return
 previous=QtGui.QOpenGLContext.currentContext();surface=previous.surface() if previous else None
 start=time.perf_counter()
 try:
  if time.monotonic()-v.resolution_checked>1:
   v.native_resolution=(int(cmds.getAttr('defaultResolution.width')),int(cmds.getAttr('defaultResolution.height')));v.resolution_checked=time.monotonic()
  width,height=v.native_resolution
  if width<=0 or height<=0:return
  if getattr(v,'fullres_resolution',None)!=(width,height):
   v.native_container.setFixedSize(width+128,height+128)
   v.source.resize(width+128,height+128)
   cmds.arnoldRenderView(option=('Frame All','1'))
   v.fullres_resolution=(width,height);v.fullres_stage='real'
   v.timer.setInterval(50);return
  if getattr(v,'fullres_stage',None)=='real':
   cmds.arnoldRenderView(option=('Real Size','1'))
   v.fullres_stage=None;return
  v.source.makeCurrent();v.source.paintEvent(QtGui.QPaintEvent(QtCore.QRect(0,0,v.source.width(),v.source.height())))
  image=v.source.grabFramebuffer()
  if not image.isNull():
   previous_image=getattr(v,'last_preview_image',None)
   full_unchanged=previous_image is not None and image==getattr(v,'last_full_frame',None)
   if full_unchanged:
    image=previous_image
   else:
    v.last_full_frame=image
    width,height=v.native_resolution
    if width<=image.width() and height<=image.height():
     image=image.copy((image.width()-width)//2,(image.height()-height)//2,width,height)
   previous_image=getattr(v,'last_preview_image',None)
   unchanged=previous_image is not None and image==previous_image
   v.stable_frames=getattr(v,'stable_frames',0)+1 if unchanged else 0
   if not unchanged:v.last_preview_image=image
   recent_input=time.monotonic()-getattr(v,'global_activity',0.0)<1.0
   v.timer.setInterval(250 if v.stable_frames>=20 and not recent_input else 50)
   size=(image.width(),image.height())
   if not unchanged:
    v.item.setPixmap(QtGui.QPixmap.fromImage(image))
    if v.crop_size!=size:v.scene().setSceneRect(v.item.boundingRect().adjusted(-100000,-100000,100000,100000))
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
v.setToolTip('Live IPR • Left click: pick • Middle or Alt-left drag: pan • Right drag or wheel: zoom • F: frame')

# Keep navigation responsive while backing off repeated identical previews.
class ArnoldAdaptiveActivity(QtCore.QObject):
 def eventFilter(self,obj,event):
  typ=event.type()
  if typ in (QtCore.QEvent.Type.MouseButtonPress,QtCore.QEvent.Type.Wheel,QtCore.QEvent.Type.KeyPress) or (typ==QtCore.QEvent.Type.MouseMove and event.buttons()!=QtCore.Qt.MouseButton.NoButton):
   v.global_activity=time.monotonic();v.stable_frames=0
   if v.timer.interval()!=50:v.timer.setInterval(50)
  return False
arnold_adaptive_activity=ArnoldAdaptiveActivity(v)
QtWidgets.QApplication.instance().installEventFilter(arnold_adaptive_activity)

# Keep the native container in its original QObject hierarchy, hidden and
# outside the visible splitter layout. Only the Qt image view is visible.
native_container=v.parentWidget()
native_splitter=native_container.parentWidget()
if not isinstance(native_splitter,QtWidgets.QSplitter):
 raise RuntimeError('Unsupported Arnold layout: expected a QSplitter')
native_index=native_splitter.indexOf(native_container)
native_container.removeEventFilter(arnold_canvas_size)
v.setParent(native_splitter,QtCore.Qt.WindowType.Widget)
native_splitter.insertWidget(native_index,v)
native_container.hide()
v.native_container=native_container
native_splitter.setStretchFactor(native_splitter.indexOf(v),1)
v.show();v.raise_()
