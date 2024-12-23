import urllib.request
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import time
import customtkinter as ctk
from tkinter import filedialog
import threading
from tkinter import font

class ProxyCheckerGUI:
    def __init__(self):
        # Window setup
        self.window = ctk.CTk()
        self.window.title("ProxyChecker-UI by akramway00")
        self.window.iconbitmap('icon.ico') 

        # self.window.option_add("*Font", "SpaceGrotesk")

        window_width=1200
        window_height=800
        button_font = ("Segoe UI", 22, "bold")
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        # window_width = int(screen_width * 0.8)
        # window_height = int(screen_height * 0.8)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)

        # Left panel (1/3 width)
        self.left_panel = ctk.CTkFrame(self.window, width=window_width//3)  
        self.left_panel.pack(side="left", fill="both", padx=10, pady=10, expand=False)  

        # Proxy input area
        self.proxy_input = ctk.CTkTextbox(self.left_panel, width=window_width//3-30)
        self.proxy_input.pack(padx=10, pady=10, fill="both", expand=True)

        # Buttons in left panel
        self.load_button = ctk.CTkButton(self.left_panel, text="Load Proxies", height=40,font=button_font,fg_color="#424242" ,command=self.load_proxies)
        self.load_button.pack(padx=10, pady=5, fill="x")

        self.load_file_button = ctk.CTkButton(self.left_panel, text="Load Proxies from File",height=40,font=button_font,fg_color="#424242" , command=self.load_from_file)
        self.load_file_button.pack(padx=10, pady=5, fill="x")

        # Right panel (2/3 width)
        self.right_panel = ctk.CTkFrame(self.window)
        self.right_panel.pack(side="right", fill="both", padx=10, pady=10, expand=True)

        # Results display
        self.results_display = ctk.CTkTextbox(self.right_panel)
        self.results_display.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.results_display.tag_config("success", foreground="lime green")
        self.results_display.tag_config("error", foreground="red")

        # Start button
        self.start_button = ctk.CTkButton(self.right_panel, text="Start Checking",height=40,font=button_font,fg_color="#424242" , command=self.start_checking)
        self.start_button.pack(padx=10, pady=10, fill="x")

        # Initialize proxy lists
        self.working_proxies = []
        self.failed_proxies = []

    def run(self):
        self.window.mainloop()

    def load_proxies(self):
        
        proxy_text = self.proxy_input.get("1.0", "end-1c")
        if not proxy_text.strip():
            self.update_results("Please enter proxies first!")
            return
        self.proxies = [p.strip() for p in proxy_text.splitlines() if p.strip()]
        self.update_results(f"Loaded {len(self.proxies)} proxies from input.")

    def load_from_file(self):
        filename = filedialog.askopenfilename(
            title="Select Proxy List",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    proxies = f.read()
                    self.proxy_input.delete("1.0", "end")
                    self.proxy_input.insert("1.0", proxies)
                    self.load_proxies()  # Process loaded proxies
            except Exception as e:
                self.update_results(f"Error loading file: {str(e)}")

    def update_results(self, message: str):
        self.results_display.configure(state="normal")
        self.results_display.insert("end", f"{message}\n")
        self.results_display.see("end")
        self.results_display.configure(state="disabled")

    def validate_proxy(self, proxy: str) -> bool:
        try:
            
            parts = proxy.split(':')
            if len(parts) != 2:
                return False
            port = int(parts[1])
            return 1 <= port <= 65535
        except:
            return False
    
    def check_single_proxy(self, proxy: str) -> Tuple[str, bool]:
        try:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            
            with opener.open('http://www.google.com', timeout=10) as response:
                return proxy, True
        except Exception as e:
            return proxy, False

    def update_progress(self, proxy: str, is_working: bool):
        self.results_display.configure(state="normal")
        if isinstance(proxy, str) and ("Working:" in proxy or "Failed:" in proxy):
            # For final results summary
            self.results_display.insert("end", f"{proxy}\n")
        else:
            # For individual proxy results
            status = "✓ Working" if is_working else "✗ Failed"
            line = f"{status}: {proxy}\n"
            position = self.results_display.index("end-1c")
            self.results_display.insert("end", line)
            self.results_display.tag_add("success" if is_working else "error", 
                                    position, f"{position}+{len(line)}c")
        
        self.results_display.see("end")
        self.results_display.configure(state="disabled")
    
    def save_working_proxies(self):
        try:
            with open('workingProxies.txt', 'w') as f:
                f.write('\n'.join(self.working_proxies))
            return True
        except Exception as e:
            self.update_progress(f"Error saving proxies: {str(e)}", False)
            return False

    def start_checking(self):
        # Disable buttons during check
        self.start_button.configure(state="disabled")
        self.load_button.configure(state="disabled")
        self.load_file_button.configure(state="disabled")

        # Clear previous results
        self.results_display.configure(state="normal")
        self.results_display.delete("1.0", "end")
        self.results_display.configure(state="disabled")
        
        # Get proxies from input
        proxies = self.proxy_input.get("1.0", "end-1c").splitlines()
        if not proxies:
            self.update_progress("No proxies to check!", False)
            return

        def check_proxies_thread():
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(self.check_single_proxy, proxy): proxy 
                        for proxy in proxies if proxy.strip()}
                
                for future in as_completed(futures):
                    proxy, is_working = future.result()
                    if is_working:
                        self.working_proxies.append(proxy)
                    else:
                        self.failed_proxies.append(proxy)
                        
                    # Update GUI from main thread
                    self.window.after(0, self.update_progress, proxy, is_working)

            
            if self.working_proxies:
                self.save_working_proxies()
                save_message = "\nWorking proxies saved to 'workingProxies.txt'"
            else:
                save_message = "\nNo working proxies to save"

            # Re-enable buttons after completion
            self.window.after(0, lambda: self.start_button.configure(state="normal"))
            self.window.after(0, lambda: self.load_button.configure(state="normal"))
            self.window.after(0, lambda: self.load_file_button.configure(state="normal"))
            
            # Show final results
            self.window.after(0, lambda: self.update_progress(
                f"\nResults:\nWorking: {len(self.working_proxies)}\nFailed: {len(self.failed_proxies)}", 
                True
            ))

        
        threading.Thread(target=check_proxies_thread, daemon=True).start()

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ProxyCheckerGUI()
    app.run()

if __name__ == "__main__":
    main()