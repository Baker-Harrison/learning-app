import tkinter as tk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Learning App")
        self.geometry("800x600")

if __name__ == "__main__":
    app = App()
    app.mainloop()
