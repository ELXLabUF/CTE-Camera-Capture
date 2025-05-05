# CTE-Camera-Capture

A simple Python desktop application that captures images from your webcam every 10 seconds while a timer runs, then sends the captured images in batches to the OpenAI GPT-4o API for detailed analysis. After processing all batches, it synthesizes a comprehensive description of the entire video session.

---

## Features

- **Start/Stop Button:** Control the capture session with a single button.
- **Live Timer:** Displays elapsed time in `MM:SS` format during capture.
- **Webcam Capture:** Captures an image every 10 seconds at specified resolution.
- **Batch Processing:** Sends images in batches of 10 to OpenAI API for detailed descriptions.
- **Final Synthesis:** Combines batch descriptions into a comprehensive final analysis.
- **Local Desktop GUI:** Built entirely with Python's Tkinter for easy local use.
- **Threaded Design:** Keeps GUI responsive during capture and processing.

---

## Requirements

- Python 3.7+
- OpenCV
- Requests

---

## Dependencies

The application requires the following Python packages:

- `tkinter` (usually included with standard Python installations)
- `opencv-python` (for webcam capture)
- `requests` (for HTTP requests to OpenAI API)

---

## Installation

1. Clone this repository:
```
git clone https://github.com/ELXLabUF/CTE-Camera-Capture.git
cd CTE-Camera-Capture
```
2. Install dependencies:
```
pip install opencv-python requests
```

---

## Setup

1. Open the Python script (`camera_capture.py`).
2. Replace the placeholder API key with your OpenAI API key: `OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"`

---

## Usage

Run the app:
```
python camera_capture.py
```
- Click **Start** to begin capturing images and start the timer.
- The app captures one image every 10 seconds.
- Click **Stop** to end capture and start processing images.
- After processing, the final comprehensive analysis will be saved to `video_analysis.txt`.
- Status messages and the timer are displayed in the GUI.

---

## Notes

- The app batches images in groups of 10 for API requests to respect OpenAI's limits.
- The final description synthesizes all batch analyses into a detailed, multi-paragraph report.
- Webcam resolution is set to 640x480 by default for compatibility; adjust in the script if needed.
- The app is designed for local use and does not require internet access except for API calls.
- Ensure your webcam is connected and not used by other applications.

---

## Troubleshooting

- **Webcam not opening:**  
  Make sure no other application is using the webcam. Try restarting your computer.

- **API errors:**  
  Verify your OpenAI API key and internet connection.

- **Missing dependencies:**  
  Install required Python packages and system libraries as noted above.

---
