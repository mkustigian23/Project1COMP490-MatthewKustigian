# Project 1 - COMP490 - Matthew Kustigian

This repository contains two main components developed for COMP490:

The project has evolved through sprints:
- **Sprint 1**: Basic speech-to-text transcription from audio files/live mic
- **Sprint 2**: Room booking API client with authentication and CRUD operations
- **Sprint 3**: Voice-enabled agent using LangChain + Ollama (local LLM) to query reservations naturally (read-only for now)

## Features

### Speech-to-Text Transcription
- Supports live microphone input and audio files
- Uses Google Speech Recognition (free tier)
- Handles ambient noise adjustment and timeouts
- Basic error handling and retry logic

### Room Booking Client & Voice Agent
- Authenticate with email/password
- List currently available meeting rooms
- Book a room for a specified time slot
- View personal booking history
- Cancel upcoming bookings
- Voice interface (Sprint 3): Ask natural-language questions like  
  "Do I have any bookings today?"  
  "What rooms are available right now?"  
  "When is my reservation for Room A?"
- Uses local Ollama LLM (e.g. granite-1b) for offline/privacy-focused operation

## Setup

### Prerequisites
- Python 3.10+
- Git
- (Optional for voice mode) Ollama installed and running locally with a model pulled (e.g. `ollama pull ibm/granite4:1b-h`)
- Microphone for voice input (optional)


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