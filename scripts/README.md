# JDM Car Rentals Scripts

This directory contains utility scripts for the JDM Car Rentals application.

## Administrative Notification Scripts

### Create Admin Notifications

This script generates notifications for admin users for all existing bookings. It's useful for populating admin notifications for bookings that were created before the admin notification functionality was implemented.

**Usage:**
```
# Navigate to the JDM_Car_Rentals root directory
cd /path/to/JDM_Car_Rentals

# Run the script
python scripts/create_admin_notifications.py
```

### Test Notifications

This script populates the system with test notifications for all users, including both regular users and admins. It creates various types of notifications, including booking status changes, payment status updates, and system notifications.

**Usage:**
```
# Navigate to the JDM_Car_Rentals root directory
cd /path/to/JDM_Car_Rentals

# Run the script
python scripts/test_notifications.py
```

## Database Scripts

### Create Notifications Table

If you're setting up the notification system for the first time and not using Flask-Migrate, you can execute this SQL script to create the necessary database table and indexes.

**Usage:**
```
# Option 1: Using the mysql command-line client
mysql -u your_username -p your_database < scripts/create_notifications_table.sql

# Option 2: Copy the contents of the script and execute it in your MySQL client
``` 