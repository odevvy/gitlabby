# In-memory HTTPS image replies for offline source-policy and image-render tests.
import base64
from PySide6.QtCore import QIODevice, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtQml import QQmlNetworkAccessManagerFactory
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGO0zlvBAANMDEgANwcAQmkBWeHkvAIAAAAASUVORK5CYII=')
requests=[]
# Strong references: Qt owns these objects on its image-reader thread, and a
# collected Python wrapper would leave Qt calling a dead readData override.
keep=[]
class Reply(QNetworkReply):
    def __init__(self, request, parent):
        super().__init__(parent); self.payload=PNG; self.offset=0
        self.setRequest(request);self.setUrl(request.url());self.setOperation(QNetworkAccessManager.GetOperation)
        self.setHeader(QNetworkRequest.ContentTypeHeader,"image/png");self.setHeader(QNetworkRequest.ContentLengthHeader,len(PNG))
        self.open(QIODevice.ReadOnly);QTimer.singleShot(0,self.complete)
    def complete(self):
        self.setFinished(True);self.readyRead.emit();self.finished.emit()
    def readData(self,n):
        out=self.payload[self.offset:self.offset+n];self.offset+=len(out);return out
    def bytesAvailable(self):return len(self.payload)-self.offset+super().bytesAvailable()
    def isSequential(self):return True
    def abort(self):pass
class Manager(QNetworkAccessManager):
    def createRequest(self, operation, request, outgoing=None):
        requests.append(request.url().toString());r=Reply(request,self);keep.append(r);return r
class Factory(QQmlNetworkAccessManagerFactory):
    def create(self,parent):m=Manager(parent);keep.append(m);return m
factory=Factory()
def install(lib):
    original=lib.QQmlApplicationEngine
    class Engine(original):
        def __init__(self):
            super().__init__();self.setNetworkAccessManagerFactory(factory)
    lib.QQmlApplicationEngine=Engine
