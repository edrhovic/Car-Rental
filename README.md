# JDM Car Rentals

A car rental management system specializing in Japanese Domestic Market (JDM) vehicles.

## Features

- User registration and authentication
- Car booking and return functionality
- Payment processing
- User booking history
- Car reviews and ratings
- Admin panel for managing cars, bookings, users, and reviews

## Notification System

JDM Car Rentals now includes a comprehensive notification system that keeps users informed about their bookings and payments.

## Features

- Real-time notifications for booking status changes (pending, confirmed, completed, cancelled)
- Payment notifications (successful, failed, refunded)
- System notifications for offers and announcements
- Notification counts displayed in the navigation bar
- Ability to view all notifications and mark them as read

## For Users

Users can access their notifications in two ways:

1. **Notification Bell**: Click the bell icon in the top navigation bar to view recent notifications in a dropdown.
2. **Notifications Page**: Click "Notifications" in the user menu or "View All" in the dropdown to see all notifications.

## For Administrators

Notifications are automatically created when:

- A booking status is changed (via admin panel)
- A payment is processed, refunded, or fails
- System notifications can be added programmatically

### Testing Notifications

To generate test notifications for all users, run:

```
cd JDM_Car_Rentals
python scripts/test_notifications.py
```

### Creating the Database Table

If you're setting up the notification system for the first time and not using Flask-Migrate, run the following SQL script:

```
mysql -u your_username -p your_database < scripts/create_notifications_table.sql
```

Or copy the contents of `scripts/create_notifications_table.sql` into your MySQL client.

## Database Setup Instructions

### Setting up the MySQL Database

1. Install and open MySQL Workbench
2. Connect to your local MySQL server
3. Open the `database_setup.sql` script located in the project root
4. Execute the script to create the database, tables, and sample data

### Configuring the Application to Use Your Database

1. Open `app.py` in the project root
2. Modify the database connection string with your MySQL credentials:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://your_username:your_password@localhost/jdm_car_rentals'
```

Alternatively, you can set the DATABASE_URL environment variable:

```
# Windows (Command Prompt)
set DATABASE_URL=mysql+pymysql://your_username:your_password@localhost/jdm_car_rentals

# Windows (PowerShell)
$env:DATABASE_URL = "mysql+pymysql://your_username:your_password@localhost/jdm_car_rentals"

# Linux/macOS
export DATABASE_URL=mysql+pymysql://your_username:your_password@localhost/jdm_car_rentals
```

## Installation and Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database as described above

5. Run the application:
   ```
   python app.py
   ```

## Default Admin User

Username: admin  
Password: admin123

## License

This project is licensed under the MIT License. 