"""Optional Qt checks: run with Maya's mayapy and QT_QPA_PLATFORM=offscreen."""
import ast
from pathlib import Path
import time
import types
import unittest
from PySide6 import QtCore, QtGui, QtWidgets

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'maya/arnold_qt_canvas_impl.py').read_text())
NS={'QtCore':QtCore,'QtGui':QtGui,'QtWidgets':QtWidgets,'time':time,
    'shiboken6':__import__('shiboken6')}
CLASS=next(n for n in TREE.body if isinstance(n,ast.ClassDef) and n.name=='ArnoldQtViewerTest')
for name in ['wheelEvent','pickMesh','capturePicking']:
 node=next(n for n in CLASS.body if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<canvas checks>','exec'),NS)
node=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='update_hidden_arnold')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<canvas checks>','exec'),NS)
APP=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

class Timer:
 def setInterval(self,value):self.interval=value

class Frame(QtGui.QImage):
 copies=0
 def copy(self,*args):
  type(self).copies+=1
  return super().copy(*args)

class Source:
 def __init__(self,image):self.image=image
 def width(self):return self.image.width()
 def height(self):return self.image.height()
 def makeCurrent(self):pass
 def doneCurrent(self):pass
 def paintEvent(self,event):pass
 def grabFramebuffer(self):return self.image

class View(QtWidgets.QGraphicsView):
 wheelEvent=NS['wheelEvent']

class CanvasChecks(unittest.TestCase):
 def setUp(self):
  self.view=View();self.view.setScene(QtWidgets.QGraphicsScene(self.view))
  self.view.item=self.view.scene().addPixmap(QtGui.QPixmap())
  self.view.resize(1000,650);self.view.show();APP.processEvents()
 def tearDown(self):self.view.close()
 def test_pointer_zoom_after_native_anchor_disabled(self):
  v=self.view;v.scene().setSceneRect(-100000,-100000,200000,200000)
  for anchor_mode in [QtWidgets.QGraphicsView.ViewportAnchor.NoAnchor,QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse]:
   v.setTransformationAnchor(anchor_mode)
   for delta in [120,-120,0]:
    point=QtCore.QPoint(713,187);before=v.mapToScene(point)
    event=QtGui.QWheelEvent(QtCore.QPointF(point),QtCore.QPointF(point),QtCore.QPoint(),QtCore.QPoint(0,delta),QtCore.Qt.MouseButton.NoButton,QtCore.Qt.KeyboardModifier.NoModifier,QtCore.Qt.ScrollPhase.NoScrollPhase,False)
    v.wheelEvent(event);after=v.mapFromScene(before)
    self.assertLessEqual(abs(after.x()-point.x()),1)
    self.assertLessEqual(abs(after.y()-point.y()),1)
 def test_full_resolution_pixels_and_identical_frame_reuse(self):
  v=self.view;width,height=2500,1406
  frame=Frame(width+128,height+128,QtGui.QImage.Format.Format_RGBA8888)
  frame.fill(QtGui.QColor(15,25,35,255))
  frame.setPixelColor(64,64,QtGui.QColor(200,30,50,150))
  frame.setPixelColor(64+width-1,64+height-1,QtGui.QColor(20,220,70,255))
  v.source=Source(frame);v.timer=Timer();v.native_resolution=(width,height)
  v.fullres_resolution=(width,height);v.fullres_stage=None;v.resolution_checked=time.monotonic()
  v.last_input=0;v.crop_first=True;v.crop_size=None;v.live_updates=0
  NS['v']=v;Frame.copies=0
  NS['update_hidden_arnold']()
  expected=QtGui.QImage.copy(frame,64,64,width,height)
  self.assertEqual(v.last_preview_image,expected)
  self.assertEqual((v.last_preview_image.width(),v.last_preview_image.height()),(width,height))
  self.assertEqual(Frame.copies,1)
  NS['update_hidden_arnold']()
  self.assertEqual(Frame.copies,1,'Identical frame should not be cropped again')
  changed=Frame(frame);changed.setPixelColor(65,65,QtGui.QColor(255,255,0,255))
  v.source.image=changed;NS['update_hidden_arnold']()
  self.assertEqual(Frame.copies,2)
  self.assertEqual(v.last_preview_image.pixelColor(1,1),QtGui.QColor(255,255,0,255))
  self.assertEqual(v.last_preview_image.pixelColor(0,0),QtGui.QColor(200,30,50,150))

if __name__=='__main__':unittest.main()
