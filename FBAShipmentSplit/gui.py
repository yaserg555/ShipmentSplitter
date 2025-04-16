import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
# Use absolute imports now
from pdf_processor import process_shipment, process_single_pdf_document 

# --- Constants ---
BG_COLOR = "#f9f9f9"
LOG_BG_COLOR = "#f3f4f6"
LOG_TEXT_COLOR = "#111827"
FOOTER_TEXT_COLOR = "#9ca3af"

class FBASplitterApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("FBA Label splitter by sku") 
        self.master.geometry("600x550") 
        self.master.configure(bg=BG_COLOR)
        self.pack(fill=tk.BOTH, expand=True) 

        # Store selection: list/tuple for files, string for folder
        self.selected_paths_or_folder = None 
        # Track selection type: "Files", "Folder", or "None"
        self.selection_type = "None" 
        # For displaying in the entry widget
        self.display_path = tk.StringVar() 

        self._configure_styles()
        self._create_widgets()

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
        # Style for the small copy button
        style.configure('Copy.TButton', padding=(2, 2), font=('Helvetica', 9)) 
        style.configure('TEntry', padding=5)
        style.configure('TLabel', background=BG_COLOR, font=('Helvetica', 11))
        style.configure('Footer.TLabel', background=BG_COLOR, foreground=FOOTER_TEXT_COLOR, font=('Helvetica', 10))
        style.configure('Header.TLabel', background=BG_COLOR, font=('Helvetica', 12, 'bold'))
        style.configure('Status.TLabel', background=BG_COLOR, font=('Helvetica', 11, 'bold'))
        style.configure('Action.TButton', font=('Helvetica', 12, 'bold'), padding=(10, 8)) 

    def _create_widgets(self):
        """Create all the UI widgets."""
        content_frame = ttk.Frame(self, padding="10 10 10 10", style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(2, weight=1) 

        # --- Section 1: Input Selection ---
        input_section = ttk.Frame(content_frame, style='TFrame')
        input_section.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        input_section.columnconfigure(0, weight=1) 

        # Buttons Frame - Reverted to two buttons
        select_buttons_frame = ttk.Frame(input_section, style='TFrame')
        select_buttons_frame.pack(fill=tk.X) 
        self.select_files_button = ttk.Button(select_buttons_frame, text="Select File(s)", 
                                              command=self.select_files, width=15) 
        self.select_files_button.pack(side=tk.LEFT, padx=(0, 5), pady=5) 
        
        self.select_folder_button = ttk.Button(select_buttons_frame, text="Select Folder", 
                                               command=self.select_folder, width=15)
        self.select_folder_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Path Entry Frame (Below Buttons)
        path_frame = ttk.Frame(input_section, style='TFrame')
        path_frame.pack(fill=tk.X, pady=(5, 0)) 
        path_frame.columnconfigure(1, weight=1) 
        
        ttk.Label(path_frame, text="Selected:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.path_entry = ttk.Entry(path_frame, textvariable=self.display_path, state='readonly', width=60) 
        self.path_entry.grid(row=0, column=1, sticky="ew")

        # --- Section 2: Optional Keyword ---
        keyword_frame = ttk.Frame(content_frame, style='TFrame')
        keyword_frame.grid(row=1, column=0, sticky="ew", pady=10) 
        
        ttk.Label(keyword_frame, text="Optional Keyword (e.g., Qty, 数量, Menge):").pack(side=tk.LEFT, padx=(0, 5))
        self.sku_keyword_entry = ttk.Entry(keyword_frame, width=20)
        self.sku_keyword_entry.pack(side=tk.LEFT)

        # --- Section 3: Output ---
        output_section = ttk.Frame(content_frame, style='TFrame')
        output_section.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        output_section.rowconfigure(1, weight=1) 
        output_section.columnconfigure(0, weight=1) 

        # Status Header Frame (Label + Copy Button)
        status_header_frame = ttk.Frame(output_section, style='TFrame')
        status_header_frame.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(status_header_frame, text="Status Log", style='Status.TLabel').pack(side=tk.LEFT, anchor=tk.W)
        
        self.copy_log_button = ttk.Button(status_header_frame, text="Copy Log", 
                                          command=self.copy_log_to_clipboard, style='Copy.TButton', width=8)
        self.copy_log_button.pack(side=tk.RIGHT, padx=(5,0)) # Place button to the right

        # Status Text Area
        self.status_text = scrolledtext.ScrolledText(output_section, wrap=tk.WORD, height=10, 
                                                     state=tk.DISABLED, relief=tk.SUNKEN, borderwidth=1,
                                                     bg=LOG_BG_COLOR, fg=LOG_TEXT_COLOR, 
                                                     font=('Courier', 10)) 
        # Place text area below the header frame
        self.status_text.grid(row=1, column=0, sticky="nsew", pady=(5, 0)) 

        # --- Footer ---
        footer_frame = ttk.Frame(content_frame, style='TFrame') 
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(footer_frame, text="© 2025 Serhii Yaremenko Ph.D. for MSVenturesGroup OÜ", style='Footer.TLabel').pack(anchor=tk.W) 

    def select_files(self): 
        """Opens file dialog for multiple files and triggers processing."""
        initial_dir = os.path.dirname(os.path.abspath(sys.argv[0])) 
        filepaths = filedialog.askopenfilename(
            multiple=True, 
            title="Select PDF File(s)",
            initialdir=initial_dir, 
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
        initial_dir = os.path.dirname(os.path.abspath(sys.argv[0])) 
        folderpath = filedialog.askdirectory(
            title="Select Folder Containing PDFs",
            initialdir=initial_dir
            )
        if folderpath:
            self.selected_paths_or_folder = folderpath 
            self.selection_type = "Folder"
            self.display_path.set(folderpath) 
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
            print(f"Error updating status text: {e}") # Avoid crashing if widget destroyed

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

        keyword = self.sku_keyword_entry.get().strip() or None 

        # Disable both buttons
        self.select_files_button.config(state=tk.DISABLED) 
        self.select_folder_button.config(state=tk.DISABLED)
        
        self.update_status("------------------------------\n")
        self.update_status("Starting processing...\n")
        if keyword:
             self.update_status(f"Using keyword: '{keyword}'\n")
        else:
             self.update_status("Using default keywords.\n")

        # Pass the actual selection (list/tuple or string) to the thread
        thread = threading.Thread(target=self.run_processing_thread, 
                                  args=(self.selected_paths_or_folder, self.selection_type, keyword))
        thread.daemon = True 
        thread.start()

    def run_processing_thread(self, paths_or_folder, selection_type, keyword):
        """Worker thread function for processing."""
        success_count = 0
        fail_count = 0
        total_files = 0

        try: 
            if selection_type == "Folder":
                success_count, fail_count, total_files = process_shipment(
                    paths_or_folder, True, keyword, self.update_status
                )
            elif selection_type == "Files":
                files_to_process = paths_or_folder
                total_files = len(files_to_process)
                self.update_status(f"Processing {total_files} selected file(s)...\n")
                for i, pdf_path in enumerate(files_to_process):
                     self.update_status(f"--- Processing file {i+1}/{total_files}: {os.path.basename(pdf_path)} ---\n")
                     if process_single_pdf_document(pdf_path, keyword, self.update_status):
                         success_count += 1
                     else:
                         fail_count += 1
            else:
                self.update_status("Error: Invalid selection type.\n")
                return 

            # Report final results
            self.update_status(f"\n--- Processing Finished ---\n")
            self.update_status(f"Total Files Processed: {total_files}\n")
            self.update_status(f"Successful: {success_count}\n")
            self.update_status(f"Failed: {fail_count}\n")
            if fail_count > 0:
                 self.update_status(f"Check log above for details on failures.\n")

        except Exception as e:
             self.update_status(f"\n--- UNEXPECTED ERROR DURING PROCESSING --- \n")
             self.update_status(f"An error occurred in the processing thread: {e}\n")
             import traceback
             self.update_status(traceback.format_exc() + "\n")
        finally:
             # Re-enable both buttons
             self.select_files_button.config(state=tk.NORMAL) 
             self.select_folder_button.config(state=tk.NORMAL)

# Note: main.py will handle creating the root window and starting this app
