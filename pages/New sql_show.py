import mysql.connector
import streamlit as st
import sqlite3
import pandas as pd
#connection=mysql.connector.connect(
#    host='localhost',
#    user='root',
#    password='ydy2350149',
 #   database='meeting_rooms'
#)
#cursor=connection.cursor()

#cursor.execute("Select * from reservations")
#data=cursor.fetchall()
title_color = "#04256e"  # 自定义标题颜色
header_color = "#0d3a9b"
st.markdown(
    f"""
    <style>
    .stTitle {{
        color: {title_color};
        margin-top: 10px;       /* 段前间距 */
        margin-bottom: 20x;
    }}
    .indented-str {{
        text-indent: 2em;
        margin-top: 10px;       /* 段前间距 */
        margin-bottom: 40px;
        color: {header_color};  /* 缩进2字符 */
    }}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown("""
<style>
    h1 {
      font-size: 52px;
      text-align:left;
      text-transform: uppercase;
   }
    h3 {
      font-size: 20px;
      text-align: left;
      text-transform: uppercase;
   }      
</style>
""", unsafe_allow_html=True)
st.markdown(f'<h1 class="stTitle">🤓SQLDatabese&Show</h1>', unsafe_allow_html=True)
st.text("")
#df=pd.DataFrame(data,columns=cursor.column_names,)
#st.dataframe(df)
#使用sqlite3时用
conn = sqlite3.connect(r'G:\Sqlite\booking.db')
cursor=conn.cursor()

# 获取bookings表的数据
cursor.execute("SELECT * FROM bookings")
bookings_data = cursor.fetchall()
bookings_column_names = [description[0] for description in cursor.description]

# 获取students表的数据
cursor.execute("SELECT * FROM students")
students_data = cursor.fetchall()
students_column_names = [description[0] for description in cursor.description]
#获取rooms表格
cursor.execute("SELECT * FROM rooms")
rooms_data = cursor.fetchall()
rooms_column_names = [description[0] for description in cursor.description]
# 关闭数据库连接
conn.close()

# 创建Streamlit应用
st.title('Streamlit SQLITE Connection')

# 显示bookings表的数据
st.subheader('Bookings Table')
bookings_df = pd.DataFrame(bookings_data, columns=bookings_column_names)
st.dataframe(bookings_df)

# 显示students表的数据
st.subheader('Students Table')
students_df = pd.DataFrame(students_data, columns=students_column_names)
st.dataframe(students_df)
# 显示students表的数据
st.subheader('Rooms Table')
students_df = pd.DataFrame(rooms_data, columns=rooms_column_names)
st.dataframe(students_df)
#cursor.execute("Select * from bookings")/ncursor.execute("Select * from students")/ndata=cursor.fetchall()/ncolumn_names = [description[0] for description in cursor.description]
#for column in column_names:
 #   print(column)
#st.title('streamlit SQLITE Connection')/ndf=pd.DataFrame(data,columns=column_names)/nst.dataframe(df)