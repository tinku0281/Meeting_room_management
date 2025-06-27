import streamlit as st
import datetime
import csv
from datetime import timedelta
import random 
import pandas as pd
import re
import pytz

# Set the timezone to "Asia/Kolkata" (Indian Standard Time)
ist = pytz.timezone('Asia/Kolkata')

# Get the current time in IST
current_time_ist = datetime.datetime.now(ist)
ctif = current_time_ist.strftime("%y-%m-%d %H:%M:%S")

# Define file paths for storing booking data
booking_data_file = "booking_data.csv"

# Load existing booking data from the CSV file
try:
    with open(booking_data_file, "r") as file:
        reader = csv.DictReader(file)
        booking_data = {"room_bookings": {}, "room_availability": {}}

        for row in reader:
            booking_id = int(row["booking_id"])
            booking_data["room_bookings"][booking_id] = {
                "booking_id": booking_id,
                "date": row["date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "room": row["room"],
                "name": row["name"],
                "description": row["description"],
            }

            # Update room availability data
            if row["date"] not in booking_data["room_availability"]:
                booking_data["room_availability"][row["date"]] = {}
            if row["room"] not in booking_data["room_availability"][row["date"]]:
                booking_data["room_availability"][row["date"]][row["room"]] = []
            booking_data["room_availability"][row["date"]][row["room"]].append(
                (row["start_time"], row["end_time"])
            )

except FileNotFoundError:
    booking_data = {"room_bookings": {}, "room_availability": {}}

# Utility Functions
def is_valid_time(time_str):
    try:
        datetime.datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def is_room_available(date, start_time, end_time, room):
    if date not in booking_data["room_availability"]:
        return True

    if room not in booking_data["room_availability"][date]:
        return True

    for booking in booking_data["room_availability"][date][room]:
        b_start_time, b_end_time = booking
        if not (end_time <= b_start_time or start_time >= b_end_time):
            return False

    return True

# Generate a random 4-digit booking ID
def generate_random_booking_id():
    return random.randint(1000, 9999)

# Book a Room
room_capacity = {
    "HIMALAYA - Basement": 20,
    "NEELGIRI - Ground Floor": 7,
    "ARAVALI  - Ground Floor": 7,
    "KAILASH - 1 Floor": 7,
    "ANNAPURNA - 1 Floor": 4,
    "EVEREST  - 2 Floor": 12,
    "KANANACJUNGA - 2 Floor": 7,
    "SHIVALIK - 3 Floor": 4,
    "TRISHUL - 3 Floor": 4,
    "DHAULAGIRI - 3 Floor": 7,
}

def book_room():
    st.header("Book a Room")
    date = st.date_input("Select the Date:", min_value=current_time_ist.date(), value=None)
    current_date = current_time_ist.date()
    if date:
        office_start_time = datetime.time(8, 0)
        office_end_time = datetime.time(20, 0)
        start_times = [office_start_time]
        while start_times[-1] < office_end_time:
            next_time = (datetime.datetime.combine(date, start_times[-1]) + timedelta(minutes=15)).time()
            start_times.append(next_time)
        
        start_time = st.selectbox("Select the Start Time:", start_times, index=None)
        current_time = current_time_ist.time()
        if start_time:
            if (date == current_date and start_time < current_time):
                st.warning("Start time should be from current date and time.")
            else:
                end_of_day = min(office_end_time, datetime.time(23, 59))
                available_end_times = [datetime.datetime.combine(date, start_time) + timedelta(minutes=i) for i in range(15, (end_of_day.hour - start_time.hour) * 60 + 1, 15)]
                formatted_end_times = [et.strftime('%H:%M:%S') for et in available_end_times]
                end_time = st.selectbox("Select the End Time:", formatted_end_times, index=None)
                if end_time:
                    available_room_options = []
                    for room, capacity in room_capacity.items():
                        if is_room_available(str(date), str(start_time), str(end_time), room):
                            available_room_options.append(f"{room} (Capacity: {capacity})")
                    
                    if not available_room_options:
                        st.warning("Rooms are not available during this time.")
                    else:
                        st.info("Available Rooms")
                        room_choice = st.selectbox("Select a Room:", available_room_options, index=None)
                        if room_choice:
                            st.subheader('Enter Booking Details')
                            selected_room = room_choice.split(" (Capacity: ")[0]
                            description = st.text_input("Enter Meeting Title:")
                            name = st.text_input("Enter your Name:")
                            
                            if not name or not description:
                                st.warning("All details are mandatory.")
                            else:
                                if st.button("Book Room"):
                                    booking_id = generate_random_booking_id()
                                    booking_data["room_bookings"][booking_id] = {
                                        "date": str(date),
                                        "start_time": str(start_time),
                                        "end_time": str(end_time),
                                        "room": selected_room,
                                        "name": name,
                                        "description": description,
                                    }
                                    if str(date) not in booking_data["room_availability"]:
                                        booking_data["room_availability"][str(date)] = {}
                                    if selected_room not in booking_data["room_availability"][str(date)]:
                                        booking_data["room_availability"][str(date)][selected_room] = []
                                    booking_data["room_availability"][str(date)][selected_room].append((str(start_time), str(end_time)))
                                    with open(booking_data_file, "w", newline="") as file:
                                        fieldnames = [
                                            "booking_id",
                                            "date",
                                            "start_time",
                                            "end_time",
                                            "room",
                                            "name",
                                            "description",
                                        ]
                                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                                        writer.writeheader()
                                        for booking_id, booking_info in booking_data["room_bookings"].items():
                                            writer.writerow(
                                                {
                                                    "booking_id": booking_id,
                                                    "date": booking_info["date"],
                                                    "start_time": booking_info["start_time"],
                                                    "end_time": booking_info["end_time"],
                                                    "room": booking_info["room"],
                                                    "name": booking_info["name"],
                                                    "description": booking_info["description"],
                                                }
                                            )
                                    
                                    st.success(f"Booking successful! Your booking ID is {booking_id}.")
                                
def is_upcoming(booking, current_datetime):
    date_str = booking["date"]
    time_str = booking["start_time"]
    booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    booking_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
    booking_datetime = datetime.datetime.combine(booking_date, booking_time)
    current_datetime = datetime.datetime.strptime(current_datetime, '%y-%m-%d %H:%M:%S')
    return booking_datetime > current_datetime

# Cancel Room Reservation
def cancel_room():
    st.header("Cancel Room Reservation")

    booked_rooms = list(booking_data["room_bookings"].values())

    if not booked_rooms:
        st.warning("There are no existing room reservations to cancel.")
        return

    current_datetime = ctif
    upcoming_reservations = [booking for booking in booked_rooms if is_upcoming(booking, current_datetime)]

    if not upcoming_reservations:
        st.warning("No upcoming bookings to cancel.")
        return

    st.subheader("Select the reservation to cancel:")
    selected_reservation = st.selectbox("Upcoming Reservations", [f"Booking ID {booking_id}" for booking_id in booking_data["room_bookings"].keys() if is_upcoming(booking_data["room_bookings"][booking_id], current_datetime)], index=None)

    if selected_reservation:
        user_email_to_cancel = st.text_input("Enter Registered Mail used for booking:")

        if user_email_to_cancel:
            user_email_to_cancel = user_email_to_cancel.lower()
            if st.button("Cancel Reservation"):
                selected_booking_id = int(selected_reservation.split()[-1].strip())

                if selected_booking_id in booking_data["room_bookings"]:
                    reservation = booking_data["room_bookings"][selected_booking_id]
                    room = reservation["room"]
                    date = reservation["date"]
                    start_time = reservation["start_time"]
                    end_time = reservation["end_time"]

                    formatted_start_time = str(start_time)
                    formatted_end_time = str(end_time)
                    room_availability = booking_data["room_availability"]

                    if date in room_availability and room in room_availability[date]:
                        room_availability[date][room] = [
                            booking
                            for booking in room_availability[date][room]
                            if (formatted_start_time, formatted_end_time)
                            != (booking[0], booking[1])
                        ]

                    if user_email_to_cancel == reservation["email"].lower():
                        booking_data["room_bookings"].pop(selected_booking_id)

                        with open(booking_data_file, "w", newline="") as file:
                            fieldnames = [
                                "booking_id",
                                "date",
                                "start_time",
                                "end_time",
                                "room",
                                "name",
                                "description",
                            ]
                            writer = csv.DictWriter(file, fieldnames=fieldnames)
                            writer.writeheader()
                            for booking_id, booking_info in booking_data["room_bookings"].items():
                                writer.writerow(
                                    {
                                        "booking_id": booking_id,
                                        "date": booking_info["date"],
                                        "start_time": booking_info["start_time"],
                                        "end_time": booking_info["end_time"],
                                        "room": booking_info["room"],
                                        "name": booking_info["name"],
                                        "description": booking_info["description"],
                                    }
                                )

                        st.success(f"Reservation (Booking ID {selected_booking_id}) has been cancelled.")
                    else:
                        st.warning("Email address does not match. Cancellation failed.")

# View Reservations
def view_reservations():
    st.header("View Bookings")

    booked_rooms = list(booking_data["room_bookings"].values())

    if not booked_rooms:
        st.warning("There are no existing room reservations to view.")
    else:
        current_datetime = datetime.datetime.strptime(ctif, '%y-%m-%d %H:%M:%S')
        past_bookings = []
        upcoming_bookings = []

        for booking in booked_rooms:
            date_str = booking["date"]
            time_str = booking["start_time"]

            booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
            booking_datetime = datetime.datetime.combine(booking_date, booking_time)

            if booking_datetime < current_datetime:
                past_bookings.append(booking)
            else:
                upcoming_bookings.append(booking)

        past_bookings = sorted(past_bookings, key=lambda x: (x["date"], x["start_time"]))
        upcoming_bookings = sorted(upcoming_bookings, key=lambda x: (x["date"], x["start_time"]))

        tab1, tab2 = st.tabs(["Upcoming Bookings", "Booking History"])
        
        with tab1:
            st.subheader("Upcoming Bookings")
            if not upcoming_bookings:
                st.warning("No upcoming bookings.")
            else:
                upcoming_reservations_df = pd.DataFrame(upcoming_bookings)
                upcoming_reservations_df = upcoming_reservations_df.drop(columns=["email", "description"])
                upcoming_reservations_df.columns = ["Booking ID", "Date", "Start Time", "End Time", "Venue", "Booked by"]
                st.table(upcoming_reservations_df.assign(hack='').set_index('hack'))

        with tab2:
            st.subheader("Booking History (Past Bookings)")
            if not past_bookings:
                st.warning("No past bookings.")
            else:
                past_reservations_df = pd.DataFrame(past_bookings)
                past_reservations_df = past_reservations_df.drop(columns=["email", "description"])
                past_reservations_df.columns = ["Booking ID", "Date", "Start Time", "End Time", "Venue", "Booked by"]
                st.table(past_reservations_df.assign(hack='').set_index('hack'))

# Streamlit App
st.set_page_config(
    page_title="Meeting Room Booking",
    page_icon=":calendar:",
    initial_sidebar_state="expanded",
)

st.title("Sugam Group - Meeting Room Booking System")

date = current_time_ist.date()
time1 = current_time_ist.time()
current_time1 = f"{time1.hour:02d}:{time1.minute:02d}"

st.sidebar.button('Timezone 📍 Asia/Kolkata')
st.sidebar.button(f"Today's Date 🗓️ {date}")
st.sidebar.button(f"Current Time ⏰ {current_time1}")

# Sidebar menu
menu_choice = st.sidebar.selectbox("Menu", ["Book a Room", "Cancel Booking", "View Bookings"])

if menu_choice == "Book a Room":
    book_room()
elif menu_choice == "Cancel Booking":
    cancel_room()
elif menu_choice == "View Bookings":
    view_reservations()
