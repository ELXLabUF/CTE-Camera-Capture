# Imports
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import cv2
import os
import base64
import requests
import re

# Configuration
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Capture parameters
CAPTURE_INTERVAL = 10  # seconds between captures
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
MAX_IMAGES_PER_REQUEST = 10

def create_user_folder(username):
    """Create user-specific folder structure"""
    base_dir = os.path.join(os.getcwd(), username)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def get_sorted_images(folder_path):
    """Get sorted list of image files by creation time"""
    return sorted([
        f for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ], key=lambda x: os.path.getctime(os.path.join(folder_path, x)))

def encode_image(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_batch_description(image_batch):
    """Get comprehensive description for a batch of images"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    content = [{
        "type": "text",
        "text": (
            '''You are a video analysis application.
            You will receive images that are frames from a camera feed every 10 seconds.
            The video is capturing a participant in a Maker activity that involves different disciplines.
            Your task is to analyze the frames as a whole image and give a brief but detailed description 
            of what is happening in the video and provide a clear, concise, and technically accurate 
            summary of the task being performed. Detect what items and components were used.
            Include results of the activity. Use human-like language that is direct and professional, 
            avoiding robotic or overly formal phrasing.
            For each set of frames, identify and describe the following:
            1. The main components visible (e.g., breadboard, LEDs, resistors, jumper wires, Arduino boards).
            2. The specific actions being taken 
            (e.g., connecting an LED to a digital pin, inserting a resistor, uploading code to Arduino).
            3. The logical sequence of steps, if discernible, and any technical purpose behind them 
            (e.g., current limiting, circuit testing, prototyping).
            4. Any potential issues or best practices observed 
            (e.g., correct resistor orientation, secure connections, possible wiring errors).
            5. The overall objective of the task, if it can be inferred from the frames.
            Your analysis should be factual, objective, and focused on the technical aspects
            of the work shown in the frames. Avoid storytelling, or unnecessary commentary.
            Present your findings as if you are documenting the process for a technical audience or for training purposes.'''
        )
    }]

    for img in image_batch:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img}"}
        })

    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1500
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"API Error: {response.text}"
    except Exception as e:
        return f"Request Failed: {str(e)}"

def get_final_description(batch_descriptions):
    """Synthesize all batch descriptions into final analysis"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    content = [{
        "type": "text",
        "text": (
            '''You are a tool that synthesizes a batch of video analysis descriptions.
            You will receive multiple descriptions of frames taken from a camera capture recording a Maker activity.
            Your task is to synthesize all the descriptions and create an output consisting of answers to the three 
            questions:
            1. "What was the activity that the participant of the study was performing; what did they do?"
            2. "What items and components were used in that activity?"
            3. "What were the results of the activity?".
            Avoid storytelling, use human-like language with detailed description of the activity, 
            components used, and results.
            Use second-person language and it doesn\'t have to be complete sentences.'''
        )
    }]

    for idx, desc in enumerate(batch_descriptions):
        content.append({
            "type": "text",
            "text": f"Batch {idx+1} Analysis:\n{desc}"
        })

    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 3000
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"Final API Error: {response.text}"
    except Exception as e:
        return f"Final Request Failed: {str(e)}"

class WebcamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Analyzer")

        # Username input
        self.username_label = ttk.Label(root, text="Enter Username:")
        self.username_label.pack(pady=5)

        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(root, textvariable=self.username_var, width=20)
        self.username_entry.pack(pady=5)
        self.username_var.trace_add('write', self.validate_username)

        self.control_btn = ttk.Button(root, text="Start", command=self.toggle_capture, state='disabled')
        self.control_btn.pack(pady=10)

        self.timer_label = ttk.Label(root, text="00:00", font=('Helvetica', 24))
        self.timer_label.pack(pady=5)

        self.status = ttk.Label(root, text="Ready")
        self.status.pack(pady=10)

        # Capture control
        self.is_capturing = False
        self.capture_thread = None
        self.processing_thread = None
        self.img_counter = 0
        self.cap = None
        self.timer_id = None
        self.start_time = None

        # User folder and paths
        self.user_folder = None
        self.output_dir = None
        self.output_file = None

    def validate_username(self, *args):
        """Enable Start button only if username is entered"""
        if self.username_var.get().strip():
            self.control_btn.config(state='normal')
        else:
            self.control_btn.config(state='disabled')

    def toggle_capture(self):
        if not self.is_capturing:
            self.start_capture()
        else:
            self.stop_capture()

    def start_capture(self):
        username = self.username_var.get().strip()
        self.user_folder = create_user_folder(username)
        self.output_dir = os.path.join(self.user_folder, "Captured_Images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.user_folder, "video_analysis.txt")

        self.username_entry.config(state='disabled')
        self.is_capturing = True
        self.control_btn.config(text="Stop")
        self.status.config(text="Capturing...")
        self.img_counter = 0
        self.start_time = time.time()
        self.update_timer()
        self.capture_thread = threading.Thread(target=self.run_capture_loop, daemon=True)
        self.capture_thread.start()

    def stop_capture(self):
        # Unlock the username field
        self.username_entry.config(state='normal')
        self.is_capturing = False
        self.control_btn.config(text="Start")
        self.status.config(text="Processing images...")
        
        # Stop the timer
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_captured_images, daemon=True)
        self.processing_thread.start()

    def update_timer(self):
        if self.is_capturing:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            # Schedule next update
            self.timer_id = self.root.after(1000, self.update_timer)

    def run_capture_loop(self):
        try:
	    # Change the value to 0 to use built-in camera; 1 to use external camera 
            self.cap = cv2.VideoCapture(1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open webcam")
                self.is_capturing = False
                return

            while self.is_capturing:
                ret, frame = self.cap.read()
                if not ret:
                    break

                img_name = os.path.join(self.output_dir, f"image_{self.img_counter:03d}.jpg")

                cv2.imwrite(img_name, frame)
                self.img_counter += 1

                # Wait for capture interval
                start_time = time.time()
                while (time.time() - start_time) < CAPTURE_INTERVAL:
                    if not self.is_capturing:
                        break
                    time.sleep(0.1)

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if self.cap and self.cap.isOpened():
                self.cap.release()

    def process_captured_images(self):
        try:
            images = get_sorted_images(self.output_dir)

            if not images:
                messagebox.showinfo("Info", "No images captured")
                self.status.config(text="Ready")
                self.username_entry.config(state='normal')
                return

            batch_descriptions = []
            for i in range(0, len(images), MAX_IMAGES_PER_REQUEST):
                batch_images = images[i:i+MAX_IMAGES_PER_REQUEST]
                encoded_batch = [encode_image(os.path.join(self.output_dir, img)) for img in batch_images]
                description = get_batch_description(encoded_batch)
                
                if not description.startswith("Error"):
                    batch_descriptions.append(description)

            if batch_descriptions:
                final_analysis = get_final_description(batch_descriptions)
                with open(self.output_file, "w") as f:
                    f.write("COMPREHENSIVE VIDEO ANALYSIS\n\n")
                    f.write(final_analysis)
                
                messagebox.showinfo("Success", f"Analysis saved to {self.output_file}")
                self.status.config(text="Analysis complete")

                # Extract answers using regex
                matches = re.findall(
                    r"\d+\. \*\*(.*?)\*\*\s*(.*?)(?=\n\d+\. \*\*|$)",
                    final_analysis,
                    re.DOTALL
                )
                activity = matches[0][1].strip() if len(matches) > 0 else ""
                tools = matches[1][1].strip() if len(matches) > 1 else ""
                results = matches[2][1].strip() if len(matches) > 2 else ""
                username = self.username_var.get().strip()
                
                # Body JSON for post request.
                data = {
                    "user": {
                        "username": username  # Use entered username
                    },
                    "reflection": {
                        "entryId": -1,
                        "project": "My Maker Project",
                        "content": [
                            {"fieldName": "Activities", "content": activity},
                            {"fieldName": "Use", "content": tools},
                            {"fieldName": "Results", "content": results}
                        ]
                    }
                }
                
                # Send post request to the CT server that handles DB access.
                # requests.post("http://157.230.225.94:8081/api/user/ccr", json=data)
                requests.post("http://knowledgetracker.duckdns.org:8081/api/user/ccr", json=data)
            else:
                messagebox.showwarning("Warning", "No valid descriptions generated")
                self.status.config(text="Processing failed")
            self.username_entry.config(state='normal')
        
        except Exception as e:
            messagebox.showerror("Processing Error", str(e))
            self.status.config(text="Processing error")
            self.username_entry.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()
