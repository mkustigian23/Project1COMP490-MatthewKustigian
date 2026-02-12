# Project 1 - COMP490 - Matthew Kustigian

This repository contains two main components developed for COMP490:

1. A **speech-to-text transcription tool** using audio processing and transcription APIs
2. A **Python client** for interacting with a Room Booking API (including authentication, room listing, booking, and cancellation)

## Features

### Speech-to-Text Transcription (Original Project)
- Converts audio files to text using speech recognition
- Supports various audio formats
- Includes linting and unit testing

### Room Booking Client
- Authenticate with email/password
- List currently available meeting rooms
- Book a room for a specified time slot (15-minute duration recommended)
- View personal booking history
- Cancel upcoming bookings
- Demonstrates conflict detection (attempting to book the same room/time twice fails)

## Setup

### Prerequisites
- Python 3.10+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mkustigian23/Project1COMP490-MatthewKustigian.git
   cd Project1COMP490-MatthewKustigian
   
2. Install Dependencies 
    ```bash
   pip install -r requirements.txt
   

Required GitHub Secrets:

SERVER_URL
EMAIL
PASSWORD

These secrets are used to create the .env file during CI runs.