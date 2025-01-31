# Smart Home Energy Management System (SHEMS)

This repository contains the implementation of **SHEMS (Smart Home Energy Management System)**, developed as part of the **Principles of Database Systems (CS-GY 6083)** course project. The system is designed to manage and analyze smart home energy consumption using a relational database model and a web-based interface.

## Project Overview

SHEMS is a database-driven application that enables users to **monitor, manage, and analyze** their household energy consumption. The system is built using **PostgreSQL** for database management and **Django** for backend services, with a frontend designed using **HTML, Bootstrap CSS, and JavaScript**.

## Features

### 🔹 Database Design & Management
- **Relational Schema & ER Diagram**: A structured schema to efficiently store addresses, customers, service locations, devices, and energy consumption data.
- **Normalization**: Database design follows **BCNF (Boyce-Codd Normal Form)** to reduce redundancy and improve integrity.
- **Sample SQL Queries**: Includes optimized queries for **data retrieval and visualization**.

### 🔹 Web-Based Interface
- **🔑 Authentication System**: User login with password hashing using **Blowfish encryption**.
- **🛠 CRUD Operations**: Manage service locations and enrolled smart devices.
- **📊 Data Visualization**: Graphs and charts powered by **Plotly** to track energy consumption trends.
- **🔒 Security Measures**: Protection against **SQL Injection**, **Cross-Site Scripting (XSS)**, and **CSRF Attacks**.
- **🔄 Transaction & Concurrency Handling**: Atomic transactions for customer and address insertion.

### 🔹 Data Processing & Analytics
- **📡 Smart Device Monitoring**: Real-time tracking of energy consumption from enrolled devices.
- **💰 Energy Price Analysis**: Stores and analyzes hourly energy prices by zip code.
- **⏳ Time-Series Data Processing**: Handles high-frequency device data efficiently.

## Visualization & Reports

SHEMS provides **interactive graphs** to help users understand their energy consumption:

1. 📈 **Device Type vs. Energy Consumption**
2. ⏳ **Time-based Energy Consumption per Service Location**
3. ⚡ **Actual vs. Average Energy Usage Comparison**
4. 🌍 **Energy Consumption Trends Across Devices & Locations**
5. 🏷 **Average Energy Prices by Zip Code**

## Tech Stack

- **Backend**: Django (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, Bootstrap CSS, JavaScript
- **Libraries**: Plotly (Data Visualization), Crypt (Password Hashing)

## Authors

- **Sumedh Parvatikar** (`sp7479`)
- **Jaya Sabarish Reddy Remala** (`jr6421`)

Please look up into the Final_Report for additional information.

