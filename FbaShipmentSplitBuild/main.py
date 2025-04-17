import tkinter as tk
from gui import FBASplitterApp # Import the main app class from gui.py

if __name__ == "__main__":
    # Create the main application window
    root = tk.Tk() 
    
    # Create an instance of the application class, passing the root window
    app = FBASplitterApp(master=root) 
    
    # Start the Tkinter event loop
    root.mainloop()
