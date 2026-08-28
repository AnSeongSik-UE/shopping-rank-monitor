import sys, time, sqlite3
from PyQt5.QtCore import pyqtSignal, QThread, QDateTime
from PyQt5.QtWidgets import QDialog, QApplication, QStyledItemDelegate, QTableWidgetItem, QMessageBox
from PyQt5 import uic, QtGui, QtCore
from datetime import datetime
import main

notice_ui = uic.loadUiType("./ui/notice.ui")[0]

class NoticeDialog(QDialog, notice_ui):
    
    def __init__(self, filterd_id, bot):
        mainClass = main.MainWindow()
        self.bot = bot
        self.filterd_id = filterd_id
        self.text = ''
        self.date = ''


        super().__init__()

        self.setupUi(self)

        self.showData()
        self.shop_sendBtn.clicked.connect(self.sendNotice)
        self.shop_resBtn.clicked.connect(self.reservation)
        self.shop_notiDelBtn.clicked.connect(self.noticeDel)

        self.noticeThread = NoticeThread(self)
        self.noticeThread.change_sendBtn.connect(self.shop_sendBtn.setText)
        self.noticeThread.change_statusText.connect(self.shop_statusText.setText)

        # 선택된 열 확인 (미선택, 초기화시 -1)
        self.selectedIdx = -1
        self.selectedRow = -1
        self.shop_notiTable.itemClicked.connect(self.noticeTableclick)

        # AlignDelegate 가운데 정렬
        delegate = AlignDelegate(self.shop_notiTable)
        self.shop_notiTable.setItemDelegateForColumn(2, delegate)

        # 폰트크기
        self.shop_sendBtn.setFont(QtGui.QFont("Gulim", mainClass.fontSize))
        self.shop_resBtn.setFont(QtGui.QFont("Gulim", mainClass.fontSize))
        self.shop_notiDelBtn.setFont(QtGui.QFont("Gulim", mainClass.fontSize))
        self.shop_date.setFont(QtGui.QFont("Gulim", mainClass.fontSize))
        self.shop_statusText.setFont(QtGui.QFont("Gulim", mainClass.fontSize))

        # 현재시간
        self.shop_date.setDateTime(QDateTime.currentDateTime())
        

        # 창 물음표 제거
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
    
    # 데이터 불러오기
    def showData(self):
        global row_count
        global tables_data
        
        tables_data = selectDB('*', 'notice')
        row_count = len(tables_data) #row 행
        self.shop_notiTable.setRowCount(row_count)

        count=0
        for i in tables_data:
            # 10개 까지만 보여주기
            if count < 10:
                #0 noti_idx     -> 3 idx
                #1 noti_date    -> 0 전송일자
                #2 noti_text    -> 1 내용
                #3 noti_check   -> 2 전송상태 (대기중, 전송완료)
                
                item_name = QTableWidgetItem(str(i[0]))
                self.shop_notiTable.setItem(count,3,item_name)  
                item_name = QTableWidgetItem(i[1])
                self.shop_notiTable.setItem(count,0,item_name)
                item_name = QTableWidgetItem(i[2])
                self.shop_notiTable.setItem(count,1,item_name)
                item_name = QTableWidgetItem(i[3])
                self.shop_notiTable.setItem(count,2,item_name)
                
                # idx 숨기기
                self.shop_notiTable.hideColumn(3)
        
                self.shop_notiTable.resizeColumnToContents(count) ## 컬럼 넓이 자동정렬
                count=count+1

    # 선택열 확인
    def noticeTableclick(self):
        noti_cell = self.shop_notiTable.selectedIndexes()
        self.selectedRow = noti_cell[0].row()
        self.selectedIdx = int(self.shop_notiTable.item(self.selectedRow, 3).text())
        self.shop_inputNotice.setText(self.shop_notiTable.item(self.selectedRow, 1).text())
        

    # 삭제
    def noticeDel(self):
        print('삭제')

        # 클릭된 항목 삭제
        if self.selectedIdx != -1:
            buttonReply = QMessageBox.warning(self, '경고', '선택된 항목을 삭제하시겠습니까?', QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                deleteDB(self.selectedIdx)
            elif buttonReply == QMessageBox.No:
                QMessageBox.warning(self,'확인', '삭제가 취소되었습니다.')
        # 삭제할 항목 없음
        else:
            QMessageBox.warning(self,'경고','선택된 항목이 없습니다.')

        self.selectedIdx = -1
        self.showData()

    # 예약
    def reservation(self):
        print('예약')
        if self.isInserted():
            insertDB(self.date ,self.text ,'대기중')
            self.showData()
            self.shop_statusText.setText('예약완료')

    # 전송
    def sendNotice(self):
        print('send')
        if self.isInserted():
            self.shop_resBtn.setDisabled(True)
            self.shop_notiDelBtn.setDisabled(True)
            self.shop_sendBtn.setDisabled(True)
            self.noticeThread.start()
            insertDB('', self.text, '전송완료')
            time.sleep(1)
            self.showData()

    # 입력값 확인
    def isInserted(self):
        if self.shop_inputNotice.toPlainText() == '':
            QMessageBox.warning(self,'확인', '공지사항이 입력되지 않았습니다.')
            result = False
        else:
            self.text = self.shop_inputNotice.toPlainText()
            self.date = self.shop_date.text()
            result = True

        return result


class NoticeThread(QThread):
    change_sendBtn = pyqtSignal(str)
    change_statusText = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.power = True

    def run(self):

        notice = self.parent().shop_inputNotice.toPlainText()
        notice = '[공지사항]\n' + notice
        self.change_sendBtn.emit('전송중')
        filterd_id = self.parent().filterd_id
        cnt = 1

        for id in filterd_id:
            if self.power == False: #쓰레드 정지되어있으면 False 
                break
            time.sleep(0.5)
            print(id)
            try:
                self.parent().bot.sendMessage(id, notice, 'HTML')
            except:
                print('[오류] 텔레그램 전송 오류. 주소를 찾을수 없습니다.')
            self.change_statusText.emit(str(cnt) + '/' + str(len(filterd_id)) + ' 전송')
            cnt = cnt + 1

        self.change_statusText.emit('전송 완료')
        self.change_sendBtn.emit('전송')
        self.parent().shop_resBtn.setEnabled(True)
        self.parent().shop_notiDelBtn.setEnabled(True)
        self.parent().shop_sendBtn.setEnabled(True)

    def stop(self):
        self.power = False
        self.quit()
        self.wait(3000)  # 3초 대기 (바로 안꺼질수도)

#############################################
## 쿼리 s
def selectDB(col ,table):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    sql = "SELECT "+ col +" FROM " + table + " ORDER BY noti_date DESC"
    cursor.execute(sql)
    conn.commit()
    db_list = cursor.fetchall()
    # conn.close()
    return db_list

def insertDB(date, text, check):

    if date == '':
        date = datetime.now().strftime('%Y-%m-%d %H:%M')

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    sql  = "INSERT INTO notice (noti_date, noti_text, noti_check) VALUES (?,?,?)"
    param = (date, text, check)
    cursor.execute(sql, param)
    conn.commit()
    return True

# def updateDB(idx, product, keyword, mid, company, rank, memo):
#     conn = sqlite3.connect('shop.db')
#     cursor = conn.cursor()

#     sql  = "UPDATE product SET pd_name = ?, pd_keyword = ?, pd_mid = ?, pd_company = ?, pd_rank = ?, pd_memo = ?, pd_date = ? WHERE idx = ?"
#     param = (product, keyword, mid, company, rank, memo, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx)
#     cursor.execute(sql, param)
#     conn.commit()
#     return True

def deleteDB(idx):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    sql  = "DELETE FROM notice WHERE noti_idx = ?"
    param = (idx,)
    cursor.execute(sql, param)
    conn.commit()
    # conn.close()
## 쿼리 e

class AlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

if __name__ == "__main__":
    app = QApplication(sys.argv)
    noticeDialog = NoticeDialog()
    noticeDialog.show()
    app.exec_()
