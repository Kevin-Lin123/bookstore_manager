# bookstore_manager.py
import sqlite3
from typing import Optional

def connect_db() -> sqlite3.Connection:
    """建立資料庫連線"""
    conn = sqlite3.connect('bookstore.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db(conn: sqlite3.Connection) -> None:
    """初始化資料庫表格與資料"""
    try:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS member (
                mid TEXT PRIMARY KEY,
                mname TEXT NOT NULL,
                mphone TEXT NOT NULL,
                memail TEXT
            );
            
            CREATE TABLE IF NOT EXISTS book (
                bid TEXT PRIMARY KEY,
                btitle TEXT NOT NULL,
                bprice INTEGER NOT NULL,
                bstock INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS sale (
                sid INTEGER PRIMARY KEY AUTOINCREMENT,
                sdate TEXT NOT NULL,
                mid TEXT NOT NULL,
                bid TEXT NOT NULL,
                sqty INTEGER NOT NULL,
                sdiscount INTEGER NOT NULL,
                stotal INTEGER NOT NULL
            );
            
            INSERT INTO member VALUES 
                ('M001', 'Alice', '0912-345678', 'alice@example.com'),
                ('M002', 'Bob', '0923-456789', 'bob@example.com'),
                ('M003', 'Cathy', '0934-567890', 'cathy@example.com');
                
            INSERT INTO book VALUES 
                ('B001', 'Python Programming', 600, 50),
                ('B002', 'Data Science Basics', 800, 30),
                ('B003', 'Machine Learning Guide', 1200, 20);
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"資料庫初始化失敗: {e}")
        conn.rollback()




def validate_date(date_str: str) -> bool:
    """驗證日期格式"""
    return len(date_str) == 10 and date_str.count('-') == 2

def add_sale(conn: sqlite3.Connection) -> None:
    """新增銷售記錄"""
    try:
        sdate = input("請輸入銷售日期 (YYYY-MM-DD)：")
        if not validate_date(sdate):
            raise ValueError("日期格式錯誤")
            
        mid = input("請輸入會員編號：")
        bid = input("請輸入書籍編號：")
        
        # 檢查會員和書籍是否存在
        cursor = conn.cursor()
        member = cursor.execute("SELECT * FROM member WHERE mid = ?", (mid,)).fetchone()
        book = cursor.execute("SELECT * FROM book WHERE bid = ?", (bid,)).fetchone()
        
        if not member or not book:
            print("=> 錯誤：會員編號或書籍編號無效")
            return
            
        # 輸入數量與折扣
        while True:
            try:
                sqty = int(input("請輸入購買數量："))
                if sqty <= 0:
                    print("=> 錯誤：數量必須為正整數")
                    continue
                break
            except ValueError:
                print("=> 錯誤：必須輸入整數")
                
        while True:
            try:
                sdiscount = int(input("請輸入折扣金額："))
                if sdiscount < 0:
                    print("=> 錯誤：折扣金額不能為負數")
                    continue
                break
            except ValueError:
                print("=> 錯誤：必須輸入整數")
        
        # 檢查庫存
        if book['bstock'] < sqty:
            print(f"=> 錯誤：書籍庫存不足 (現有庫存: {book['bstock']})")
            return
            
        # 計算總額
        stotal = (book['bprice'] * sqty) - sdiscount
        
        # 交易處理
        try:
            cursor.execute("""
                INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sdate, mid, bid, sqty, sdiscount, stotal))
            
            cursor.execute("""
                UPDATE book SET bstock = bstock - ? WHERE bid = ?
            """, (sqty, bid))
            
            conn.commit()
            print(f"=> 銷售記錄已新增！(銷售總額: {stotal:,})")
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"=> 資料庫錯誤: {e}")
            
    except ValueError as e:
        print(f"=> 輸入錯誤: {e}")



def print_sale_report(conn: sqlite3.Connection) -> None:
    """顯示銷售報表"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, 
               s.sqty, s.sdiscount, s.stotal
        FROM sale s
        JOIN member m ON s.mid = m.mid
        JOIN book b ON s.bid = b.bid
        ORDER BY s.sid
    """)
    
    sales = cursor.fetchall()
    
    print("\n==================== 銷售報表 ====================")
    for idx, sale in enumerate(sales, 1):
        print(f"銷售 #{idx}")
        print(f"銷售編號: {sale['sid']}")
        print(f"銷售日期: {sale['sdate']}")
        print(f"會員姓名: {sale['mname']}")
        print(f"書籍標題: {sale['btitle']}")
        print("--------------------------------------------------")
        print(f"{sale['bprice']:,}  {sale['sqty']}  {sale['sdiscount']}  {sale['stotal']:,}")
        print("--------------------------------------------------")
        print(f"銷售總額: {sale['stotal']:,}")
        print("==================================================")



def list_sales(conn: sqlite3.Connection) -> list:
    """取得銷售記錄列表"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sid, s.sdate, m.mname 
        FROM sale s
        JOIN member m ON s.mid = m.mid
        ORDER BY s.sid
    """)
    return cursor.fetchall()

def update_sale(conn: sqlite3.Connection) -> None:
    """更新銷售記錄"""
    sales = list_sales(conn)
    print("\n======== 銷售記錄列表 ========")
    for idx, sale in enumerate(sales, 1):
        print(f"{idx}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
    print("================================")
    
    try:
        choice = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ")
        if not choice:
            return
            
        sid = int(choice)
        cursor = conn.cursor()
        sale = cursor.execute("SELECT * FROM sale WHERE sid = ?", (sid,)).fetchone()
        
        if not sale:
            print("=> 錯誤：銷售編號不存在")
            return
            
        new_discount = int(input("請輸入新的折扣金額："))
        if new_discount < 0:
            print("=> 錯誤：折扣金額不能為負數")
            return
            
        # 重新計算總額
        book = cursor.execute("SELECT bprice FROM book WHERE bid = ?", (sale['bid'],)).fetchone()
        new_total = (book['bprice'] * sale['sqty']) - new_discount
        
        cursor.execute("""
            UPDATE sale 
            SET sdiscount = ?, stotal = ?
            WHERE sid = ?
        """, (new_discount, new_total, sid))
        
        conn.commit()
        print(f"=> 銷售編號 {sid} 已更新！(銷售總額: {new_total:,})")
        
    except ValueError:
        print("=> 錯誤：請輸入有效的數字")

def delete_sale(conn: sqlite3.Connection) -> None:
    """刪除銷售記錄"""
    sales = list_sales(conn)
    print("\n======== 銷售記錄列表 ========")
    for idx, sale in enumerate(sales, 1):
        print(f"{idx}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
    print("================================")
    
    try:
        choice = input("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ")
        if not choice:
            return
            
        sid = int(choice)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sale WHERE sid = ?", (sid,))
        
        if cursor.rowcount == 0:
            print("=> 錯誤：銷售編號不存在")
            return
            
        conn.commit()
        print(f"=> 銷售編號 {sid} 已刪除")
        
    except ValueError:
        print("=> 錯誤：請輸入有效的數字")



def main_menu() -> None:
    """主選單介面"""
    print("\n***************選單***************")
    print("1. 新增銷售記錄")
    print("2. 顯示銷售報表")
    print("3. 更新銷售記錄")
    print("4. 刪除銷售記錄")
    print("5. 離開")
    print("**********************************")

# 更新 main 函式
if __name__ == "__main__":
    with connect_db() as conn:
        initialize_db(conn)
        while True:
            main_menu()
            choice = input("請選擇操作項目(Enter 離開)：").strip()
            
            if not choice:
                break
                
            if choice == '1':
                add_sale(conn)
            elif choice == '2':
                print_sale_report(conn)
            elif choice == '3':
                update_sale(conn)
            elif choice == '4':
                delete_sale(conn)
            elif choice == '5':
                break
            else:
                print("=> 請輸入有效的選項（1-5）")