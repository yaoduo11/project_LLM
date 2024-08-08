from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain.tools.render import render_text_description
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from operator import itemgetter
import re
import time
import datetime
import uuid

#支持上下文保留的包
from langchain_core.prompts import MessagesPlaceholder
def parse_conditions(conditions_str):
    condition_pattern = re.compile(r'(\w+)\s*(>=|<=|!=|=|>|<|LIKE)\s*(\'[^\']*\'|"[^"]*"|[^ \'\"]+)')
    
    # Find all matches in the conditions string
    matches = condition_pattern.findall(conditions_str)
    
    # Create a dictionary to store parsed conditions
    condition_dict = {}
    
    for match in matches:
        key, _, value = match  # Ignore the operator
        # Remove surrounding quotes if they exist
        value = value.strip('\'"')
        condition_dict[key.strip()] = value.strip()  # Store the value directly
    return condition_dict
def search_conditions(conditions):
        
    conditions_str= parse_conditions(conditions)
    if 'location'in conditions_str:
        value=conditions_str.get('location')
        conditions=f"location LIKE '%{value}%'"                
    elif 'room_type'in conditions_str:
        value=conditions_str.get('room_type')
        conditions=f"room_type = '{value}' AND is_available = True"  
    elif 'capacity'in conditions_str:
        conditions=conditions  
    elif 'room_number'in conditions_str:
        value=conditions_str.get('room_number')
        conditions=f"room_number ='{value}'"
    else:
        conditions="is_available = True"    
    return conditions
def tankle_tuple(result):
    python_list = eval(result)
    tuple_value = python_list[0]
    extracted_value = tuple_value[0]
    return extracted_value
class MeetingQA:
    def __init__(self,db, llm):
        self.db=db
        self.llm=llm
        #Note: When there is only "afternoon," "noon," or "morning" without a specific time range, determine the time range first before using this tool.
        @tool
        def search_time_room(start_time: str, end_time: str,conditions:str="",) -> str:
            """ 
            Search for available meeting rooms within a specified time range,
            optionally applying additional conditions.
            Args:
            conditions (str, optional):The conditions for the WHERE clause,May be needed.
            """
            try:
                conditions=search_conditions(conditions)
                if conditions:
                    query = f"SELECT room_number,capacity,location FROM rooms WHERE {conditions} AND is_available = True AND room_number NOT IN (SELECT room_number FROM bookings WHERE start_time <'{end_time}' AND end_time >'{start_time}');"                
                else:
                    query=f"SELECT room_number,capacity,location FROM rooms WHERE room_number NOT IN (SELECT room_number FROM bookings WHERE start_time <'{end_time}' AND end_time >'{start_time}');"    
                result =db.run(query)  # Uncomment this line for actual database execution
                return result
            except Exception as e:
                # Handle any exceptions that occur during query generation
                error_msg = f"1Error generating SQL query: {str(e)}"
                # Log the error or handle it appropriately
                print(error_msg)
                # Return a default query or an error message
                return "2SELECT * FROM default_table WHERE is_available = 1;"
        @tool
        def search_normal_room(columns:str,table:str,conditions: str = "") -> str:
            """
            It is useful when you need to answer a query for information about a meeting room under a certain condition.
            Args:
            table (str): The name of the table to query.
            columns (str): The columns to select, separated by commas.
            conditions (str, optional): The conditions for the WHERE clause.
            """
            conditions=search_conditions(conditions)
            select_query=f"SELECT {columns} FROM {table} WHERE {conditions};"
            try:
                result=self.db.run(select_query)
                return result
            except Exception as e:
                return f"3Error: {e}"
        @tool
        def db_book_room(room_number: str, start_time: str, end_time: str, student_name: str) -> str:
            """ 
            Books a meeting room if available. Returns the booking ID on success, or an error message otherwise.
            User's name known to the system.
            """
            def ID():
                return (uuid.uuid4().int >> 64) % 100000
            booking_id=ID()
            try:
                con_quey=f"SELECT COUNT(*) FROM bookings WHERE room_number = '{room_number}' AND start_time <= '{end_time}' AND end_time >='{start_time}';"
                book=db.run(con_quey)
                is_booking=tankle_tuple(book)
                if is_booking==0:
                    select_query = f"SELECT student_id FROM students WHERE name = '{student_name}';"
                    student_id_query = self.db.run(select_query)
                    student_id_value = tankle_tuple(student_id_query)
                    insert_query = f"""INSERT INTO bookings (booking_id,student_id, room_number, start_time, end_time)
                        VALUES ('{booking_id}','{student_id_value}', '{room_number}', '{start_time}','{end_time}');
                    """
                    result=db.run(insert_query)
                    #明明已经执行还要继续询问执行
                    return booking_id
                else:
                    return f"{room_number} has been booked at this time, please select again other meeting"
            except Exception as e:
                return f"4Booking error: {str(e)}"
        @tool
        def Cancel_booking(booking_id:int) -> str:
            """
            Cancle a room booking by book_id. If successful, return 'Booking canceled.' otherwise return an error message.
            Args:
            booking_id (int): The booking_id of the booking to be canceled.
            """
            try:
                if booking_id:
                    cancel_query=f"DELETE FROM bookings WHERE booking_id = {booking_id};"
                    try:
                        self.db.run(cancel_query)
                        return "meeting room has been cancelled meeting room successfully"
                    except sqlite3.Error as db_error:
                         return f"44Database error during cancellation: {str(db_error)}"
                else:
                    return f"5No booking_id provided to cancel."   
            except Exception as e:
                return f"6\Error during cancellation: {str(e)}"
        @tool
        def Update_booking(
            booking_id: int, room_number: str = None, new_start_time: str =None, new_end_time: str = None, conditions: str = "") -> str:
            """
            It's useful when you need to answer questions about changing/rewprking information about a meeting room that has already been booked.
            Args:
            booking_id (int): The booking_id of the booking to be Updated.
            new_start_time(str,optional): The new_start_time the user wants to set, different from the previous start time. This parameter is optional.
            new_end_time(str,optional): The new_end_time the user wants to set, different from the previous end time. This parameter is optional.
            """
            booking_id=booking_id
            #临时获取booking_id,room_number以及startime and endtime
            Co_query=f"""WITH ExistingBooking AS (SELECT start_time, end_time FROM bookings WHERE booking_id = {booking_id})"""    
            def is_change():
                #当参数存在时间段时，请确定原来的会议室在此时间段是否能用？
                if room_number:
                    availability_query=f"""{Co_query} SELECT COUNT(*) FROM bookings,ExistingBooking WHERE room_number ='{room_number}' AND bookings.start_time < ExistingBooking.end_time AND bookings.end_time > ExistingBooking.start_time;"""
                #给出新的会议室要修改，此处是判断该会议室在原来时间段是否可用
                elif new_start_time and new_end_time:
                    availability_query=f"""SELECT COUNT(*) FROM bookings WHERE room_number = (SELECT room_number FROM bookings WHERE booking_id = {booking_id}) AND start_time < '{new_end_time}' AND end_time > '{new_start_time}' AND booking_id != {booking_id};"""
                else:
                    raise f"7Error:please reinput question"
                available_query=self.db.run(availability_query)
                is_available_query=tankle_tuple(available_query)     
                return is_available_query
            try:
                if room_number:
                    if is_change()==0:
                        update_query = f"UPDATE bookings SET room_number = '{room_number}' WHERE booking_id = {booking_id};"
                    else:
                        suitable_room_query =f"""{Co_query}
                        SELECT room_number FROM rooms WHERE room_number NOT IN 
                        ( SELECT DISTINCT bookings.room_number
                        FROM bookings JOIN ExistingBooking ON bookings.room_number = rooms.room_number 
                        WHERE bookings.start_time < ExistingBooking.end_time AND bookings.end_time > ExistingBooking.start_time);"""
                        suitable=self.db.run(suitable_room_query)
                        if not suitable:
                            raise "9No available rooms found during the specified time."
                        else:
                            return suitable                                
                elif new_start_time and new_end_time:
                    if is_change()==0:
                        update_query = f"UPDATE bookings SET start_time = '{new_start_time}', end_time = '{new_end_time}' WHERE booking_id = {booking_id};"
                    else:
                        raise "8The room is not available at the specified time. Please choose a different time slot."
                elif conditions:
                    #此sql语法表示在conditions前提下，将查找出符合condition且也符合该时间范围内的会议室，并与之更新
                    conditions=search_conditions(conditions)
                    select_query=f"""{Co_query}
                    SELECT room_number FROM rooms WHERE {conditions} AND room_number 
                    NOT IN ( SELECT DISTINCT bookings.room_number FROM bookings JOIN ExistingBooking ON bookings.room_number = rooms.room_number 
                    WHERE bookings.start_time < ExistingBooking.end_time AND bookings.end_time > ExistingBooking.start_time);
                    """
                    Whether_select=self.db.run(select_query)
                    if Whether_select:
                        update_query =f"""UPDATE bookings SET room_number = ({select_query} LIMIT 1)WHERE booking_id = {booking_id};"""
                    else:
                        raise "10Error:No rooms found matching the given conditions for the specified time range."                
                else:
                    raise "11Error: No valid update parameters provided. Please specify what you want to update."
                # Uncomment the following line to execute the query
                result = self.db.run(update_query)
                return booking_id
            except Exception as e:
                return f"12Error during update: {str(e)}"
        #
        def split_debug_query(llm,tools):
            formatted_time = datetime.datetime.now().strftime("%Y-%m-%d")
            now = datetime.datetime.now()
            weeknu = now.weekday()
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday=weekdays[weeknu]
            table_info=self.db.table_info
            rendered_tools = render_text_description(tools)
            tools_select_prompt_msg = f"""
            Today's date is {formatted_time} , and it is {weekday}.
            You are a quick meeting room assistant, that has access to the following set of tools. Your task is to reason about the appropriate tool based on user input.
            student_name is Bob.
            When you known that the user's booking details, please confirm with the user again before proceeding with booking, updating, or deleting operation.
            Do not automatically calculate time ranges based on terms like 'afternoon' or 'morning'. Instead, always ask the user for a precise time range.
            When the user uses words like "quickly" or "hurry",and knows the time range for the reservation, some tedious inquiries should be skipped, and should be directly selected and booked.
            You can have the capability to book rooms.usually choose tool 'db_book room'
            According{table_info}.
            Here are the tool_names and descriptions for each tool: {rendered_tools}.
            Given the user input, return the tool_name and input of the tool to use. 
            Please convert the date related words like 'today', 'tomorrow', 'friday' to the actual date when necessaray.
            Don't ask for additional content to user.
            Return your response Only as a JSON blob with 'tool_name' and 'arguments' keys.
            << FORMATTING >>
            JSON object formatted to look like:
            ```json
            "tool_name": string \\tool_name of the prompt to use
            "arguments": dict\\arguments for the tool
            
            ```
            """
            prompt = ChatPromptTemplate.from_messages([("system", tools_select_prompt_msg),MessagesPlaceholder(variable_name='history'), ("user", "{input}")])
            tool_map = {tool.name: tool for tool in tools}
            def tool_chain(model_output):
                chosen_tool = tool_map[model_output["tool_name"]]
                return itemgetter("arguments") | chosen_tool
            def choose_parser(model_output):
                if "tool_name" in model_output.content:
                    return JsonOutputParser()|RunnablePassthrough.assign(output=tool_chain)
                else:
                    return StrOutputParser()
            return prompt | llm | choose_parser
            #return prompt | llm |JsonOutputParser()| RunnablePassthrough.assign(output=tool_chain)  
        self.tools = [search_time_room,search_normal_room,db_book_room,Cancel_booking,Update_booking]
        self.llm_with_tools=split_debug_query(self.llm,self.tools)
        self.meeting_roomchain_template = """
        Your are a secretary.
        **Task Instructions:**

        1.you know the booker's student's full name is Bob.
        2.When the user asks you to help select a reservation, please select a meeting from the dialogue history and avoid some extra answer .
        3.Do not display 'tool_name' or reveal that you are using a database.

        **SQL Result:{output} Handling:**
        -If the output is in string form, return 'output' directly without processing.
        -if a booking_id value is found in the SQL result is the booking considered successful; other content cannot confirm booking success.
        
        **Meeting Room Listings:**
        When listing available meeting rooms, present them in a table format based on the SQL result, not randomly generated.
        
        **Response Requirements:**
        the booking_id value is unique and can only be obtained by SQL Result.
        Answer can't show SQL result:dict, can't let user know the operation details.
        Do not return JSON structure.
        Return your answer is concise.
        """
        self.meeting_roomchain_prompt =ChatPromptTemplate.from_messages(
            [("system", self.meeting_roomchain_template ),
            MessagesPlaceholder(variable_name='history'), 
             ("user", "{input}")]
        )
        try:
            self.meeting_room_chain = RunnablePassthrough.assign(output=self.llm_with_tools)|self.meeting_roomchain_prompt |self.llm|StrOutputParser()
            self.meeting_chain= RunnablePassthrough.assign(answer=self.meeting_room_chain)
        except Exception as e:
            print(f"14{str(e)}")
    def get_chain(self):
        return self.meeting_chain
    