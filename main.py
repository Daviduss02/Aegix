import sys
import os
import tkinter as tk

def check_display():
    if os.name == 'posix':
        if 'DISPLAY' not in os.environ:
            print("[!] Error: No graphical display found. If you are using SSH, ensure you use the -X or -Y flag.")
            return False
    return True

if __name__ == "__main__":
    if not check_display():
        sys.exit(1)

    try:
        from GUI import AegixApp
        app = AegixApp()
        app.mainloop()
    except tk.TclError as e:
        print(f"[!] Critical Error: Could not initialize graphical interface.\nDetails: {e}")
        print("\nPossible solutions:")
        print("1. If on SSH: Connect using 'ssh -X user@host'")
        print("2. Ensure an X-server is running on your client machine (e.g., Xming, VcXsrv, or XQuartz)")
        print("3. Check if 'xauth' is installed on the remote machine")
        sys.exit(1)
    except ImportError as e:
        print(f"[!] Error: Missing dependencies. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        sys.exit(1)
