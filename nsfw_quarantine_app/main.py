import sys
print(f'PYTHON EXECUTABLE: {sys.executable}')
print('PYTHONPATH:')
for p in sys.path:
    print('   ', p)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from dotenv import load_dotenv
from alert_mailer import send_quarantine_alert
import sys
import numpy as np
import cv2
from PIL import Image, ImageTk
from logger import setup_logger
from detector import ContentDetector
from threading import Thread
import webbrowser
from datetime import datetime
import io

# Load environment variables from .env at startup
load_dotenv()

logger = setup_logger()

# Define colors for theming
COLORS = {
    'primary': '#1f7db3',     # Blue
    'secondary': '#f9f9f9',  # Light gray
    'accent': '#e74c3c',     # Red
    'text': '#333333',       # Dark gray
    'success': '#2ecc71',    # Green
    'warning': '#f39c12',    # Orange
    'background': '#e6f0fa', 
    'header': '#095580',     # Dark blue
    'button_text': '#000000', # Black for button text
    'disabled': '#bbbbbb',   # Gray for disabled elements
}

# Define fonts for consistent typography
FONTS = {
    'base': ('Segoe UI', 10),
    'header': ('Segoe UI', 18, 'bold'),
    'section': ('Segoe UI', 12, 'bold'),
    'label': ('Segoe UI', 10),
    'button': ('Segoe UI', 10, 'bold'),
    'small': ('Segoe UI', 8),
    'mono': ('Consolas', 9),
}

class NSFWQuarantineApp:
    def __init__(self):
        self.logger = logger
        self.selected_files = []
        self.detector = ContentDetector()
        self.scanning = False
        self.preview_image = None
        self.scan_results = {}  # Always initialize scan_results
        
        # Create main window
        self.window = tk.Tk()
        self.window.title('Obscene Media Detection Tool')
        self.window.geometry('900x700')
        self.window.minsize(800, 600)
        self.window.configure(bg=COLORS['background'])
        
        # Set app icon if available
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys._MEIPASS
            else:
                # Running as script
                app_path = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(app_path, 'app_icon.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Could not set app icon: {e}")
        
        # Configure custom styles
        self.configure_styles()
        
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with logo and title
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Application title
        title = ttk.Label(header_frame, 
                         text='Obscene Media Detection Tool', 
                          style='Header.TLabel')
        title.pack(side=tk.LEFT, pady=10)
        
        # Version and info
        version_label = ttk.Label(header_frame, 
                                 text='v1.0.0 | Hackathon Project', 
                                 style='Version.TLabel')
        version_label.pack(side=tk.RIGHT, pady=10)
        
        # Split into two main sections (left and right panels)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for file selection and controls
        left_panel = ttk.Frame(content_frame, style='Panel.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7))
        
        # File selection section
        file_section = ttk.LabelFrame(left_panel, text='File Selection', style='Section.TLabelframe')
        file_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # Files listbox with scrollbar
        file_list_frame = ttk.Frame(file_section)
        file_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.file_list = tk.Listbox(file_list_frame, 
                                   activestyle='none',
                                   selectbackground=COLORS['primary'],
                                   selectforeground='white',
                                   background=COLORS['secondary'],
                                   highlightthickness=0,
                                   bd=1,
                                   font=FONTS['label'])
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_list.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Scrollbar for the listbox
        list_scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=self.file_list.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=list_scrollbar.set)
        
        # Buttons frame
        btn_frame = ttk.Frame(file_section)
        btn_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Create custom colored buttons
        self.browse_btn = ttk.Button(btn_frame, text='Browse Files', command=self.browse_files, style='Primary.TButton')
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        self.scan_btn = ttk.Button(btn_frame, text='Scan Selected', command=self.scan_files, state='disabled', style='Action.TButton')
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text='Clear All', command=self.clear_files, state='disabled')
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status and progress section
        status_section = ttk.LabelFrame(left_panel, text='Scan Status', style='Section.TLabelframe')
        status_section.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Status indicator
        status_frame = ttk.Frame(status_section)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_icon = ttk.Label(status_frame, text='🔍', font=('Segoe UI', 16), background=COLORS['background'])
        self.status_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        status_right = ttk.Frame(status_frame)
        status_right.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(status_right, text='Ready to scan', style='Status.TLabel')
        self.status_label.pack(anchor='w', pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_right, variable=self.progress_var, maximum=100, style='Accent.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X)
        
        # Progress details
        self.progress_details = ttk.Label(status_right, text='0/0 files processed', style='Detail.TLabel')
        self.progress_details.pack(anchor='w', pady=(5, 0))
        
        # Right panel for preview and logs
        right_panel = ttk.Frame(content_frame, style='Panel.TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(7, 0))
        
        # Preview section
        preview_section = ttk.LabelFrame(right_panel, text='Preview', style='Section.TLabelframe')
        preview_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # Preview canvas with placeholder
        self.preview_frame = ttk.Frame(preview_section, style='Preview.TFrame')
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_canvas = tk.Canvas(self.preview_frame, bg=COLORS['secondary'], highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.no_preview_label = ttk.Label(self.preview_canvas, text='No preview available', style='Placeholder.TLabel', font=FONTS['label'])
        self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Log section
        log_section = ttk.LabelFrame(right_panel, text='Activity Log', style='Section.TLabelframe', height=200)
        log_section.pack(fill=tk.BOTH, expand=False, padx=5)
        
        # Log area with scrollbar
        log_frame = ttk.Frame(log_section)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, state='disabled',
                              font=FONTS['mono'],
                              bg=COLORS['secondary'],
                              padx=5, pady=5,
                              highlightthickness=0,
                              bd=1)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Footer with application info
        footer_frame = ttk.Frame(main_container, style='Footer.TFrame')
        footer_frame.pack(fill=tk.X, pady=(15, 0))
        
        footer_text = ttk.Label(footer_frame, 
                               text='2025 KernelKlashKrew Team | Designed for hackathon', 
                               style='Footer.TLabel', font=FONTS['small'])
        footer_text.pack(side=tk.LEFT)
        
        # Configure tags for log coloring
        self.log_text.tag_configure('info', foreground=COLORS['text'])
        self.log_text.tag_configure('success', foreground=COLORS['success'])
        self.log_text.tag_configure('warning', foreground=COLORS['warning'])
        self.log_text.tag_configure('error', foreground=COLORS['accent'])
        self.log_text.tag_configure('bold', font=('Consolas', 9, 'bold'))
        
        # Add initial log message
        self.log_message('Application started - ready to scan files', 'info')
        
        # About button
        about_button = ttk.Button(footer_frame, text='About', command=self.show_about, style='TButton')
        about_button.pack(side=tk.RIGHT, padx=10)
        # Consider using 'Primary.TButton' or 'Action.TButton' for more visual feedback if desired
    
    def browse_files(self):
        """Handle file browsing and selection."""
        file_types = (
            ('All Files', '*.*'),
            ('Image Files', '*.jpg;*.jpeg;*.png;*.gif;*.bmp'),
            ('Text Files', '*.txt;*.md;*.csv;*.log')   
        )
        
        files = filedialog.askopenfilenames(
            title='Choose Files to Scan',
            filetypes=file_types
        )
        
        if files:
            # Verify files exist before adding them
            valid_files = []
            for file in files:
                if os.path.exists(file):
                    valid_files.append(file)
                else:
                    self.log_message(f"File not found: {os.path.basename(file)}", 'error')
            
            if not valid_files:
                messagebox.showwarning("No Valid Files", "None of the selected files could be found.")
                return
                
            self.selected_files = valid_files
            self.file_list.delete(0, tk.END)
            
            # Add files to listbox with just filenames (not full paths)
            for file in self.selected_files:
                filename = os.path.basename(file)
                self.file_list.insert(tk.END, filename)
                
            # Enable controls
            self.scan_btn['state'] = 'normal'
            self.clear_btn['state'] = 'normal'
            self.status_label['text'] = 'Ready to scan'
            self.progress_details['text'] = f'0/{len(self.selected_files)} files processed'
            
            # Log the action
            self.log_message(f'Selected {len(self.selected_files)} files for scanning', 'info')
            
            # Load preview of first file (blurred by default)
            if self.selected_files:
                self.file_list.selection_set(0)
                self.load_image_preview(self.selected_files[0], is_safe=None)
    
    def configure_styles(self):
        """Configure custom ttk styles for the application."""
        style = ttk.Style()
        
        # Configure default styles for all frames and labels
        style.configure('TFrame', background=COLORS['background'])
        style.configure('TLabel', background=COLORS['background'], foreground=COLORS['text'], font=FONTS['label'])
        style.configure('TButton', font=FONTS['button'], padding=6)
        style.configure('TLabelframe', background=COLORS['background'])
        style.configure('TLabelframe.Label', background=COLORS['background'], foreground=COLORS['primary'], font=FONTS['section'])
        
        # Custom styles for various elements
        style.configure('Header.TLabel', font=FONTS['header'], foreground=COLORS['header'], background=COLORS['background'])
        style.configure('Version.TLabel', font=FONTS['small'], foreground='gray', background=COLORS['background'])
        style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'), foreground=COLORS['primary'], background=COLORS['background'])
        style.configure('Detail.TLabel', font=FONTS['small'], foreground='gray', background=COLORS['background'])
        style.configure('Footer.TLabel', font=FONTS['small'], foreground='gray', background=COLORS['background'])
        style.configure('Placeholder.TLabel', foreground='gray', background=COLORS['secondary'], font=FONTS['label'])
        
        # Button styles
        style.configure('Primary.TButton', font=FONTS['button'], background=COLORS['primary'], foreground=COLORS['button_text'], borderwidth=1, focusthickness=3, focuscolor=COLORS['header'])
        style.configure('Action.TButton', font=FONTS['button'], background=COLORS['accent'], foreground=COLORS['button_text'], borderwidth=1, focusthickness=3, focuscolor=COLORS['accent'])
        style.map('Primary.TButton',
            foreground=[('active', COLORS['button_text']), ('!disabled', COLORS['button_text'])],
            background=[('active', '#2a8bc4'), ('!disabled', COLORS['primary'])],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )
        style.map('Action.TButton',
            foreground=[('active', COLORS['button_text']), ('!disabled', COLORS['button_text'])],
            background=[('active', '#f85c4c'), ('!disabled', COLORS['accent'])],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )
        style.map('TButton',
            foreground=[('disabled', COLORS['disabled']), ('!disabled', COLORS['text'])],
            background=[('active', COLORS['secondary']), ('!disabled', COLORS['background'])]
        )
        
        # Progress bar style
        style.configure('Accent.Horizontal.TProgressbar', background=COLORS['accent'])
        
        # Panel and section styles
        style.configure('Panel.TFrame', relief='flat', background=COLORS['secondary'])
        style.configure('Preview.TFrame', relief='solid', borderwidth=1, background=COLORS['secondary'])
        style.configure('Section.TLabelframe', borderwidth=1, relief='solid', background=COLORS['background'])
        style.configure('Footer.TFrame', background=COLORS['background'], relief='flat', borderwidth=0)
        
        # Add tooltip style (future use)
        style.configure('Tooltip.TLabel', background='#ffffe0', foreground=COLORS['text'], font=FONTS['small'], borderwidth=1, relief='solid')

    def on_file_select(self, event):
        """Handle selection of a file in the file list."""
        try:
            # Get selected index
            selection = self.file_list.curselection()
            if not selection:
                return
                
            # Get the file path
            file_idx = selection[0]
            file_path = self.selected_files[file_idx]
            
            # Check if file has been quarantined and use that path instead
            original_path = file_path
            display_path = self.detector.get_quarantine_path(file_path) or file_path
            
            # Log the path being used
            if display_path != original_path:
                self.log_message(f"Using quarantined path: {os.path.basename(display_path)}", 'info')
            
            # Check if file still exists
            if not os.path.exists(display_path):
                self.log_message(f"File not found: {os.path.basename(display_path)}", 'error')
                self.preview_canvas.delete("all")
                self.no_preview_label.configure(text="File not found")
                self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
                return
            
            # Check if this file has been scanned yet
            is_safe = None  # Default is blurred (unscanned)
            
            # If scanning is completed, determine safety from scan results
            if not self.scanning and hasattr(self, 'scan_results'):
                if file_path in self.scan_results:
                    is_safe = not self.scan_results[file_path]
            
            # Load and display the preview with appropriate blur
            self.load_image_preview(display_path, is_safe)
            
        except Exception as e:
            self.log_message(f"Error showing preview: {e}", 'error')

    def apply_blur(self, img, blur_radius=21):
        """Apply Gaussian blur to an image.
        
        Note: blur_radius must be a positive odd integer for OpenCV's GaussianBlur.
        """
        # Ensure blur_radius is a positive odd integer
        blur_radius = max(1, blur_radius)
        if blur_radius % 2 == 0:  # If even
            blur_radius += 1  # Make it odd
            
        # Convert PIL Image to numpy array (for OpenCV)
        img_np = np.array(img) 
        
        # Convert RGB to BGR (OpenCV uses BGR)
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(img_np, (blur_radius, blur_radius), 0)
        
        # Convert back to RGB and then to PIL Image
        blurred = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
        return Image.fromarray(blurred)
    
    def load_image_preview(self, file_path, is_safe=None):
        """Load and display a preview of an image or text file.
        
        Parameters:
        - file_path: Path to the file
        - is_safe: If None, show as unscanned. If True, show safe. If False, show flagged/quarantined.
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Clear previous preview
            self.preview_canvas.delete("all")
            if hasattr(self, 'preview_photo'):
                del self.preview_photo
            
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.txt', '.md', '.csv', '.log']:
                # For text files, do not display any preview, just show placeholder
                self.no_preview_label.configure(text="No preview available")
                self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
                return
            elif ext in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']:
                # For audio files, show audio placeholder
                self.no_preview_label.configure(text="Audio file – no preview available")
                self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
                return

            # Default: image preview logic (unchanged)
            img = Image.open(file_path)
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            if canvas_width <= 1:
                canvas_width = 300
            if canvas_height <= 1:
                canvas_height = 300
            img_width, img_height = img.size
            ratio = min(canvas_width/img_width, canvas_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            scan_key = file_path
            if scan_key in self.scan_results:
                is_flagged, _ = self.scan_results[scan_key]
                is_safe = not is_flagged
            apply_blur = True
            blur_radius = 125
            if is_safe is True:
                apply_blur = False
            elif is_safe is None:
                blur_radius = 125
            if apply_blur:
                img = self.apply_blur(img, blur_radius=blur_radius)
            self.preview_photo = ImageTk.PhotoImage(img)
            self.preview_canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.preview_photo, anchor='center'
            )
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024
            file_info = f"{file_name} ({file_size:.1f} KB, {img_width}×{img_height})"
            self.preview_canvas.create_text(
                10, 10, text=file_info, anchor='nw',
                fill='black', font=('Segoe UI', 8)
            )
            if is_safe is False:
                overlay_id = self.preview_canvas.create_rectangle(
                    0, 0, canvas_width, canvas_height,
                    fill=COLORS['accent'], stipple='gray25', outline=''
                )
                self.preview_canvas.tag_lower(overlay_id)
                warning_msg = "NSFW CONTENT DETECTED\nImage has been quarantined"
                self.preview_canvas.create_text(
                    canvas_width//2, canvas_height//2,
                    text=warning_msg,
                    font=('Segoe UI', 14, 'bold'),
                    fill='white',
                    justify=tk.CENTER
                )
            elif is_safe is True:
                self.preview_canvas.create_text(
                    canvas_width - 10, 10,
                    text="✓ SAFE",
                    font=('Segoe UI', 10, 'bold'),
                    fill=COLORS['success'],
                    anchor='ne'
                )
            else:
                self.preview_canvas.create_text(
                    canvas_width - 10, 10,
                    text="? UNSCANNED",
                    font=('Segoe UI', 10),
                    fill='gray',
                    anchor='ne'
                )
            self.no_preview_label.place_forget()
        except Exception as e:
            self.preview_canvas.delete("all")
            if isinstance(e, FileNotFoundError):
                self.no_preview_label.configure(text="File not found")
            else:
                self.no_preview_label.configure(text="Cannot preview this file")
            self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
            self.log_message(f"Error loading preview: {e}", 'error')

    def update_file_list(self):
        """Update the file list UI to match the current selected_files."""
        self.file_list.delete(0, tk.END)
        for file in self.selected_files:
            filename = os.path.basename(file)
            self.file_list.insert(tk.END, filename)
            
        # Update button states
        if self.selected_files:
            self.scan_btn['state'] = 'normal'
            self.clear_btn['state'] = 'normal'
        else:
            self.scan_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'disabled'
            
        # Update status details
        self.progress_details['text'] = f'0/{len(self.selected_files)} files processed'
    
    def clear_files(self):
        """Clear all selected files from the list."""
        self.selected_files = []
        self.file_list.delete(0, tk.END)
        self.scan_btn['state'] = 'disabled'
        self.clear_btn['state'] = 'disabled'
        self.status_label['text'] = 'Ready to scan'
        self.status_icon['text'] = '🔍'
        self.progress_var.set(0)
        self.progress_details['text'] = '0/0 files processed'
        
        # Clear scan results
        self.scan_results = {}
        # The detector maintains its own quarantine map
        
        # Clear preview
        self.preview_canvas.delete("all")
        self.no_preview_label.configure(text="No preview available")
        self.no_preview_label.place(relx=0.5, rely=0.5, anchor='center')
        if hasattr(self, 'preview_photo'):
            del self.preview_photo
            
        self.log_message('File list cleared', 'info')

    def log_message(self, message, level='info'):
        """Add a message to the log area with appropriate styling."""
        # Log to file
        if level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'success':
            self.logger.info(f"SUCCESS: {message}")
            
        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert into log text widget
        self.log_text['state'] = 'normal'
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'bold')
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text['state'] = 'disabled'
        self.log_text.see(tk.END)
    
    def scan_files(self):
        """Start scanning the selected files in a separate thread."""
        if self.scanning or not self.selected_files:
            return
        
        self.scanning = True
        
        # Initialize scan results dictionary
        self.scan_results = {}
        
        # Update UI state
        self.browse_btn['state'] = 'disabled'
        self.scan_btn['state'] = 'disabled'
        self.clear_btn['state'] = 'disabled'
        self.progress_var.set(0)
        self.status_icon['text'] = '⚙️'
        self.status_label['text'] = 'Scanning in progress...'
        
        def scan_thread():
            total_files = len(self.selected_files)
            flagged_files = 0
            safe_files = 0
            
            self.log_message(f"Starting scan of {total_files} file{'s' if total_files != 1 else ''}", 'info')
            
            try:
                # Filter out non-existent files before scanning
                valid_files = []
                for file_path in self.selected_files:
                    if os.path.exists(file_path):
                        valid_files.append(file_path)
                    else:
                        self.log_message(f'File not found: {os.path.basename(file_path)}', 'error')
                
                # Update selected files to only include existing files
                if len(valid_files) < len(self.selected_files):
                    removed_count = len(self.selected_files) - len(valid_files)
                    self.selected_files = valid_files
                    self.log_message(f'Removed {removed_count} missing files from the scan list', 'warning')
                    
                    # Update file list in UI
                    self.window.after(0, self.update_file_list)
                
                # If no valid files, stop scanning
                if not self.selected_files:
                    self.log_message("No valid files to scan", 'error')
                    return
                
                # Start scanning valid files
                for i, file_path in enumerate(self.selected_files):
                    # Double-check file still exists before scanning
                    if not os.path.exists(file_path):
                        self.log_message(f'File disappeared during scan: {os.path.basename(file_path)}', 'error')
                        continue
                    
                    # Update progress
                    progress = (i + 1) / total_files * 100
                    self.progress_var.set(progress)
                    self.progress_details['text'] = f'{i + 1}/{total_files} files processed'
                    
                    # Update file list selection to show current file
                    self.window.after(0, lambda idx=i: self.file_list.selection_clear(0, tk.END) 
                                      or self.file_list.selection_set(idx) 
                                      or self.file_list.see(idx))
                    
                    # Load preview of current file with blur (before analysis)
                    self.window.after(0, lambda path=file_path: self.load_image_preview(path, is_safe=None))
                    
                    # Scan file
                    filename = os.path.basename(file_path)
                    self.log_message(f'Scanning {filename}...', 'info')
                    is_flagged, reasons = self.detector.scan_file(file_path)
                    
                    # Store result in our scan_results dictionary
                    self.scan_results[file_path] = (is_flagged, reasons)
                    
                    if is_flagged:
                        flagged_files += 1
                        success, msg = self.detector.quarantine_file(file_path)
                        status = 'Quarantined' if success else 'Failed to quarantine'
                        
                        # If successfully quarantined, get the new path directly from the detector
                        if success:
                            # Get quarantine path directly
                            quarantine_path = msg  # The msg is now the destination path
                            # Add the scan result for the quarantined path as well
                            self.scan_results[quarantine_path] = (is_flagged, reasons)
                            # Show blurred preview with warning using the NEW quarantine path
                            self.window.after(0, lambda path=quarantine_path: self.load_image_preview(path, is_safe=False))
                            self.log_message(f"File quarantined to: {os.path.basename(quarantine_path)}", 'info')
                            # --- ALERT EMAIL SYSTEM (pure Python) ---
                            try:
                                sender = os.environ.get('ALERT_MAIL_SENDER')
                                recipient = os.environ.get('ALERT_MAIL_RECIPIENT')
                                smtp_user = os.environ.get('ALERT_MAIL_USER')
                                smtp_pass = os.environ.get('ALERT_MAIL_PASS')
                                if not (sender and recipient and smtp_user and smtp_pass):
                                    self.log_message('[ALERT ERROR] Email env vars missing (ALERT_MAIL_SENDER, ALERT_MAIL_RECIPIENT, ALERT_MAIL_USER, ALERT_MAIL_PASS)', 'error')
                                else:
                                    send_quarantine_alert(file_path, reasons, quarantine_path, sender, recipient, smtp_user, smtp_pass)
                            except Exception as alert_exc:
                                self.log_message(f"[ALERT ERROR] {alert_exc}", 'error')
                        else:
                            # Use original path if quarantine failed
                            self.window.after(0, lambda path=file_path: self.load_image_preview(path, is_safe=False))
                        
                        # Log results
                        self.log_message(f'⚠️ {filename} - {status}', 'warning')
                    else:
                        safe_files += 1
                        # Show unblurred preview for safe images
                        self.window.after(0, lambda path=file_path: self.load_image_preview(path, is_safe=True))
                        self.log_message(f'✅ {filename} - Safe', 'success')
                    # Always log scan reasons (including transcript)
                    for reason in reasons:
                        self.log_message(f'   → {reason}', 'info')
                
                # Scan complete
                scan_result = f"Scan complete: {safe_files} safe, {flagged_files} quarantined"
                self.log_message(scan_result, 'bold')
                
                # Update status indicators
                if flagged_files > 0:
                    self.status_icon['text'] = '⚠️'
                    self.status_label['text'] = f'{flagged_files} inappropriate files quarantined'
                else:
                    self.status_icon['text'] = '✅'
                    self.status_label['text'] = 'All files are safe'
                    
            except Exception as e:
                self.log_message(f"Error during scan: {e}", 'error')
                self.status_icon['text'] = '❌'
                self.status_label['text'] = 'Scan failed - see log for details'
            finally:
                # Re-enable controls
                self.scanning = False
                self.window.after(0, lambda: self.browse_btn.configure(state='normal'))
                self.window.after(0, lambda: self.scan_btn.configure(state='normal' if self.selected_files else 'disabled'))
                self.window.after(0, lambda: self.clear_btn.configure(state='normal' if self.selected_files else 'disabled'))
        
        Thread(target=scan_thread, daemon=True).start()
    
    def show_about(self):
        """Show about dialog with application information"""
        # About window
        about_window = tk.Toplevel(self.window)
        about_window.title("About NSFW Content Scanner")
        about_window.geometry("500x400")
        about_window.transient(self.window)  # Make it transient to main window
        about_window.grab_set()  # Make it modal
        about_window.configure(bg=COLORS['background'])
        
        # Center window
        about_window.update_idletasks()
        width = about_window.winfo_width()
        height = about_window.winfo_height()
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Content
        content_frame = ttk.Frame(about_window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        about_text = (
            "NSFW Content Scanner\n\n"
            "Version 1.0\n\n"
            "This application helps identify and quarantine potentially inappropriate "
            "content, protecting users from accidental exposure to NSFW imagery, Hate Speech and Profanity.\n\n"
            "Key Features:\n"
            "\u2022 Deep learning content detection\n"
            "\u2022 NSFW classification\n"
            "\u2022 Automatic file quarantine\n"
            "\u2022 Image preview with safety blur\n\n"
            "2025"
        )
        
        about_label = ttk.Label(
            content_frame, 
            text=about_text,
            justify=tk.CENTER,
            font=('Segoe UI', 10),
            wraplength=450
        )
        about_label.pack(pady=20)
        
        # Close button
        close_btn = ttk.Button(
            content_frame, 
            text="Close", 
            command=about_window.destroy,
            style='Primary.TButton'
        )
        close_btn.pack(pady=20)

    def run(self):
        """Run the main application window."""
        self.window.mainloop()

if __name__ == '__main__':
    app = NSFWQuarantineApp()
    app.run()
