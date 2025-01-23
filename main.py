import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import queue
from src.services.vision_service import VisionAPIService, Receipt
from src.utils.config import get_debug_mode
import tkinter

class ReceiptProcessor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Add rotation state
        self.rotation_angle = 90  # Start with 90 degree rotation (counterclockwise)
        
        # Add receipt data storage
        self.current_receipt = None
        self.fields_to_display = [
            'vendor', 'invoice', 'bill_date', 'paid_date', 
            'payment_method', 'total_amount', 'item', 'project'
        ]
        
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
            height=700  # Reduced height for portrait orientation
        )
        self.camera_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")  # Stick to top
        
        # Create control panel frame at bottom of camera frame
        self.control_panel = ctk.CTkFrame(self.camera_frame)
        self.control_panel.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        # Create buttons in control panel
        self.rotate_button = ctk.CTkButton(
            self.control_panel,
            text="Rotate (R)",
            command=self.rotate_view
        )
        self.rotate_button.pack(side="left", padx=5, pady=5)
        
        self.save_button = ctk.CTkButton(
            self.control_panel,
            text="Save (Return)",
            command=self.save_image
        )
        self.save_button.pack(side="left", padx=5, pady=5)
        
        self.capture_button = ctk.CTkButton(
            self.control_panel,
            text="Capture (Spacebar)",
            command=self.capture_image
        )
        self.capture_button.pack(side="left", padx=5, pady=5)
        
        # Add status label below control panel
        self.status_label = ctk.CTkLabel(self.camera_frame, text="")
        self.status_label.grid(row=2, column=0, pady=(0, 10), sticky="ew")
        
        # Replace placeholder right panel content with scrollable frame
        self.right_scroll = ctk.CTkScrollableFrame(self.right_frame)
        self.right_scroll.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_rowconfigure(0, weight=1)
        
        # Create dictionary to store label widgets and entry fields
        self.field_labels = {}
        self.field_values = {}
        self.field_overrides = {}  # New dictionary for override entries
        
        # Create labels for each field
        for idx, field in enumerate(self.fields_to_display):
            label = ctk.CTkLabel(self.right_scroll, text=f"{field.replace('_', ' ').title()}:")
            label.grid(row=idx, column=0, padx=5, pady=5, sticky="e")
            
            value_label = ctk.CTkLabel(self.right_scroll, text="", width=200)
            value_label.grid(row=idx, column=1, padx=5, pady=5, sticky="w")
            
            # Add override entry field
            override_entry = ctk.CTkEntry(self.right_scroll, width=200)
            override_entry.grid(row=idx, column=2, padx=5, pady=5, sticky="w")
            
            self.field_labels[field] = label
            self.field_values[field] = value_label
            self.field_overrides[field] = override_entry
        
        # Add commit button
        self.commit_button = ctk.CTkButton(
            self.right_scroll,
            text="Commit to CSV",
            command=self.commit_to_datastore,
            state="disabled"
        )
        self.commit_button.grid(row=len(self.fields_to_display), column=0, 
                              columnspan=2, pady=20)
        
        # Bind keyboard shortcuts to main window
        self.bind('<space>', self.handle_space)
        self.bind('<Return>', self.handle_return)
        self.bind('r', self.handle_r)
        
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
                
                # Rotate image according to current rotation angle
                image = image.rotate(self.rotation_angle, expand=True)
                
                # Get the actual dimensions of the camera label
                preview_width = self.camera_label.winfo_width()
                preview_height = self.camera_label.winfo_height()
                
                # Calculate scaling while maintaining aspect ratio
                img_ratio = image.width / image.height
                preview_ratio = preview_width / preview_height
                
                if img_ratio > preview_ratio:
                    new_height = preview_height
                    new_width = int(preview_height * img_ratio)
                else:
                    new_width = preview_width
                    new_height = int(preview_width / img_ratio)
                
                # Resize image
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center horizontally but align to top vertically
                x_offset = (new_width - preview_width) // 2
                y_offset = 0  # Changed from centered to top-aligned
                image = image.crop((x_offset, y_offset, x_offset + preview_width, y_offset + preview_height))
                
                # Create CTkImage instead of PhotoImage
                photo = ctk.CTkImage(light_image=image, 
                                   dark_image=image,
                                   size=(preview_width, preview_height))
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
            # Show immediate feedback that capture was triggered
            self.status_label.configure(text="Capturing and analyzing image...")
            # Force update the display immediately
            self.status_label.update()
            
            # Clear all field values
            for value_label in self.field_values.values():
                value_label.configure(text="")
                value_label.update()  # Force immediate update of each field
            
            # Disable commit button while processing
            self.commit_button.configure(state="disabled")
            self.commit_button.update()  # Force immediate update of button
            
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                self.frame_queue.put(frame)  # Put it back if needed elsewhere
                
                # Rotate frame according to current rotation angle
                if self.rotation_angle == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif self.rotation_angle == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif self.rotation_angle == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # Convert to BGR for consistent color handling
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Convert frame to bytes
                _, buffer = cv2.imencode('.jpg', frame_bgr)
                image_bytes = buffer.tobytes()
                
                # DEBUG: Save the exact image being sent to vision service if debug mode is enabled
                if get_debug_mode():
                    from datetime import datetime
                    import os
                    os.makedirs('./output/saved_images', exist_ok=True)
                    debug_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    with open(f'./output/saved_images/debug_sent_{debug_timestamp}.jpg', 'wb') as f:
                        f.write(image_bytes)
                
                # Analyze the receipt
                receipt = self.vision_service.analyze_receipt(image_bytes)
                
                # Update UI with receipt data
                self.status_label.configure(text=f"Vendor: {receipt.vendor}, Total: {receipt.total_amount}")
                print("Receipt analyzed:", receipt)
                
                # Store the receipt and update UI
                self.current_receipt = receipt
                self.update_receipt_display()
                
                # Clear the message after 2 seconds
                self.after(2000, lambda: self.status_label.configure(text=""))
            else:
                self.status_label.configure(text="Error: No frame available")
        except Exception as e:
            print(f"Error capturing image: {e}")
            self.status_label.configure(text=f"Error capturing image: {e}")
            self.after(2000, lambda: self.status_label.configure(text=""))
    
    def save_image(self):
        """Save the current frame to the output/saved_images folder"""
        try:
            import os
            from datetime import datetime
            
            # Create output/saved_images directory if it doesn't exist
            os.makedirs('./output/saved_images', exist_ok=True)
            
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                self.frame_queue.put(frame)  # Put it back
                
                # Rotate frame according to current rotation angle
                if self.rotation_angle == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif self.rotation_angle == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif self.rotation_angle == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'./output/saved_images/receipt_{timestamp}.jpg'
                
                # Save the image
                cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                
                self.status_label.configure(text=f"Image saved: {filename}")
                self.after(2000, lambda: self.status_label.configure(text=""))
            else:
                self.status_label.configure(text="Error: No frame available")
        except Exception as e:
            print(f"Error saving image: {e}")
            self.status_label.configure(text=f"Error saving image: {e}")
            self.after(2000, lambda: self.status_label.configure(text=""))
    
    def rotate_view(self):
        """Rotate the preview by 90 degrees clockwise"""
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.status_label.configure(text=f"Rotation: {self.rotation_angle}°")
        self.after(2000, lambda: self.status_label.configure(text=""))
    
    def on_closing(self):
        """Clean up resources on window close"""
        self.camera_running = False
        if self.camera is not None:
            self.camera.release()
        self.quit()

    def update_receipt_display(self):
        """Update the right panel with receipt data"""
        if self.current_receipt:
            for field in self.fields_to_display:
                value = getattr(self.current_receipt, field)
                # Reset text color to default and update value
                self.field_values[field].configure(
                    text=str(value),
                    text_color=("black", "white")  # (light mode, dark mode)
                )
            self.commit_button.configure(state="normal")

    def commit_to_datastore(self):
        """Save the current receipt data to CSV file"""
        import csv
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs('./output', exist_ok=True)
        csv_file = './output/receipts.csv'
        file_exists = os.path.isfile(csv_file)
        
        try:
            with open(csv_file, mode='a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields_to_display)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Write receipt data, using overrides where present
                receipt_dict = {}
                for field in self.fields_to_display:
                    override_value = self.field_overrides[field].get().strip()
                    if override_value:  # Use override if present
                        receipt_dict[field] = override_value
                    else:  # Otherwise use extracted value
                        receipt_dict[field] = getattr(self.current_receipt, field)
                
                writer.writerow(receipt_dict)
                
                # Grey out the field values and clear overrides
                for field in self.fields_to_display:
                    self.field_values[field].configure(text_color="grey")
                    self.field_overrides[field].delete(0, 'end')  # Clear override entries
                
                # Disable commit button and show success message
                self.commit_button.configure(state="disabled")
                self.status_label.configure(text="Receipt committed to CSV")
                self.after(2000, lambda: self.status_label.configure(text=""))
                
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            self.status_label.configure(text=f"Error saving to CSV: {e}")
            self.after(2000, lambda: self.status_label.configure(text=""))

    def is_override_focused(self):
        """Check if any override entry has focus"""
        focused = self.focus_get()
        print(f"Focused widget: {focused}, type: {type(focused)}")  # Debug print
        return isinstance(focused, (ctk.CTkEntry, tkinter.Entry))  # Check for both types

    def handle_space(self, event):
        """Handle spacebar press only if not in override fields"""
        focused = self.is_override_focused()
        print(f"Space pressed, override focused: {focused}")  # Debug print
        if not focused:
            self.capture_image()

    def handle_return(self, event):
        """Handle return press only if not in override fields"""
        focused = self.is_override_focused()
        print(f"Return pressed, override focused: {focused}")  # Debug print
        if not focused:
            self.save_image()

    def handle_r(self, event):
        """Handle R press only if not in override fields"""
        focused = self.is_override_focused()
        print(f"R pressed, override focused: {focused}")  # Debug print
        if not focused:
            self.rotate_view()

if __name__ == "__main__":
    app = ReceiptProcessor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()