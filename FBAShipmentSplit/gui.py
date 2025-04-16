import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import json 
from pdf_processor import process_shipment, process_single_pdf_document 

# --- Constants ---
BG_COLOR = "#f9f9f9"
LOG_BG_COLOR = "#f3f4f6"
LOG_TEXT_COLOR = "#111827"
FOOTER_TEXT_COLOR = "#9ca3af"
CONFIG_FILE = "config.json" 

class FBASplitterApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("FBA Label splitter by sku") 
        self.master.geometry("600x500") # Adjusted height
        self.master.resizable(False, False) # Disable resizing
        
        self.master.configure(bg=BG_COLOR)
        self.pack(fill=tk.BOTH, expand=True) 

        self.config = self._load_config()
        self.config['usage_count'] = self.config.get('usage_count', 0) + 1
        self._save_config() 
        self.initial_dir = self.config.get('last_folder', os.path.dirname(os.path.abspath(sys.argv[0]))) 

        self.selected_paths_or_folder = None 
        self.selection_type = "None" 
        self.display_path = tk.StringVar() 

        self._configure_styles()
        self._create_widgets()
        self._update_stats_display() 

    def _configure_styles(self):
        """Configure ttk styles."""
        style = ttk.Style(self.master)
        try:
            if sys.platform == "darwin": style.theme_use('aqua') 
            elif sys.platform == "win32": style.theme_use('vista')
            else: style.theme_use('clam')
        except tk.TclError:
            print("Default ttk theme will be used.") 
            
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TButton', padding=6, font=('Helvetica', 11))
        style.configure('Copy.TButton', padding=(2, 2), font=('Helvetica', 9)) 
        style.configure('TEntry', padding=5)
        style.configure('TLabel', background=BG_COLOR, font=('Helvetica', 11))
        style.configure('Footer.TLabel', background=BG_COLOR, foreground=FOOTER_TEXT_COLOR, font=('Helvetica', 10))
        style.configure('Stats.TLabel', background=BG_COLOR, foreground=FOOTER_TEXT_COLOR, font=('Helvetica', 9)) 
        style.configure('Header.TLabel', background=BG_COLOR, font=('Helvetica', 12, 'bold'))
        style.configure('Status.TLabel', background=BG_COLOR, font=('Helvetica', 11, 'bold'))
        style.configure('Action.TButton', font=('Helvetica', 12, 'bold'), padding=(10, 8)) 

    def _load_config(self):
        """Loads configuration from JSON file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    # Handle empty file case
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {} 
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading config file ({CONFIG_FILE}): {e}. Using defaults.")
            return {} 

    def _save_config(self):
        """Saves current configuration to JSON file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, CONFIG_FILE)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config file ({CONFIG_FILE}): {e}")

    def _create_widgets(self):
        """Create all the UI widgets using grid layout."""
        content_frame = ttk.Frame(self, padding="10 10 10 10", style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)
        # Row 1 (Output section) should expand vertically now
        content_frame.rowconfigure(1, weight=1) 

        # --- Section 1: Input Selection ---
        input_section = ttk.Frame(content_frame, style='TFrame')
        input_section.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        # Configure columns for centering the button frame
        input_section.columnconfigure(0, weight=1) 
        input_section.columnconfigure(1, weight=0) # Button frame column
        input_section.columnconfigure(2, weight=1)

        # Buttons Frame - Centered using grid placement
        select_buttons_frame = ttk.Frame(input_section, style='TFrame')
        # Place the frame in the middle column (col 1)
        select_buttons_frame.grid(row=0, column=1, pady=(5, 5)) 
        
        self.select_files_button = ttk.Button(select_buttons_frame, text="Select File(s)", 
                                              command=self.select_files, width=15) 
        self.select_files_button.pack(side=tk.LEFT, padx=(0, 5)) 
        
        self.select_folder_button = ttk.Button(select_buttons_frame, text="Select Folder", 
                                               command=self.select_folder, width=15)
        self.select_folder_button.pack(side=tk.LEFT, padx=5) 

        # Path Entry Frame 
        path_frame = ttk.Frame(input_section, style='TFrame')
        # Place below buttons, spanning all columns for width
        path_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(5, 0)) 
        path_frame.columnconfigure(1, weight=1) 
        
        ttk.Label(path_frame, text="Selected:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.path_entry = ttk.Entry(path_frame, textvariable=self.display_path, state='readonly', width=60) 
        self.path_entry.grid(row=0, column=1, sticky="ew")

        # --- Section 2: Output --- (Keyword section removed)
        output_section = ttk.Frame(content_frame, style='TFrame')
        output_section.grid(row=1, column=0, sticky="nsew", pady=(10, 0)) 
        output_section.rowconfigure(1, weight=1) 
        output_section.columnconfigure(0, weight=1) 

        # Status Header Frame (Label + Copy Button)
        status_header_frame = ttk.Frame(output_section, style='TFrame')
        status_header_frame.grid(row=0, column=0, sticky="ew")
        status_header_frame.columnconfigure(1, weight=1) 
        
        ttk.Label(status_header_frame, text="Status Log", style='Status.TLabel').grid(row=0, column=0, sticky="w")
        
        self.copy_log_button = ttk.Button(status_header_frame, text="Copy Log", 
                                          command=self.copy_log_to_clipboard, style='Copy.TButton', width=8)
        self.copy_log_button.grid(row=0, column=2, sticky="e", padx=(5,0)) 

        # Status Text Area
        self.status_text = scrolledtext.ScrolledText(output_section, wrap=tk.WORD, height=10, 
                                                     state=tk.DISABLED, relief=tk.SUNKEN, borderwidth=1,
                                                     bg=LOG_BG_COLOR, fg=LOG_TEXT_COLOR, 
                                                     font=('Courier', 10)) 
        self.status_text.grid(row=1, column=0, sticky="nsew", pady=(5, 0)) 

        # --- Footer ---
        footer_frame = ttk.Frame(content_frame, style='TFrame') 
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0)) 
        footer_frame.columnconfigure(0, weight=1) 

        ttk.Label(footer_frame, text="© 2025 MSVenturesGroup OÜ — Serhii Yaremenko", style='Footer.TLabel').grid(row=0, column=0, sticky="w") 
        self.stats_label = ttk.Label(footer_frame, text="", style='Stats.TLabel')
        self.stats_label.grid(row=0, column=1, sticky="e", padx=(10, 0)) 

    def _update_stats_display(self):
        """Updates the statistics label in the footer."""
        usage = self.config.get('usage_count', 0)
        pages = self.config.get('total_pages_split', 0)
        self.stats_label.config(text=f"Runs: {usage} | Pages Split: {pages}")

    def select_files(self): 
        """Opens file dialog for multiple files and triggers processing."""
        filepaths = filedialog.askopenfilename(
            multiple=True, 
            title="Select PDF File(s)",
            initialdir=self.initial_dir, 
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if filepaths: 
            self.selected_paths_or_folder = filepaths 
            self.selection_type = "Files"
            display_text = f"{len(filepaths)} file(s) selected"
            self.display_path.set(display_text) 
            self.update_status(f"{display_text}\n") 
            self.path_entry.xview_moveto(1) 
            self.start_processing() 

    def select_folder(self):
        """Opens folder dialog and triggers processing."""
        folderpath = filedialog.askdirectory(
            title="Select Folder Containing PDFs",
            initialdir=self.initial_dir 
            )
        if folderpath:
            self.selected_paths_or_folder = folderpath 
            self.selection_type = "Folder"
            self.display_path.set(folderpath) 
            self.config['last_folder'] = folderpath
            self._save_config() 
            self.initial_dir = folderpath 
            
            self.update_status(f"Selected Folder: {folderpath}\n")
            self.path_entry.xview_moveto(1) 
            self.start_processing() 

    def update_status(self, message):
        """Appends a message to the status log area."""
        try:
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, str(message)) 
            self.status_text.see(tk.END) 
            self.status_text.config(state=tk.DISABLED)
            self.master.update_idletasks() 
        except tk.TclError as e:
            print(f"Error updating status text: {e}") 

    def copy_log_to_clipboard(self):
        """Copies the entire content of the status log to the clipboard."""
        try:
            log_content = self.status_text.get("1.0", tk.END).strip()
            if log_content:
                self.master.clipboard_clear()
                self.master.clipboard_append(log_content)
                self.update_status("Log content copied to clipboard.\n")
            else:
                self.update_status("Log is empty, nothing to copy.\n")
        except tk.TclError as e:
             self.update_status(f"Error copying log: {e}\n")

    def start_processing(self):
        """Validates selection and starts the PDF processing in a background thread."""
        if not self.selected_paths_or_folder:
            messagebox.showerror("Error", "No file(s) or folder selected.") 
            return

        # Keyword is always None now
        keyword = None 

        self.select_files_button.config(state=tk.DISABLED) 
        self.select_folder_button.config(state=tk.DISABLED)
        
        self.update_status("------------------------------\n")
        self.update_status("Starting processing...\n")
        # No keyword logging needed

        # Pass None for keyword
        thread = threading.Thread(target=self.run_processing_thread, 
                                  args=(self.selected_paths_or_folder, self.selection_type, None)) 
        thread.daemon = True 
        thread.start()

    def run_processing_thread(self, paths_or_folder, selection_type, keyword):
        """Worker thread function for processing."""
        success_count = 0
        fail_count = 0
        total_files = 0
        total_pages_split_this_run = 0

        try: 
            if selection_type == "Folder":
                success_count, fail_count, total_files, total_pages_split_this_run = process_shipment(
                    paths_or_folder, True, keyword, self.update_status
                )
            elif selection_type == "Files":
                files_to_process = paths_or_folder
                total_files = len(files_to_process)
                self.update_status(f"Processing {total_files} selected file(s)...\n")
                for i, pdf_path in enumerate(files_to_process):
                     self.update_status(f"--- Processing file {i+1}/{total_files}: {os.path.basename(pdf_path)} ---\n")
                     success, pages_split = process_single_pdf_document(pdf_path, keyword, self.update_status)
                     if success:
                         success_count += 1
                         total_pages_split_this_run += pages_split 
                     else:
                         fail_count += 1
            else:
                self.update_status("Error: Invalid selection type.\n")
                return 

            self.update_status(f"\n--- Processing Finished ---\n")
            self.update_status(f"Total Files Processed: {total_files}\n")
            self.update_status(f"Successful: {success_count}\n")
            self.update_status(f"Failed: {fail_count}\n")
            if fail_count > 0:
                 self.update_status(f"Check log above for details on failures.\n")

            if total_pages_split_this_run > 0:
                # Use a lock or queue for thread-safe config updates if high concurrency expected
                # For this simple case, reloading before update is likely sufficient
                current_config = self._load_config() 
                current_total = current_config.get('total_pages_split', 0)
                self.config['total_pages_split'] = current_total + total_pages_split_this_run
                self._save_config()
                self._update_stats_display() 

        except Exception as e:
             self.update_status(f"\n--- UNEXPECTED ERROR DURING PROCESSING --- \n")
             self.update_status(f"An error occurred in the processing thread: {e}\n")
             import traceback
             self.update_status(traceback.format_exc() + "\n")
        finally:
             self.select_files_button.config(state=tk.NORMAL) 
             self.select_folder_button.config(state=tk.NORMAL)

# Note: main.py will handle creating the root window and starting this app
