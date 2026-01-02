"""
创建或更新 top_performers 表
"""
import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'stock_trade.db')

def migrate():
    """执行数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='top_performers'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("创建 top_performers 表...")
            cursor.execute('''
                CREATE TABLE top_performers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code VARCHAR(20) NOT NULL,
                    name VARCHAR(100),
                    date DATE NOT NULL,
                    period VARCHAR(20) NOT NULL,
                    change_pct FLOAT,
                    amount FLOAT,
                    start_price FLOAT,
                    end_price FLOAT,
                    start_date DATE,
                    end_date DATE,
                    market VARCHAR(10),
                    board VARCHAR(50),
                    rank INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX idx_date_period ON top_performers(date, period)')
            cursor.execute('CREATE INDEX idx_ts_code_date ON top_performers(ts_code, date)')
            cursor.execute('CREATE INDEX idx_period_rank ON top_performers(period, rank)')

            print("表创建完成！")
        else:
            print("表已存在，检查字段...")

            # 检查字段是否已存在
            cursor.execute("PRAGMA table_info(top_performers)")
            columns = [col[1] for col in cursor.fetchall()]

            # 需要添加的新字段
            new_columns = {
                'start_price': 'FLOAT',
                'end_price': 'FLOAT',
                'start_date': 'DATE',
                'end_date': 'DATE',
            }

            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    print(f"添加字段: {col_name}")
                    cursor.execute(f"ALTER TABLE top_performers ADD COLUMN {col_name} {col_type}")
                else:
                    print(f"字段已存在，跳过: {col_name}")

        conn.commit()
        print("数据库操作完成！")

    except Exception as e:
        conn.rollback()
        print(f"操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

