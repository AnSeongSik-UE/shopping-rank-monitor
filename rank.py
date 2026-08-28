import sys, sqlite3
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication, QTableWidgetItem
from PyQt5 import uic,QtCore, QtGui, QtWidgets, uic
from selenium.webdriver.common.by import *

rank_ui = uic.loadUiType("./ui/rank.ui")[0]

class rankDialog(QDialog, rank_ui):
    resized = QtCore.pyqtSignal()
    global conn
    conn = sqlite3.connect('shop.db')

    def __init__(self, product, idx):

        super().__init__()

        self.idx = idx

        self.setupUi(self)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        #DB연결 확인
        try:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history")
        except:
            QMessageBox().warning(self, '오류', 'DB 파일을 찾을수 없습니다.')
            sys.exit(0)

        self.resized.connect(self.resizeWidget) # 창 크기따라 사이즈변경
        self.rank_product.setText(product)
        self.showData()
        

        # AlignDelegate 가운데 정렬 Class 나중에 분리 하기
        delegate = AlignDelegate(self.rank_tableWidget)
        self.rank_tableWidget.setItemDelegateForColumn(0, delegate)
        self.rank_tableWidget.setItemDelegateForColumn(1, delegate)

        # 폰트크기
        self.rank_product.setFont(QtGui.QFont("Gulim", 9)) # 상품명
        

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def resizeWidget(self):
        tw = self.width()-50
        th = self.height()-100
        self.rank_tableWidget.resize(tw, th)

    # 데이터 불러오기
    def showData(self):
        global row_count
        global tables_data
        
        tables_data = selectDB('history', self.idx)
        row_count = len(tables_data) #row 행
        self.rank_tableWidget.setRowCount(row_count)
 
        count=0
        for i in tables_data:
            #2 hs_rank
            #3 hs_date
            
            item_name = QTableWidgetItem(str(i[2]))
            self.rank_tableWidget.setItem(count,0,item_name)
            item_name = QTableWidgetItem(str(i[3]))
            self.rank_tableWidget.setItem(count,1,item_name)
    
            self.rank_tableWidget.resizeColumnToContents(count) ## 컬럼 넓이 자동정렬  
            self.rank_tableWidget.setColumnWidth(0,self.rank_tableWidget.columnWidth(1)/4) ## 컬럼FIX            
            count=count+1

#############################################
## 쿼리 s
def selectDB(table, idx):
    cursor = conn.cursor()
    sql = "SELECT * FROM " + table + " WHERE pd_id = ? ORDER BY hs_date DESC"
    param = (idx,)
    cursor.execute(sql, param)
    conn.commit()
    db_list = cursor.fetchall()
    # conn.close()
    
    return db_list
## 쿼리 e

class AlignDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

if __name__ == "__main__":

    app = QApplication(sys.argv)
    rankWindow = rankDialog()
    rankWindow.show()
    app.exec_()