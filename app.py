import os
import tkinter as tk
from tkinter import filedialog, messagebox
from image_detector import ImageDetector
from alert_system import AlertSystem

print("Starting application...")

class MediaContentDetectionApp:
    def __init__(self, root):
        print("Initializing application...")
        self.root = root
        self.root.title("Media Content Detection System")
        self.root.geometry("600x400")
        
        print("Loading image detector...")
        try:
            self.image_detector = ImageDetector()
            print("Image detector loaded successfully")
        except Exception as e:
            print(f"Error loading image detector: {str(e)}")
            messagebox.showerror("Error", f"Failed to load image detector: {str(e)}")
        
        self.alert_system = AlertSystem()
        print("Alert system initialized")
        
        # Create UI elements
        print("Creating widgets...")
        self.create_widgets()
        print("Widgets created")
    
    def create_widgets(self):
        # Title
        tk.Label(self.root, text="Media Content Detection System", font=("Arial", 16)).pack(pady=10)
        
        # File selection frame
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=20, fill=tk.X, padx=20)
        
        tk.Button(file_frame, text="Select Image", command=self.process_image).pack(side=tk.LEFT, padx=10)
        tk.Button(file_frame, text="Select Audio", command=self.process_audio).pack(side=tk.LEFT, padx=10)
        tk.Button(file_frame, text="Select Video", command=self.process_video).pack(side=tk.LEFT, padx=10)
        
        # Results frame
        self.results_text = tk.Text(self.root, height=15, width=70)
        self.results_text.pack(pady=10, padx=20)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def process_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            self.status_var.set(f"Processing image: {os.path.basename(file_path)}")
            self.root.update()
            
            result = self.image_detector.detect_nsfw_content(file_path)
            
            # Update results area
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"File: {file_path}\n")
            self.results_text.insert(tk.END, f"Inappropriate content detected: {result['is_inappropriate']}\n")
            self.results_text.insert(tk.END, f"Confidence score: {result['confidence_score']:.4f}\n")
            
            # Generate alert if needed
            if result['is_inappropriate']:
                alert_id = self.alert_system.send_alert("image", file_path, result)
                self.results_text.insert(tk.END, f"\nALERT GENERATED: {alert_id}\n")
                messagebox.showwarning("Inappropriate Content", 
                                       "Inappropriate content detected in this image.\nAn alert has been generated.")
            
            self.status_var.set("Ready")
    
    def process_audio(self):
        # Placeholder for future audio processing
        messagebox.showinfo("Feature Not Implemented", 
                           "Audio detection will be implemented in the next phase.")
    
    def process_video(self):
        # Placeholder for future video processing
        messagebox.showinfo("Feature Not Implemented", 
                           "Video detection will be implemented in the next phase.")

if __name__ == "__main__":
    print("Creating Tkinter root...")
    root = tk.Tk()
    print("Root created, initializing app...")
    app = MediaContentDetectionApp(root)
    print("App initialized, starting mainloop...")
    root.mainloop()
    print("Mainloop finished - application closed")