Blood Bank Management System
Overview

The Blood Bank Management System is a web-based application developed using Python, Flask, SQLite, HTML, and CSS. It helps manage blood donations, blood requests, inventory tracking, emergency blood matching, and transfusion history.

The project also demonstrates the practical application of Data Structures and Algorithms (DSA) in a real-world healthcare system.

---

Features

- Blood Donation Management
- Blood Request Processing
- Blood Inventory Tracking
- Emergency Blood Matching
- Expired Blood Monitoring
- Recent Transfusion History
- Dashboard with Inventory Statistics

---

Technologies Used

Backend

- Python
- Flask
- SQLite

Frontend

- HTML
- CSS

Database

- SQLite Database (bloodbank.db)

---

DSA Concepts Used

Hash Map

Used for fast blood-group indexing and inventory lookup.

Time Complexity: O(1) Average Lookup

Queue

Used to allocate the oldest blood units first (FIFO principle).

Time Complexity: O(1)

Merge Sort

Used to sort blood units according to expiry dates.

Time Complexity: O(n log n)

---

System Modules

Dashboard

Displays:

- Total Blood Units
- Expired Blood Units
- Blood Group Inventory
- Recent Transfusions

Donate Blood

Allows donors to register blood donations and automatically calculates expiry dates.

Request Blood

Processes patient requests and allocates compatible blood units.

Inventory

Shows available blood units and expiry information.

Emergency Match

Finds compatible blood groups during emergencies.

History

Maintains a record of all blood transfusions.

---

Future Improvements

- User Authentication and Authorization
- SMS and Email Notifications
- Mobile Application Development
- QR/Barcode Tracking of Blood Units
- Cloud Database Integration
- Real-Time Inventory Updates
- AI-Based Blood Demand Prediction

---

How to Run the Project

1. Clone the repository.
2. Install required packages:

pip install -r requirements.txt

3. Run the application:

python app.py

4. Open your browser and visit:

http://127.0.0.1:5000

---

Authors

Developed as a Data Structures and Algorithms (DSA) Project.

Department of Biomedical Engineering
Addis Ababa University
