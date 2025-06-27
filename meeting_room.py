pip install gspread
import streamlit as st
import datetime
from datetime import timedelta
import random
import pandas as pd
import pytz
import gspread
from google.oauth2.service_account import Credentials

# --- SETUP ---
# Timezone setup
ist = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.datetime.now(ist)
ctif = current_time_ist.strftime("%y-%m-%d %H:%M:%S")

# Room capacities
room_capacity = {
    "HIMALAYA - Basement": 20,
    "NEELGIRI - Ground Floor": 7,
    "ARAVALI - Ground Floor": 7,
    "KAILASH - 1 Floor": 7,
    "ANNAPURNA - 1 Floor": 4,
    "EVEREST - 2 Floor": 12,
    "KANANACJUNGA - 2 Floor": 7,
    "SHIVALIK - 3 Floor": 4,
    "TRISHUL - 3 Floor": 4,
    "DHAULAGIRI - 3 Floor": 7,
}

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def connect_to_gsheet():
    try:
        # Create the connection using Streamlit secrets
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["1uq53uD-qh0gyLDCc2iUgCutrqMsufQHVG5MZFOornNM"]).sheet1
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- UTILITY FUNCTIONS ---
def generate_booking_id():
    return random.randint(1000, 9999)

def is_room_available(date, start_time, end_time, room):
    sheet = connect_to_gsheet()
    if not sheet:
        return False
    
    records = sheet.get_all_records()
    
    for booking in records:
        if (booking["room"] == room and 
            booking["date"] == date and 
            booking["status"] == "Active" and
            not (end_time <= booking["start_time"] or 
                 start_time >= booking["end_time"])):
            return False
    return True

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def is_upcoming(booking):
    booking_datetime = datetime.datetime.strptime(
        f"{booking['date']} {booking['start_time']}", 
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=ist)
    return booking_datetime > current_time_ist

# --- BOOKING FUNCTIONS ---
def book_room():
    st.header("Book a Room")
    date = st.date_input("Select the Date:", min_value=current_time_ist.date(), value=None)
    
    if date:
        # Time selection logic
        office_start = datetime.time(8, 0)
        office_end = datetime.time(20, 0)
        start_times = [office_start]
        
        while start_times[-1] < office_end:
            next_time = (datetime.datetime.combine(date, start_times[-1]) + timedelta(minutes=15))
            start_times.append(next_time.time())
        
        start_time = st.selectbox("Select Start Time:", start_times, index=None)
        
        if start_time:
            if date == current_time_ist.date() and start_time < current_time_ist.time():
                st.warning("Start time must be in the future")
                return
                
            end_times = [
                (datetime.datetime.combine(date, start_time) + timedelta(minutes=15*i)).time() 
                for i in range(1, 49)  # Max 12 hours
                if (datetime.datetime.combine(date, start_time) + timedelta(minutes=15*i)).time() <= datetime.time(23, 59)
            ]
            
            end_time = st.selectbox("Select End Time:", end_times, index=None)
            
            if end_time:
                # Show available rooms
                available_rooms = []
                for room, capacity in room_capacity.items():
                    if is_room_available(str(date), str(start_time), str(end_time), room):
                        available_rooms.append(f"{room} (Capacity: {capacity})")
                
                if not available_rooms:
                    st.warning("No rooms available for selected time")
                    return
                    
                room_choice = st.selectbox("Select Room:", available_rooms, index=None)
                
                if room_choice:
                    # Booking details
                    selected_room = room_choice.split(" (Capacity: ")[0]
                    description = st.text_input("Meeting Title:")
                    name = st.text_input("Your Name:")
                    email = st.text_input("Your Email:")
                    
                    if st.button("Confirm Booking"):
                        if not all([name, description, email]):
                            st.warning("Please fill all required fields")
                            return
                            
                        if not is_valid_email(email):
                            st.warning("Please enter a valid email address")
                            return
                            
                        # Create booking
                        booking_id = generate_booking_id()
                        sheet = connect_to_gsheet()
                        
                        if sheet:
                            sheet.append_row([
                                booking_id,
                                str(date),
                                str(start_time),
                                str(end_time),
                                selected_room,
                                name,
                                email,
                                description,
                                "Active"  # Status
                            ])
                            st.success(f"""
                            ✅ Booking confirmed!
                            - Booking ID: **{booking_id}**
                            - Room: **{selected_room}**
                            - Date: **{date.strftime('%Y-%m-%d')}**
                            - Time: **{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}**
                            """)
                        else:
                            st.error("Failed to save booking")

def cancel_booking():
    st.header("Cancel Booking")
    
    booking_id = st.number_input("Enter Booking ID", min_value=1000, max_value=9999)
    email = st.text_input("Enter Your Email (used for booking)")
    
    if st.button("Cancel Booking"):
        sheet = connect_to_gsheet()
        if not sheet:
            return
            
        records = sheet.get_all_records()
        
        for i, row in enumerate(records, start=2):  # Rows start at 2
            if (row["booking_id"] == booking_id and 
                row["email"].lower() == email.lower() and
                row["status"] == "Active"):
                
                sheet.update_cell(i, 9, "Cancelled")  # Update status column
                st.success(f"""
                ❌ Booking cancelled:
                - Room: {row['room']}
                - Date: {row['date']}
                - Time: {row['start_time']} to {row['end_time']}
                """)
                return
                
        st.error("No matching active booking found")

def view_bookings():
    st.header("Current Bookings")
    
    sheet = connect_to_gsheet()
    if not sheet:
        return
        
    all_bookings = sheet.get_all_records()
    active_bookings = [b for b in all_bookings if b["status"] == "Active"]
    
    if not active_bookings:
        st.info("No active bookings")
    else:
        # Create nice dataframe display
        df = pd.DataFrame(active_bookings)[["booking_id", "date", "start_time", "end_time", "room", "name"]]
        st.dataframe(
            df.style.set_properties(**{'text-align': 'left'}),
            hide_index=True,
            column_config={
                "booking_id": "Booking ID",
                "date": "Date",
                "start_time": "Start Time",
                "end_time": "End Time",
                "room": "Room",
                "name": "Booked By"
            }
        )

# --- MAIN APP ---
def main():
    st.set_page_config(
        page_title="Meeting Room Booking",
        page_icon=":calendar:",
        layout="wide"
    )
    
    st.title("Meeting Room Booking System")
    
    # Sidebar
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Options", 
        ["Book a Room", "Cancel Booking", "View Bookings"],
        label_visibility="collapsed"
    )
    
    st.sidebar.divider()
    st.sidebar.write(f"📍 Timezone: Asia/Kolkata")
    st.sidebar.write(f"🗓️ Today: {current_time_ist.strftime('%Y-%m-%d')}")
    st.sidebar.write(f"⏰ Current Time: {current_time_ist.strftime('%H:%M')}")
    
    # Main content
    if menu == "Book a Room":
        book_room()
    elif menu == "Cancel Booking":
        cancel_booking()
    elif menu == "View Bookings":
        view_bookings()

if __name__ == "__main__":
    import re  # Added for email validation
    main()
