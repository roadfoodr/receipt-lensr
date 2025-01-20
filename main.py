import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import queue
from src.services.vision_service import VisionAPIService, Receipt

class ReceiptProcessor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure main window
        self.title("Receipt Processor")
        self.geometry("1600x900")  # Landscape window
        
        # Configure grid layout (two columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Left panel fixed width
        self.grid_columnconfigure(1, weight=1)  # Right panel expands
        
        # Create left frame for camera preview (fixed width)
        self.camera_frame = ctk.CTkFrame(self, width=500)  # Slightly narrower
        self.camera_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.camera_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Configure camera frame grid
        self.camera_frame.grid_rowconfigure(0, weight=1)  # Preview expands vertically
        self.camera_frame.grid_columnconfigure(0, weight=1)
        
        # Create right frame for controls and data
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # Create label for camera preview with fixed portrait dimensions
        self.camera_label = ctk.CTkLabel(
            self.camera_frame,
            text="",
            width=500,  # Fixed width
            height=800  # Fixed height for portrait orientation
        )
        self.camera_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")  # Stick to top
        
        # Create control panel frame at bottom of camera frame
        self.control_panel = ctk.CTkFrame(self.camera_frame)
        self.control_panel.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Create capture button in control panel
        self.capture_button = ctk.CTkButton(
            self.control_panel,
            text="Capture (Spacebar)",
            command=self.capture_image
        )
        self.capture_button.pack(pady=5)
        
        # Add status label in control panel
        self.status_label = ctk.CTkLabel(self.control_panel, text="")
        self.status_label.pack(pady=5)
        
        # Add placeholder text in right panel
        self.right_label = ctk.CTkLabel(
            self.right_frame,
            text="Data and controls will appear here"
        )
        self.right_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Bind spacebar to capture
        self.bind('<space>', lambda event: self.capture_image())

        # Initialize the Vision API Service without explicit api_key
        # It will load from config automatically
        self.vision_service = VisionAPIService(use_anthropic=False)
        
        # Add debug print to verify key
        # print(f"Vision service initialized with key: {self.vision_service.api_key[:8]}...") # Only show first 8 chars for security
        
        # Initialize camera variables
        self.camera = None
        self.camera_running = False
        self.frame_queue = queue.Queue(maxsize=1)
        
        # Start camera
        self.start_camera()
        
    def start_camera(self):
        """Initialize and start the camera feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera resolution to a more suitable size
            # Using 1080p resolution in landscape (will be rotated)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
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
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.frame_queue.full():
                    self.frame_queue.get()
                self.frame_queue.put(frame)
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        try:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                                
                # Convert to PIL Image
                image = Image.fromarray(frame)
                
                # Get the actual dimensions of the camera label
                preview_width = self.camera_label.winfo_width()
                preview_height = self.camera_label.winfo_height()
                
                # Calculate scaling while maintaining aspect ratio
                img_ratio = image.width / image.height
                preview_ratio = preview_width / preview_height
                
                if img_ratio > preview_ratio:
                    # Image is wider relative to its height than preview area
                    new_height = preview_height
                    new_width = int(preview_height * img_ratio)
                else:
                    # Image is taller relative to its width than preview area
                    new_width = preview_width
                    new_height = int(preview_width / img_ratio)
                
                # Resize image
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center the image
                x_offset = (new_width - preview_width) // 2
                y_offset = (new_height - preview_height) // 2
                image = image.crop((x_offset, y_offset, x_offset + preview_width, y_offset + preview_height))
                
                # Create photo image and update label
                photo = ImageTk.PhotoImage(image)
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
            
            # Schedule next update
            self.after(10, self.update_frame)
            
        except Exception as e:
            print(f"Error updating frame: {e}")
            self.status_label.configure(text=f"Error: {e}")
    
    def capture_image(self):
        """Capture the current frame and analyze it using the Vision API"""
        try:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                self.frame_queue.put(frame)  # Put it back if needed elsewhere
                
                # Convert frame to bytes
                _, buffer = cv2.imencode('.jpg', frame)
                image_bytes = buffer.tobytes()
                
                # Analyze the receipt
                receipt = self.vision_service.analyze_receipt(image_bytes)
                
                # Update UI with receipt data
                self.status_label.configure(text=f"Vendor: {receipt.vendor}, Total: {receipt.total_amount}")
                print("Receipt analyzed:", receipt)
                
                # Clear the message after 2 seconds
                self.after(2000, lambda: self.status_label.configure(text=""))
            else:
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