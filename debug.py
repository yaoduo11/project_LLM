#导入封装好的和MeetingQA类
from phdGuid_chain import PhdguidQA
from Meeting_chain import MeetingQA
#——————————————————————————————————————————————————————————————————————————————————————————
import os
from langchain.prompts import PromptTemplate
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_models.moonshot import MoonshotChat
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains.router.llm_router import RouterOutputParser

from langchain.chains.router.multi_prompt_prompt import MULTI_PROMPT_ROUTER_TEMPLATE
from ImageTo import upload_image
import base64
from langchain_core.chat_history import HumanMessage
from langchain_core.chat_history import AIMessage
#更改你自己的api_key
os.environ["MOONSHOT_API_KEY"] = "MOONSHOT_API_KEY"
llm = MoonshotChat(model="moonshot-v1-8k", moonshot_api_key=os.environ["MOONSHOT_API_KEY"])
# 网页标题---包含样式————————————————————————————————————————————————————————————————————————————
from PIL import Image
#加载图片自定义————————————————————————————————————————————————————————————————————————————
def load_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
logo_avatar = 'static\logo1.png'
logo_avatar_path= load_image(logo_avatar)
#st.image("static\logo.png",width=300)
# 显示logo和标题
#st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="logo.png")
title_color = "#04256e"  # 自定义标题颜色
header_color = "#0d3a9b"
st.markdown(
    f"""
    <style>
    .stTitle {{
        color: {title_color};
    }}
    .stHeader {{
        color: {header_color};
        text-indent: 0.5em;                                                                                                                                
    }}
     .indented-text {{
        text-indent: 3em;
        margin-top: 30px;       /* 段前间距 */
        margin-bottom: 30px;  /* 缩进2字符 */
    }}
    .indented-str {{
        text-indent: 2em;
        margin-top: 10px;       /* 段前间距 */
        margin-bottom: 10px;
        color: {header_color};  /* 缩进2字符 */
    }}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown("""
<style>
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .logo {
        width: 180px; /* 根据需要调整logo的宽度 */
        height: auto;
        margin-bottom: 10px;
    }
    .title {
        font-size: 70px;
        color: #04256e; /* 深蓝色 */
        margin-bottom: 30px; /* logo和标题之间的间距 */
        text-transform: uppercase;
    }
    h1 {
      text-align:left;
      text-transform: uppercase;
   }
    h2 {
      text-align: left;
      text-transform: uppercase;
   }
    h3 {
      text-align: left;
      text-transform: uppercase;
   }
    .image-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .resized-image {
        width: 100%; /* 填满宽度 */
        height: 20px; /* 固定高度 */
        object-fit: cover; /* 确保图片适应容器 */
    }   
</style>
""", unsafe_allow_html=True)
#添加logo
gradient_text_html = """
<style>
.gradient-text {
    text-align:left;
    font-weight: bold;
    background: -webkit-linear-gradient(left, red, orange);
    background: linear-gradient(to right, orange, red);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 20px;
    margin-bottom: 10px;    
    display: flex;
    font-size: 2.5em;
}
</style>
"""
logo_title=f"""<div class="header-container">
        <img src="data:image/png;base64,{logo_avatar_path}"  class="logo" alt="Logo">
        <h1 class="gradient-text"> Copilot</h1>
        </div>
"""

st.markdown(gradient_text_html, unsafe_allow_html=True)
    #<h1 class="title">CityU Q&A</h1>
            #<h1 class="title"> Assistant 2.0</h1>
st.markdown(logo_title, unsafe_allow_html=True)
image_path = "static\ee.png"
image = Image.open(image_path)
# 调整图像的大小
resized_image = image.resize((image.width,40))  # 将高度调整为 50px，宽度保持原样
# 显示调整后的图像
st.image(resized_image, use_column_width=True)

st.text("")
#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
#初始化数据库以及加载文档
view_messages = st.expander("View the message contents in session state")
from langchain_community.utilities import SQLDatabase
#更改路径
db=SQLDatabase.from_uri("sqlite:///G:/Sqlite/booking.db")
loader_path =r"G:\llm program\scholarship.pdf"
loader_path1=r"G:\llm program\aphdqualify_exam.pdf"
loader_path2=r"G:\llm program\thesis_defence.pdf"
scholarship_system=PhdguidQA(loader_path, llm,"appendix")
PhDQualifying_system=PhdguidQA(loader_path1, llm,"appendix0")
ThesisExamination_system=PhdguidQA(loader_path2, llm,"appendix1")
meeting_system = MeetingQA(db,llm)
Scholarship_chain =scholarship_system.get_chain()
PhDQualifyingExaminationchain_chain=PhDQualifying_system.get_chain()
ThesisExaminationchain_chain=ThesisExamination_system.get_chain()
Meeting_chain=meeting_system.get_chain()
destination_chains = {}
destination_chains["meeting_roomQA"] =Meeting_chain
destination_chains["ScholarshipQA"] =Scholarship_chain
destination_chains["PhDQualifyingExaminationQA"] =PhDQualifyingExaminationchain_chain
destination_chains["ThesisExaminationQA"] =ThesisExaminationchain_chain
destinations_template_str = """
meeting_roomQA:Good at answering questions about booking a meeting room, querying about meeting rooms, modifying meeting room details, or deleting/canceling a meeting room booking.
ScholarshipQA:Good at answering Phd scholarship questions.
PhDQualifyingExaminationQA:Good at answering questions about PhD Qualifying Examination
ThesisExaminationQA:Good at answering questions about Thesis Examination.
"""
router_template = MULTI_PROMPT_ROUTER_TEMPLATE.format(
    destinations=destinations_template_str
)
router_prompt = PromptTemplate(
    template=router_template,
    input_variables=["input"],
    output_parser=RouterOutputParser(),
)
def router(query):
    try:
        router_chain = router_prompt|llm|JsonOutputParser()
        router_with_history=RunnableWithMessageHistory(
        router_chain ,
        #get_session_history,
        lambda session_id: msgs,
        input_messages_key="input",
        history_messages_key="history")
        #output_messages_key="answer")
        response=router_with_history.invoke({"input":query},config={"configurable": {"session_id": "abs"}})
        print(response)
        destination = response['destination']
        selected_chain = destination_chains.get(destination)
        Runable_history=RunnableWithMessageHistory(
        selected_chain,
        #get_session_history,
        lambda session_id: msgs,
        input_messages_key="input",
        history_messages_key="history",
        output_messages_key="answer"
    )
        return Runable_history
    except Exception as e:
        return "no !!!"
        
#——————————————————————————————————————————————————————————————————————————————————————————————
#整体对话的样式———css———————————————————————————————————————————————————————————————————————————————————
import streamlit as st
import time
st.markdown(
    """
    <style>
    .chat-message-container {
    max-width: 1080px;
    margin: 0 auto;
    display: flex;
    margin-bottom: 20px; /* Increased margin for message separation */
    align-items: flex-end;
    padding: 10px; /* Add padding for better spacing */
    
}
.chat-message-box {
        background-color: #f1f1f1; /* 对话框背景色 */
        border: 1px solid #ddd; /* 对话框边框 */
        border-radius: 10px; /* 圆角边框 */
        padding: 15px; /* 内边距 */
        max-width: 80%; /* 最大宽度 */
        word-wrap: break-word; /* 自动换行 */
    }
.chat-message-container.ai {
    justify-content: flex-start; /* Align AI messages to the left */
}
.chat-message-container.human {
    justify-content: flex-end; /* Align Human messages to the right */
}
.chat-message-content {

display: flex;
align-items: center;
max-width: 60%;
}
.chat-avatar-left {
    width: 38px;
    height: 40px;
    border-radius: 12%;
    margin-right: 10px;
    transform: translateY(6px) translateX(2px);
}
.chat-avatar-right {

    width: 28px;
    height:34px;
    border-radius: 60%;
    transform: translateY(-1px) translateX(12px);
    
}
.floating {
    animation: float 1s infinite; /* Add animation */
}
@keyframes float {
    0% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0); }
}
.chat-message {
    font-size:20px
    display: inline-block;
    background-color: #f2f1f1;
    padding: 15px 30px 15px 30px;
    border: None;
    border-radius: 10px 20px 20px 1px;
    background: #ffffff;
    max-width: 80%;
    word-wrap: break-word;
    margin-bottom: 20px; 
}
.chat-rightmessage {
    color:#f9ede8;
    display: inline-block;
    background-color: #f2f1f1;
    padding: 8px 20px 8px 20px;
    border: None;
    border-radius:  20px 10px 1px 20px;
    background: linear-gradient(to right, rgba(255, 165, 0, 1), rgba(209, 56, 112, 1));
    max-width: 80%;
    word-wrap: break-word;
    margin-bottom: 20px; 
}
ol {
font-weight: bold; 
}

div{
font-size:20px
}
p{
font-size:20px
}
ul {
font-weight: bold; 
}
td {
font-weight: 100; 
    display: table-cell;
    vertical-align: inherit;
    unicode-bidi: isolate;
}
th {
    text-align: -webkit-match-parent;
}
.st-emotion-cache-1kzds0v li {
font-size:18px

}
.st-emotion-cache-1uj96rm {
    position: sticky;
    left: 0px;
    bottom: 0px;
    width: 60%;
}
.st-emotion-cache-1eo1tir {
    width: 100%;
    padding: 6rem 1rem 1rem;
    max-width: 80rem;
}
.st-emotion-cache-arzcut {
    width: 100%;
    padding: 1rem 1rem 55px;
    max-width: 80rem;
}
.spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border-left-color: #09f;
    animation: spin 1s linear infinite;
}
div{

}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
        </style>
        """,
        unsafe_allow_html=True,
    )

robot_avatar = 'static\obot2.png' 
human_avatar = 'static\human.png'
warning_avatar='static\warning.png'
# 将图片转换为 Base64
robot_avatar_path= load_image(robot_avatar)
human_avatar_path= load_image(human_avatar)
warning_avatar_path=load_image(warning_avatar)
#对话框以及加载对话头像的格式—————————————————————————————————————————————————————————————————————————
def create_chat_message_html(avatar_base64, message, alignment):
    avatar_data_uri = f"data:image/png;base64,{avatar_base64}"
    if alignment=="ai":
        
        return f'''
        <div class="chat-message-container {alignment}">
            <img src="{avatar_data_uri}" class="chat-avatar-left">
            <div class="chat-message">{message}</div>
        </div>
        '''
    
    else:
        return f'''
            <div class="chat-message-container {alignment}">
                <div class="chat-rightmessage">{message}</div>
                <img src="{avatar_data_uri}" class="chat-avatar-right">
            </div>
            '''
#st.markdown(div,unsafe_allow_html=True)
#——————————————————————————————————————————————————————————————————————————————————————

# 使用 Base64 编码的图片显示
#st.markdown(f'<img src="data:image/png;base64,{img_base64}" width="600">', unsafe_allow_html=True)
#逐字打印且有圆角背景框并且具有浮动动画效果---------------------------------------
def display_message_with_avatar_and_typing(message_type, avatar_path, message):
    # Custom CSS for left-aligned chat message
    # Create a container to hold the avatar and message
    message_container = st.container()
    with message_container:
        # Create a placeholder for the typing message
        message_placeholder = st.empty()
        
        # Initial empty message to set up the container
        chat_message_html = f'<img src="data:image/png;base64,{avatar_path}" class="chat-avatar-left  floating"><div class="chat-message-container"><div class="chat-message"></div></div>'
        message_placeholder.markdown(chat_message_html, unsafe_allow_html=True)
        
        # Typing effect: gradually display the message
        for i in range(1, len(message) + 1):
            time.sleep(0.01)
            chat_message_html = f'<div class="chat-message-container"><img src="data:image/png;base64,{avatar_path}" class="chat-avatar-left floating" ><div class="chat-message">{message[:i]}</div></div>'
            message_placeholder.markdown(chat_message_html, unsafe_allow_html=True)
                # Final message display
        chat_message_html = f'<div class="chat-message-container"><img src="data:image/png;base64,{avatar_path}" class="chat-avatar-left  "><div class="chat-message">{message}</div></div>'
        message_placeholder.markdown(chat_message_html, unsafe_allow_html=True)
#————————————————————————————————————————————————————————————————————————————————————————————————
msgs = StreamlitChatMessageHistory(key="chat_messages")
#if len(msgs.messages) == 0:
#    msgs.add_ai_message("Hello, Bob!I am your  assistant!")
if 'messages' not in st.session_state:
        st.session_state['messages'] = [AIMessage(content="Hello, Bob! I am your assistant!")] 


#历史对话显示--------------------------------------------
for message in st.session_state.messages:
    if isinstance(message,HumanMessage):
        chat_message_html = create_chat_message_html(human_avatar_path,message.content,"human")
        st.markdown(chat_message_html, unsafe_allow_html=True)
    elif isinstance(message,AIMessage):
        chat_message_html = create_chat_message_html(robot_avatar_path,message.content,"ai")
        st.markdown(chat_message_html, unsafe_allow_html=True)
    #用户输入问题此结构其中头像不包含动画效果-----------------------------------------------------------------------
#主程序显示message   
def display_message(msg_type, content):
    if msg_type == "ai":
        chat_message_html = create_chat_message_html(robot_avatar_path, content, "ai")
    else:
       chat_message_html = create_chat_message_html(human_avatar_path ,content, "human")
    st.markdown(chat_message_html, unsafe_allow_html=True)
    #if input_text:= st.chat_input("Say something", key="text_input"):
if input_text := st.chat_input("Say something", key="text_input"):
    st.session_state['messages'].append(HumanMessage(content=input_text))
    display_message("human", input_text)
    tt=router(input_text)      
    try:
        with st.spinner(''):
            answer =tt.invoke(
                {"input": input_text},
                config={"configurable": {"session_id": "abs"}}
            )['answer']
        st.session_state['messages'].append(AIMessage(content=answer)) 
        display_message_with_avatar_and_typing("ai", robot_avatar_path, answer)
    except Exception as e:
        print(f"14{str(e)}")
        display_message_with_avatar_and_typing("ai", warning_avatar_path, "Sorry,Please re-input question...........")
      
