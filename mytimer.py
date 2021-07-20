from PyQt5.QtCore import QTimer

class mytimer(QTimer):
    def __init__(self,args):
        super().__init__()
        self.args = args
    def set_args(self,args):
        self.args = args