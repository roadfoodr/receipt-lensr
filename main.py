import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import queue

class ReceiptProcessor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure main window
        self.title("Receipt Processor")
        self.geometry("1280x960")
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create frame for camera preview
        self.camera_frame = ctk.CTkFrame(self)
        self.camera_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create label for camera preview
        self.camera_label = ctk.CTkLabel(self.camera_frame, text="")
        self.camera_label.grid(row=0, column=0, padx=10, pady=10)
        
        # Create capture button
        self.capture_button = ctk.CTkButton(
            self.camera_frame, 
            text="Capture (Spacebar)", 
            command=self.capture_image
        )
        self.capture_button.grid(row=1, column=0, padx=10, pady=10)
        
        # Add status label
        self.status_label = ctk.CTkLabel(self.camera_frame, text="")
        self.status_label.grid(row=2, column=0, padx=10, pady=10)
        
        # Bind spacebar to capture
        self.bind('<space>', lambda event: self.capture_image())
        
        # Initialize camera variables
        self.camera = None
        self.camera_running = False
        self.frame_queue = queue.Queue(maxsize=1)
        
        # Start camera
        self.start_camera()
        
    def start_camera(self):
        """Initialize and start the camera feed"""
        try:
            self.camera = cv2.VideoCapture(0)  # Try first camera
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
                
            # Set resolution (adjust as needed)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            self.camera_running = True
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.update_camera)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
            # Start frame update
            self.update_frame()
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            self.status_label.configure(text=f"Error: {e}")
    
    def update_camera(self):
        """Camera capture thread function"""
        while self.camera_running:
            ret, frame = self.camera.read()
            if ret:
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # If queue full, remove old frame
                if self.frame_queue.full():
                    self.frame_queue.get()
                self.frame_queue.put(frame)
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        try:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                image = Image.fromarray(frame)
                
                # Resize to fit window while maintaining aspect ratio
                display_size = (1024, 768)  # Larger preview size
                image.thumbnail(display_size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
            
            # Schedule next update
            self.after(10, self.update_frame)
            
        except Exception as e:
            print(f"Error updating frame: {e}")
            self.status_label.configure(text=f"Error: {e}")
    
    def capture_image(self):
        """Capture the current frame"""
        print("Capture method called")  # Debug print
        try:
            if not self.frame_queue.empty():
                print("Frame queue not empty")  # Debug print
                frame = self.frame_queue.get()
                self.frame_queue.put(frame)  # Put frame back in queue first
                
                # Update status in UI
                self.status_label.configure(text="Image captured!")
                print("Status label updated")  # Debug print
                
                # Clear the message after 2 seconds
                self.after(2000, lambda: self.status_label.configure(text=""))
                
                print("Image captured!")  # Console feedback
            else:
                print("Frame queue was empty")  # Debug print
                self.status_label.configure(text="Error: No frame available")
        except Exception as e:
            print(f"Error capturing image: {e}")
            self.status_label.configure(text=f"Error capturing image: {e}")
            self.after(2000, lambda: self.status_label.configure(text=""))
    
    def on_closing(self):
        """Clean up resources on window close"""
        self.camera_running = False
        if self.camera is not None:
            self.camera.release()
        self.quit()

if __name__ == "__main__":
    app = ReceiptProcessor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()