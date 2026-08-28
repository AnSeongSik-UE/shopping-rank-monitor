import sys, sqlite3
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication, QTableWidgetItem
from PyQt5 import uic,QtCore, QtGui, QtWidgets, uic
from datetime import datetime

list_ui = uic.loadUiType("./ui/list.ui")[0]

class listDialog(QDialog, list_ui):
    resized = QtCore.pyqtSignal()
    global conn
    conn = sqlite3.connect('shop.db')

    def __init__(self, company):
        super().__init__()
        self.company = company
        self.setupUi(self)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        #DB연결 확인
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telegram_list")
        except:
            QMessageBox().warning(self, '오류', 'DB 파일을 찾을수 없습니다.')
            sys.exit(0)

        self.btn_save.clicked.connect(self.clickSave)
        self.btn_cancel.clicked.connect(self.clickCancel)
        self.resized.connect(self.resizeWidget) # 창 크기따라 사이즈변경
        self.lbl_company.setText("업체명 : " + company)
        self.showData()        

        # AlignDelegate 가운데 정렬 Class 나중에 분리 하기
        delegate = AlignDelegate(self.list_tableWidget)
        self.list_tableWidget.setItemDelegateForColumn(0, delegate)

        # 폰트크기
        self.lbl_company.setFont(QtGui.QFont("Gulim", 9)) # 상품명        

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def resizeWidget(self):
        tw = self.width()-50
        th = self.height()-100
        self.list_tableWidget.resize(tw, th)
    
    def clickSave(self):
        reply = QMessageBox.question(self, '알림', "저장하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:

            #기존 테이블에 있는거는 삭제
            cursor = conn.cursor()
            sql = "DELETE FROM telegram_list WHERE tl_company = '" + self.company + "'"
            cursor.execute(sql)
            conn.commit()

            #현재 목록 읽어서 모두 INSERT
            count = self.list_tableWidget.rowCount()
            for i in range(count):
                id = self.list_tableWidget.item(i, 0).text()
                sql  = "INSERT INTO telegram_list (tl_company, tl_telegram_id, tl_date) VALUES (?,?,?)"
                param = (self.company, id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                cursor.execute(sql, param)
                conn.commit()
            self.close()
    
    def clickCancel(self):
        self.close()

    # 데이터 불러오기
    def showData(self):
        cursor = conn.cursor()
        sql = "SELECT * FROM telegram_list WHERE tl_company = '" + self.company + "' ORDER BY tl_date DESC"
        cursor.execute(sql)
        conn.commit()
        tables_data = cursor.fetchall()
        
        row_count = len(tables_data) #row 행
        self.list_tableWidget.setRowCount(row_count)
 
        count=0
        for i in tables_data:
            self.list_tableWidget.setItem(count, 0, QTableWidgetItem(str(i[2])))
            self.list_tableWidget.resizeColumnToContents(count) ## 컬럼 넓이 자동정렬
            self.list_tableWidget.setColumnWidth(0, self.list_tableWidget.columnWidth(1)/4) ## 컬럼FIX
            count=count+1

#############################################
class AlignDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

if __name__ == "__main__":
    app = QApplication(sys.argv)
    listWindow = listDialog()
    listWindow.show()
    app.exec_()