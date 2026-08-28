import sys, time, sqlite3, os
from PyQt5.QtWidgets import QStyledItemDelegate, QFileDialog, QPushButton, QMessageBox, QMainWindow, QApplication, QHBoxLayout, QWidget, QCheckBox, QTableWidgetItem
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtCore import Qt
from datetime import datetime
import telegram
from telegram.ext import Updater, MessageHandler, Filters
import rank
import list
import threading
import requests
from urllib import parse
import pandas as pd
import notice
from apscheduler.schedulers.background import BackgroundScheduler

main_ui = uic.loadUiType("./ui/main.ui")[0]
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

class MainWindow(QMainWindow, main_ui):
    resized = QtCore.pyqtSignal()
    global conn
    conn = sqlite3.connect('shop.db')
    fontSize = 9

    def __init__(self):
        super().__init__()

        fontSize = self.fontSize

        self.setupUi(self)
        self.shop_tableWidget.hideColumn(12)
        
        self.resized.connect(self.resizeWidget) # 창 크기따라 사이즈변경
        self.showData()
        self.shop_insertBtn.clicked.connect(self.insert)
        self.shop_refreshBtn.clicked.connect(self.refresh)        
        self.shop_checkBtn.clicked.connect(self.reloadTable)
        self.shop_deleteBtn.clicked.connect(self.delete)
        self.shop_excelBtn.clicked.connect(self.excel)
        self.shop_noticeBtn.clicked.connect(self.notice)
        self.shop_loadTableBtn.clicked.connect(self.executeCrawler_Thread)
        self.shop_loadstop.clicked.connect(self.executeCrawler_stop)
        self.shop_receiveChkBtn.stateChanged.connect(self.changeReceiveChk)

        # 선택된 열 확인 (미선택, 초기화시 -1)
        self.selectedRow = -1
        self.selectedIdx = -1
        self.selectedRank = -1
        self.shop_tableWidget.itemClicked.connect(self.tableOnclick)

        #DB연결 확인
        try:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM product")
        except:
            QMessageBox().warning(self, '오류', 'DB 파일을 찾을수 없습니다.')
            sys.exit(0)

        # AlignDelegate 가운데 정렬 Class 나중에 분리 하기
        delegate = AlignDelegate(self.shop_tableWidget)
        self.shop_tableWidget.setItemDelegateForColumn(1, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(2, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(3, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(4, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(5, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(6, delegate)
        self.shop_tableWidget.setItemDelegateForColumn(7, delegate)        

        #체크박스 전체체크
        self.shop_checkAll.stateChanged.connect(self.ckbox_sw)

        # 폰트크기
        self.shop_lb1.setFont(QtGui.QFont("Gulim", fontSize)) # 상품명
        self.shop_lb2.setFont(QtGui.QFont("Gulim", fontSize)) # 키워드
        self.shop_lb3.setFont(QtGui.QFont("Gulim", fontSize)) # Mid
        self.shop_lb4.setFont(QtGui.QFont("Gulim", fontSize)) # 업체명
        self.shop_lb6.setFont(QtGui.QFont("Gulim", fontSize)) # 메모
        self.shop_lb7.setFont(QtGui.QFont("Gulim", fontSize)) # 주기(시간)
        self.shop_checkHour.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_insertBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_refreshBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_noticeBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_loadTableBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_loadstop.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_deleteBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_excelBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_checkBtn.setFont(QtGui.QFont("Gulim", fontSize))
        self.shop_checkAll.setFont(QtGui.QFont("Gulim", fontSize))

        

    def notice(self):
        # 중복id 추리기
        db_telegram = selectDB('tl_telegram_id', 'telegram_list')
        filterd_id = []
        for i in db_telegram:
            value = i[0]
            if value not in filterd_id:
                filterd_id.append(value)
        
        print(filterd_id)
        self.noticeDialog = notice.NoticeDialog(filterd_id, bot)
        self.noticeDialog.show()

    # 엑셀 DB에 입력
    def excel(self):
        FileOpen = QFileDialog.getOpenFileName(self, 'Open file', '', 'xlsx File(*.xlsx)') # 파일
        if FileOpen[0] != '' : # 파일 선택취소 시 예외처리
            excelData = pd.read_excel(FileOpen[0])
            try: 
                data_np = pd.DataFrame.to_numpy(excelData)
                compCnt = 0
                failCnt = 0
                for i in range(0,excelData.shape[0]):
                    product  = str(data_np[i][0])   # 상품명
                    keyword   = str(data_np[i][1])  # 키워드
                    mid  = str(data_np[i][2])       # mid
                    company = str(data_np[i][3])    # 업체명
                    rank = -1
                    memo = str(data_np[i][4])       # 메모
                    
                    # mid keyword 체크
                    if mid != 'nan' and keyword != 'nan':
                        insertDB(product, keyword, mid, company, rank, memo)
                        compCnt = compCnt + 1
                    else:
                        failCnt = failCnt + 1
                    # print(product, keyword, mid, company, memo)
                    
                self.reloadTable()
                if failCnt == 0:
                    QMessageBox().information(self, '확인', "엑셀 업데이트 완료\n순위 갱신을 위해 시작버튼을 클릭해주세요.")
                else:
                    QMessageBox().information(self, '확인', "엑셀 업데이트 완료\n성공 : " + str(compCnt) + "\n실패 : " + str(failCnt) + "\n순위 갱신을 위해 시작버튼을 클릭해주세요.")
                
            except NameError : # 참조할 변수가 없을경우 예외처리
                QMessageBox().warning(self, '경고', "오류가 발생하였습니다.")
        else :
            print('파일선택취소')
            # QMessageBox().warning(self, '경고', "파일을 확인해주세요.")

    # 셀 클릭시 해당 열 데이터 가져오기
    def tableOnclick(self):
        cell = self.shop_tableWidget.selectedIndexes()
        self.selectedRow = cell[0].row()
        self.selectedIdx = int(self.shop_tableWidget.item(self.selectedRow, 1).text())
        txt = self.shop_tableWidget.item(self.selectedRow, 2).text()
        self.shop_product.setText(txt)
        txt = self.shop_tableWidget.item(self.selectedRow, 3).text()
        self.shop_keyword.setText(txt)
        txt = self.shop_tableWidget.item(self.selectedRow, 4).text()
        self.shop_mid.setText(txt)
        txt = self.shop_tableWidget.item(self.selectedRow, 5).text()
        self.shop_company.setText(txt)
        self.selectedRank = int(self.shop_tableWidget.item(self.selectedRow, 6).text())
        txt = self.shop_tableWidget.item(self.selectedRow, 9).text()
        self.shop_memo.setText(txt)
        # self.checkBoxList[self.selectedRow].setChecked(True)

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def resizeWidget(self):
        tw = self.width()-40
        th = self.height()-130
        self.shop_tableWidget.resize(tw, th)

    # 체크박스 전체선택   
    def ckbox_sw(self) :
        count = self.shop_tableWidget.rowCount()
        if self.shop_checkAll.isChecked() :
            for i in range(count):
                self.checkBoxList[i].setChecked(True)
        else :
            for i in range(count):
                self.checkBoxList[i].setChecked(False)
    
    # 변경사항 적용 후 테이블 다시 불러오기
    def reloadTable(self):
        self.shop_tableWidget.setRowCount(0)
        self.showData()

    # 삭제 버튼
    def delete(self):
        count = self.shop_tableWidget.rowCount()
        checkedIdx = [-1] * count
        isChecked = False
        delCnt = 0

        # 체크된 항목 idx 추출
        for i in range(count):
            if self.checkBoxList[i].isChecked():
                checkedIdx[i] = int(self.shop_tableWidget.item(i, 1).text())
                isChecked = True
                delCnt = delCnt + 1
        
        # 체크된 항목 삭제
        if isChecked:
            buttonReply = QMessageBox.warning(self,
                                                    '경고',
                                                    "선택된 항목을 삭제하시겠습니까?", 
                                                    QMessageBox.Yes, 
                                                    QMessageBox.No
                                                    )
            if buttonReply == QMessageBox.Yes:
                for i in range(count):
                    if checkedIdx[i] != -1:
                        deleteDB(checkedIdx[i])
                QMessageBox.warning(self,'확인', str(delCnt) + '개의 항목이 삭제되었습니다.')
            elif buttonReply == QMessageBox.No:
                QMessageBox.warning(self,'확인', '삭제가 취소되었습니다.')
        # 클릭된 항목 삭제
        elif self.selectedIdx != -1:
            buttonReply = QMessageBox.warning(self,
                                                    '경고',
                                                    "선택된 항목을 삭제하시겠습니까?", 
                                                    QMessageBox.Yes, 
                                                    QMessageBox.No
                                                    )
            if buttonReply == QMessageBox.Yes:
                deleteDB(self.selectedIdx)
                QMessageBox.warning(self,'확인', '선택된 항목이 삭제되었습니다.')
            elif buttonReply == QMessageBox.No:
                QMessageBox.warning(self,'확인', '삭제가 취소되었습니다.')
        # 삭제할 항목 없음
        else:
            QMessageBox.warning(self,'경고','선택된 항목이 없습니다.')
        
        self.reloadTable()

    # 초기화 버튼
    def refresh(self):
        self.selectedRow = -1
        self.selectedIdx = -1
        self.selectedRank = -1
        txt = ''
        self.shop_product.setText(txt)
        self.shop_keyword.setText(txt)
        self.shop_mid.setText(txt)
        self.shop_company.setText(txt)
        self.shop_memo.setText(txt)

    # 입력 버튼
    def insert(self):
        idx = int(self.selectedIdx)
        product = self.shop_product.text()
        keyword = self.shop_keyword.text()
        mid = self.shop_mid.text()
        company = self.shop_company.text()
        memo = self.shop_memo.text()

        if idx == -1:
            if mid != '' and keyword != '':
                rank = int(self.selectedRank) # 순위 크롤링
                buttonReply = QMessageBox.warning(self, '확인', '데이터를 입력하시겠습니까?', QMessageBox.Yes, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    result = insertDB(product, keyword, mid, company, rank, memo)
                    if result == False:
                        QMessageBox.warning(self, '실패', '중복된 데이터가 있습니다.')
                elif buttonReply == QMessageBox.No:
                    QMessageBox.warning(self,'확인', '데이터 입력이 취소되었습니다.')
            else:
                QMessageBox.warning(self,'경고', '주요 데이터가 입력되지 않았습니다.')
        else:
            rank = int(self.selectedRank)
            buttonReply = QMessageBox.warning(self, '경고', '데이터를 업데이트 하시겠습니까?', QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                result = updateDB(idx, product, keyword, mid, company, rank, memo)
                if result == False:
                    QMessageBox.warning(self, '실패', '중복된 데이터가 있습니다.')
            elif buttonReply == QMessageBox.No:
                QMessageBox.warning(self,'확인', '데이터가 업데이트 취소 되었습니다.')

        self.reloadTable()

    #텔레그램 목록 확인
    def showTelegramList(self):
        button = self.sender()
        item = self.shop_tableWidget.indexAt(button.pos())
        company = self.shop_tableWidget.item(item.row(), 5).text()
        self.listDialog = list.listDialog(company)
        self.listDialog.show()

    # 순위 확인
    def seeRank(self):
        button = self.sender()
        item = self.shop_tableWidget.indexAt(button.pos())
        idx = self.shop_tableWidget.item(item.row(), 1).text()
        product = self.shop_tableWidget.item(item.row(), 2).text()
        self.rankDialog = rank.rankDialog(product, idx)
        self.rankDialog.show()

    # 데이터 불러오기
    def showData(self):
        global row_count
        global tables_data
        
        tables_data = selectDB('*', 'product')
        row_count = len(tables_data) #row 행
        self.shop_tableWidget.setRowCount(row_count)

        # 체크 박스 생성
        self.checkBoxList = []        
        for i in range(row_count):
            ckbox = QCheckBox()
            cellWidget = QWidget()
            self.checkBoxList.append(ckbox)  
            layoutCB = QHBoxLayout(cellWidget)
            layoutCB.addWidget(self.checkBoxList[i])
            layoutCB.setAlignment(QtCore.Qt.AlignCenter)            
            layoutCB.setContentsMargins(0,0,0,0)
            cellWidget.setLayout(layoutCB)     
            self.shop_tableWidget.setCellWidget(i,0,cellWidget)
 
        count=0
        for i in tables_data:
            #0 체크박스
            #1 No               idx
            #2 상품명           pd_name
            #3 키워드           pd_keyword
            #4 Mid              pd_mid
            #5 업체명           pd_company
            #6 현재 순위        pd_rank
            #7 순위변동상항
            #8 텔레그램 주소    pd_telegram_url
            #9 메모             pd_memo
            
            item_name = QTableWidgetItem(str(i[0]))
            self.shop_tableWidget.setItem(count,1,item_name)  
            item_name = QTableWidgetItem(i[1])
            self.shop_tableWidget.setItem(count,2,item_name)
            item_name = QTableWidgetItem(i[2])
            self.shop_tableWidget.setItem(count,3,item_name)
            item_name = QTableWidgetItem(i[3])
            self.shop_tableWidget.setItem(count,4,item_name)
            item_name = QTableWidgetItem(i[4])
            self.shop_tableWidget.setItem(count,5,item_name)
            item_name = QTableWidgetItem(str(i[5]))
            self.shop_tableWidget.setItem(count,6,item_name)
            
            self.rankBtn = QPushButton("확인하기")
            self.rankBtn.clicked.connect(self.seeRank)
            self.shop_tableWidget.setCellWidget(count, 7, self.rankBtn)

            self.btn_telegram_list = QPushButton("확인하기")
            self.btn_telegram_list.clicked.connect(self.showTelegramList)
            self.shop_tableWidget.setCellWidget(count, 8, self.btn_telegram_list)

            item_name = QTableWidgetItem(i[7])
            self.shop_tableWidget.setItem(count, 9, item_name)
    
            self.shop_tableWidget.resizeColumnToContents(count) ## 컬럼 넓이 자동정렬
            # self.shop_tableWidget.setColumnWidth(3,self.shop_tableWidget.columnWidth(1)) ## 컬럼FIX
            count=count+1
    ## 크롤링 2
    def executeCrawler(self):
        try:
            while(True):
                conn = sqlite3.connect('shop.db')
                cursor = conn.cursor()
                sql = "SELECT * FROM product"
                cursor.execute(sql)
                rows = cursor.fetchall()     

                for row in rows:
                    idx = row[0]
                    pd_name = row[1]
                    pd_keyword = row[2]
                    pd_mid = row[3]
                    pd_company = row[4]
                    pd_rank = row[5]
                    pd_telegram = row[6]
                    pd_memo = row[7]
                    pd_date = row[8]
                    pd_keyword_ps= parse.quote(pd_keyword)

                    print("제품명:"+pd_name)
                    self.statusBar.showMessage(pd_mid)

                    for_stop = True #이중포문 빠져나가는 변수
                    for i in range(1, 10) :                        
                        if (for_stop == False) : 
                            break                        
                        #print(i)                
                        url = "https://search.shopping.naver.com/api/search/all?sort=rel&pagingIndex="+str(i)+"&pagingSize=40&viewType=list&productSet=total&deliveryFee=&deliveryTypeValue=&frm=NVSHATC&query="+pd_keyword_ps+"&origQuery="+pd_keyword_ps+"&iq=&eq=&xq="
                        headers = {'Referer': "https://search.shopping.naver.com/search/all?frm=NVSHATC&origQuery="+pd_keyword_ps+"&pagingIndex="+str(i)+"&pagingSize=40&productSet=total&query="+pd_keyword_ps+"&sort=rel&timestamp=&viewType=list",
                            'user-agent' :'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'} 
                        timeout = 5
                        res  = requests.get(url, headers=headers, timeout=timeout)
                        output = res.json()

                        if output['shoppingResult']['productCount'] == 0: #검색되는 상품이 하나라도 있어야지만 진행
                            break
                        
                        for x in range(0, len(output['shoppingResult']['products'])) :
                            self.statusBar.showMessage(str(pd_mid) + ' ' + str(i) + '페이지 크롤링중')

                            if (output['shoppingResult']['products'][x]['crUrl'].find(pd_mid) != -1 ):
                                #2022.12.21 계속 히스토리 남기기
                                self.Rank_Insert(idx, output['shoppingResult']['products'][x]['rank'])
                                print(output['shoppingResult']['products'][x]['productName']) #제품명
                                print(output['shoppingResult']['products'][x]['rank'])   # 랭킹       
                                output['shoppingResult']['products'][x]['productTitle'] #타이틀                         
                                if (output['shoppingResult']['products'][x]['rank'] != pd_rank):
                                    #self.Rank_Insert(idx, output['shoppingResult']['products'][x]['rank'])
                                    self.Rank_Update(idx, output['shoppingResult']['products'][x]['rank'], output['shoppingResult']['products'][x]['productTitle'])
                                    self.updateTableRank(str(idx), str(output['shoppingResult']['products'][x]['rank']),output['shoppingResult']['products'][x]['productTitle'])                                     

                                    #업체명이 안비어있으면 텔레그램 목록 찾아서 메시지 전송
                                    if pd_company != '':
                                        sql = "SELECT * FROM telegram_list WHERE tl_company = '" + pd_company + "' ORDER BY idx"
                                        cursor.execute(sql)
                                        conn.commit()
                                        rows = cursor.fetchall()
                                        for row in rows:
                                            if row[2] != '':
                                                message = '[안내] 순위가 변경되었습니다.\n키워드 : ' + pd_keyword + '\n상품명 : ' + pd_name + '\nMid : ' + pd_mid + '\n순위 : ' + str(pd_rank) + '위 -> ' + str(output['shoppingResult']['products'][x]['rank']) + '위'
                                                sendMessage(message, row[2])
                                for_stop = False
                                break

                        time.sleep(3)    
                                            
                if (self.label.text() == '크롤링중지'):
                    print("무한루프 중지")
                    break                                     
                
                # 주기
                checkHour = int(self.shop_checkHour.text())*3600
                self.statusBar.showMessage(self.shop_checkHour.text() + '시간 휴식')
                print(self.shop_checkHour.text() + '시간 휴식')
                time.sleep(checkHour)
                
        except requests.JSONDecodeError:
            self.statusBar.showMessage('[오류] 네이버 크롤링 연결 제한 발생. 잠시후에 다시 시도해주세요.')
            self.executeCrawler_stop()
    
    #table에 있는 rank 값 업데이트
    def updateTableRank(self, idx, rank,title):
        #쿼리결과의 idx값을 table에서 찾아서 해당 row를 찾고 해당 row의 rank 값을 업데이트함
        for r in range(self.shop_tableWidget.rowCount()):
            row_no = self.shop_tableWidget.item(r, 1).text()
            if idx == row_no:
                self.shop_tableWidget.item(r, 6).setText(rank)
                self.shop_tableWidget.item(r, 2).setText(title)
                self.shop_tableWidget.setCurrentItem(self.shop_tableWidget.item(r, 6))
                self.shop_tableWidget.setCurrentItem(self.shop_tableWidget.item(r, 2))
                break

    ## 랭킹 히스토리 추가
    def Rank_Insert(self,A_id,A_rank):
        #RANK HISTORY INSERT
        #크롤러가 동작할때마다 변경된 순위에 대한 정보를 테이블에 삽입함 
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        sql  = "INSERT INTO history (pd_id, hs_rank, hs_date) VALUES (?,?,?)"
        param = (A_id, A_rank, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        cursor.execute(sql, param)
        conn.commit()
        conn.close()  

    #크롤러가 동작할때마다 변경된 순위에 업데이트
    def Rank_Update(self,B_id,B_rank,B_pd_name):
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        sql  = "UPDATE product SET pd_rank = ? , pd_name = ? WHERE idx = ?"
        param = (B_rank, B_pd_name, B_id)
        cursor.execute(sql, param)
        conn.commit()
        conn.close()

    def executeCrawler_Thread(self):
        global t1
        self.shop_checkHour.setDisabled(True)
        self.label.setText("크롤링시작")  
        self.shop_loadstop.setEnabled(True)
        self.shop_loadTableBtn.setEnabled(False)
        # debugpy.debug_this_thread() #쓰레드돌리는중에도 디버깅할수있게 추가
        t1 = threading.Thread(target = self.executeCrawler, daemon = True)        
        t1.daemon = True                 
        t1.start()   
    
    def executeCrawler_stoplabel(self):
        self.shop_checkHour.setEnabled(True)
        self.label.setText("크롤링중지") 
        self.shop_loadTableBtn.setEnabled(True)
        self.shop_loadstop.setEnabled(False)

    def executeCrawler_stop(self):
        t2 = threading.Thread(target = self.executeCrawler_stoplabel, daemon = True)  
        t2.daemon = True         
        t2.start() 
        print("중지완료")
    
    def closeEvent(self, event):
        reply = QMessageBox.question(self, '알림', "프로그램을 종료하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            pid = os.getpid()
            os.kill(pid, 2)
            event.accept()
        else:
            event.ignore()
    
    #텔레그램 메시지 수신시 checkbox 상태를 체크해서 reload작업
    def changeReceiveChk(self, state):
        if state == Qt.Checked: #check되있을경우에만 reload
            self.reloadTable()

#############################################
## 쿼리 s
def selectDB(col ,table):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    sql = "SELECT "+ col +" FROM " + table
    cursor.execute(sql)
    conn.commit()
    db_list = cursor.fetchall()
    # conn.close()
    return db_list

def insertDB(product, keyword, mid, company, rank, memo):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    #INSERT 전 Mid+키워드 조합으로 중복 체크 해야함
    sql = "SELECT idx FROM product WHERE pd_mid = ? AND pd_keyword = ?"
    param = (mid, keyword)
    cursor.execute(sql, param)
    conn.commit()
    rows = cursor.fetchall()
    if len(rows) > 0:
        return False
    
    sql  = "INSERT INTO product (pd_name, pd_keyword, pd_mid, pd_company, pd_rank, pd_memo, pd_date) VALUES (?,?,?,?,?,?,?)"
    param = (product, keyword, mid, company, rank, memo, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    cursor.execute(sql, param)
    conn.commit()
    return True

def updateDB(idx, product, keyword, mid, company, rank, memo):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    #UPDATE 전 Mid+키워드 조합으로 중복 체크 해야함
    sql = "SELECT idx FROM product WHERE pd_mid = ? AND pd_keyword = ? AND idx != ?"
    param = (mid, keyword, idx)
    cursor.execute(sql, param)
    conn.commit()
    rows = cursor.fetchall()
    if len(rows) > 0:
        return False

    sql  = "UPDATE product SET pd_name = ?, pd_keyword = ?, pd_mid = ?, pd_company = ?, pd_rank = ?, pd_memo = ?, pd_date = ? WHERE idx = ?"
    param = (product, keyword, mid, company, rank, memo, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx)
    cursor.execute(sql, param)
    conn.commit()
    return True

def deleteDB(idx):
    cursor = conn.cursor()
    sql  = "DELETE FROM product WHERE idx = ?"
    param = (idx,)
    cursor.execute(sql, param)
    conn.commit()
    # conn.close()
## 쿼리 e

def checkSchedule():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    sql = "SELECT * FROM notice WHERE noti_check = '대기중'"
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        noti_idx = row[0]
        message = row[2]
        sendDate = row[1]
        nowDate = datetime.now().strftime('%Y-%m-%d %H:%M')

        if nowDate >= sendDate:
            sql1 = "SELECT DISTINCT tl_telegram_id FROM telegram_list"
            cursor.execute(sql1)
            rows1 = cursor.fetchall()
            for row1 in rows1:
                sendMessage('[공지사항]\n' + message, row1[0])

                sql2 = "UPDATE notice SET noti_check = '전송완료' WHERE noti_idx = ?"
                param = (noti_idx,)
                cursor.execute(sql2, param)
                conn.commit()

#텔레그램 메시지 송신
def sendMessage(text, chatId):
    try:
        bot.sendMessage(chat_id = chatId, text = text, parse_mode='HTML')
    except:
        print('[오류] 텔레그램 전송 오류. 주소를 찾을수 없습니다.')

#텔레그램 메시지 수신
def callbackContext(update, context):
    response_text = update.message.text
    chat_id = str(update.message.chat_id)
    user_name = str(update.message.from_user.username)
    user_full_name = str(update.message.from_user.full_name)
    
    if response_text.startswith('/사용자등록') :
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        company = response_text.replace("/사용자등록 ", "")

        sql = "SELECT * FROM telegram_list WHERE tl_company = '" + company + "' ORDER BY idx"
        cursor.execute(sql)
        conn.commit()
        rows = cursor.fetchall()

        if len(rows) < 5: #5개미만이면 INESRT
            sql = "INSERT INTO telegram_list (tl_company, tl_telegram_id, tl_date) VALUES (?,?,?)"
            param = (company, chat_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            cursor.execute(sql, param)
            conn.commit()
            sendMessage('[안내] 등록 신청이 완료되었습니다.\n현재 등록 갯수 : ' + str(len(rows)+1) + '/5개', chat_id)
        else:
            sql = "UPDATE telegram_list SET tl_telegram_id = ?, tl_date = ? WHERE idx = ?"
            param1 = (chat_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rows[0][0])
            cursor.execute(sql, param1)
            conn.commit()
            sendMessage('[안내] 최대 등록 갯수(5개)를 초과되어 가장 오래된 ID값이 업데이트 되었습니다.', chat_id)

        conn.close()
        
    elif response_text.startswith('/상품등록') :
        values = response_text.split()
        
        if len(values) != 4:
            sendMessage('[오류] 명령어를 올바르게 입력해주세요.\n/상품등록 mid 키워드 업체명', chat_id)
        else:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            mid = values[1]
            keyword = values[2]
            company = values[3]

            result = insertDB('', keyword, mid, company, -1, '')
            if result == False:
                sendMessage('[오류] 중복된 데이터가 있습니다.\nmid : ' + mid + '\n키워드 : ' + keyword, chat_id)
            else:
                sendMessage('[안내] 상품이 등록되었습니다.\nmid : ' + mid + '\n키워드 : ' + keyword + '\n업체명 : ' + company, chat_id)

            #텔레그램 메시지 수신시 테이블 reload
            mainWindow.shop_receiveChkBtn.setChecked(True)
            mainWindow.shop_receiveChkBtn.setChecked(False)

    elif response_text.startswith('/상품삭제') :
        values = response_text.split()

        if len(values) != 2:
            sendMessage('[오류] 명령어를 올바르게 입력해주세요.\n/상품삭제 mid', chat_id)
        else:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            mid = values[1]

            sql = "SELECT * FROM product WHERE pd_mid = ?"
            param = (mid,)
            cursor.execute(sql, param)
            conn.commit()
            rows = cursor.fetchall()
            delNum = len(rows)

            if delNum == 0:
                sendMessage('[오류] 삭제 가능한 mid가 없습니다.', chat_id)
            else:
                sql  = "DELETE FROM product WHERE pd_mid = ?"
                param = (mid,)
                cursor.execute(sql, param)
                conn.commit()
                sendMessage('[안내] ' + str(delNum) + '개의 상품이 삭제되었습니다.\nmid : ' + mid, chat_id)
                conn.close()

                #텔레그램 메시지 수신시 테이블 reload
                mainWindow.shop_receiveChkBtn.setChecked(True)
                mainWindow.shop_receiveChkBtn.setChecked(False)
                
    elif response_text.startswith('/등록리스트') :
        values = response_text.split()

        if len(values) != 2:
            sendMessage('[오류] 명령어를 올바르게 입력해주세요.\n/등록리스트 업체명', chat_id)
        else:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            company = values[1]

            sql = "SELECT * FROM product WHERE pd_company = ?"
            param = (company,)
            cursor.execute(sql, param)
            conn.commit()
            rows = cursor.fetchall()

            if len(rows) == 0:
                sendMessage('[오류] 등록된 업체명을 찾을 수 없습니다.', chat_id)
            else:
                message = f'[안내] {company} 업체 등록리스트\n'
                sendMessage(message, chat_id)

                for i, row in enumerate(rows):
                    no = i+1
                    keyword = row[2]
                    product_name = row[1]
                    mid = row[3]
                    rank = row[5]
                    date = row[8]
                    message = f'No.{no}\n키워드 : {keyword}\n상품명 : {product_name}\nMid : {mid}\n현재순위 : {rank}위\n\n'
                    sendMessage(message, chat_id)

    else :
        sendMessage('[오류] 등록되지 않은 명령어입니다.\nex) /사용자등록 업체명\nex) /상품등록 mid 키워드 업체명\nex) /상품삭제 mid\nex) /등록리스트 업체명', chat_id)

class AlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #텔레그램 초기 세팅
    if not telegram_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")
    bot = telegram.Bot(token=telegram_token)
    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    updater.start_polling()
    dispatcher.add_handler(MessageHandler(Filters.text, callbackContext))

    schedule = BackgroundScheduler(daemon=True, timezone='Asia/Seoul')
    schedule.add_job(checkSchedule, 'interval', seconds=10)
    schedule.start()

    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
