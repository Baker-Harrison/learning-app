import tkinter as tk
from tkinter import ttk, messagebox
from logic import LearningAppLogic

DB_FILE = "data/learning_data.db"

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, justify='left',
                      background="#ffffe0", relief='solid', borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Learning App")
        self.geometry("800x600")
        self.logic = LearningAppLogic(DB_FILE)
        self.create_widgets()
        self.populate_topics_list()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # --- Management Tab ---
        self.management_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.management_tab, text="Management")
        self.create_management_widgets(self.management_tab)

        # --- Dashboard Tab ---
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.create_dashboard_widgets(self.dashboard_tab)

        # --- Settings Tab ---
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self.create_settings_widgets(self.settings_tab)

        # --- Status Bar ---
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_management_widgets(self, parent_frame):
        # Main frames
        self.topic_selection_frame = ttk.Frame(parent_frame)
        self.concept_management_frame = ttk.Frame(parent_frame)

        self.topic_selection_frame.pack(fill="both", expand=True)

        # --- Topic Selection Widgets ---
        topic_frame = ttk.LabelFrame(self.topic_selection_frame, text="Topics")
        topic_frame.pack(padx=10, pady=10, fill="x")

        self.topic_entry = ttk.Entry(topic_frame, width=40)
        self.topic_entry.pack(side="left", padx=5, pady=5)
        Tooltip(self.topic_entry, "Enter a new topic and click 'Add Topic'")

        add_topic_button = ttk.Button(topic_frame, text="Add Topic", command=self.add_new_topic)
        add_topic_button.pack(side="left", padx=5, pady=5)
        Tooltip(add_topic_button, "Save the new topic")

        self.topics_listbox = tk.Listbox(self.topic_selection_frame, height=10)
        self.topics_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.topics_listbox.bind("<<ListboxSelect>>", self.on_topic_select)
        Tooltip(self.topics_listbox, "Select a topic to manage its concepts")

        # --- Concept Management Widgets ---
        concept_frame = ttk.LabelFrame(self.concept_management_frame, text="Concepts")
        concept_frame.pack(padx=10, pady=10, fill="x")

        self.concept_entry = ttk.Entry(concept_frame, width=40)
        self.concept_entry.pack(side="left", padx=5, pady=5)
        Tooltip(self.concept_entry, "Enter a new concept and click 'Add Concept'")

        add_concept_button = ttk.Button(concept_frame, text="Add Concept", command=self.add_new_concept)
        add_concept_button.pack(side="left", padx=5, pady=5)
        Tooltip(add_concept_button, "Save the new concept")

        self.concepts_listbox = tk.Listbox(self.concept_management_frame, height=10)
        self.concepts_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        Tooltip(self.concepts_listbox, "List of concepts for the selected topic")

        back_button = ttk.Button(self.concept_management_frame, text="Back to Topics", command=self.show_topic_selection)
        back_button.pack(pady=5)
        Tooltip(back_button, "Return to the topic list")

    def create_settings_widgets(self, parent_frame):
        # --- Gemini API Key ---
        api_key_frame = ttk.LabelFrame(parent_frame, text="Gemini API Key")
        api_key_frame.pack(padx=10, pady=10, fill="x")

        self.api_key_entry = ttk.Entry(api_key_frame, width=60, show="*")
        self.api_key_entry.pack(side="left", padx=5, pady=5)
        self.api_key_entry.insert(0, self.logic.get_api_key() or "")
        Tooltip(self.api_key_entry, "Enter your Gemini API Key")

        save_api_key_button = ttk.Button(api_key_frame, text="Save", command=self.save_api_key)
        save_api_key_button.pack(side="left", padx=5, pady=5)
        Tooltip(save_api_key_button, "Save the API Key")

        # --- Knowledge Input ---
        knowledge_frame = ttk.LabelFrame(parent_frame, text="Add Knowledge from Text")
        knowledge_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.knowledge_text = tk.Text(knowledge_frame, height=15, width=80)
        self.knowledge_text.pack(padx=5, pady=5, fill="both", expand=True)
        Tooltip(self.knowledge_text, "Paste a block of text to be processed into concepts")

        process_knowledge_button = ttk.Button(knowledge_frame, text="Process Knowledge", command=self.process_knowledge)
        process_knowledge_button.pack(pady=5)
        Tooltip(process_knowledge_button, "Use Gemini to extract concepts from the text")

    def save_api_key(self):
        api_key = self.api_key_entry.get()
        if api_key:
            self.logic.save_api_key(api_key)
            messagebox.showinfo("Settings", "API Key saved successfully.")
            self.status_bar.config(text="API Key saved.")
        else:
            messagebox.showwarning("Settings", "API Key cannot be empty.")

    def process_knowledge(self):
        knowledge_text = self.knowledge_text.get("1.0", tk.END).strip()

        if not self.logic.selected_topic:
            messagebox.showwarning("Warning", "Please select a topic first from the Management tab.")
            return

        try:
            concepts = self.logic.process_knowledge(knowledge_text, self.logic.selected_topic[0])
            if concepts:
                self.populate_concepts_list()
                self.knowledge_text.delete("1.0", tk.END)
                self.status_bar.config(text=f"{len(concepts)} concepts added to '{self.logic.selected_topic[1]}'.")
                messagebox.showinfo("Success", f"Successfully added {len(concepts)} new concepts.")
            else:
                messagebox.showinfo("Info", "No concepts were extracted. Try rephrasing your text.")

        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Error", str(e))

    def create_dashboard_widgets(self, parent_frame):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        refresh_button = ttk.Button(parent_frame, text="Refresh", command=self.update_dashboard)
        refresh_button.pack(side=tk.BOTTOM, pady=5)
        Tooltip(refresh_button, "Refresh the mastery dashboard")

        self.notebook.bind("<<Ttk::NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:  # Dashboard tab
            self.update_dashboard()

    def update_dashboard(self):
        self.ax.clear()
        topics_with_mastery = self.logic.get_all_topics_with_mastery()

        if not topics_with_mastery:
            self.ax.set_title("No topics to display")
            self.canvas.draw()
            return

        topic_names = [x[1] for x in topics_with_mastery]
        mastery_scores = [x[2] for x in topics_with_mastery]

        self.ax.bar(topic_names, mastery_scores)
        self.ax.set_title("Topic Mastery")
        self.ax.set_ylabel("Mastery Score")
        self.ax.set_ylim(0, 1)
        self.fig.tight_layout()
        self.canvas.draw()

    def populate_topics_list(self):
        self.topics_listbox.delete(0, tk.END)
        self.topics_data = self.logic.get_all_topics()
        for topic in self.topics_data:
            self.topics_listbox.insert(tk.END, topic[1])

    def add_new_topic(self):
        topic_name = self.topic_entry.get()
        if topic_name:
            if self.logic.add_new_topic(topic_name) is None:
                messagebox.showerror("Database Error", "Failed to add the new topic.")
                self.status_bar.config(text=f"Error: Failed to add topic '{topic_name}'")
            else:
                self.topic_entry.delete(0, tk.END)
                self.populate_topics_list()
                self.status_bar.config(text=f"Topic '{topic_name}' added successfully.")

    def on_topic_select(self, event):
        selection_indices = self.topics_listbox.curselection()
        if not selection_indices:
            return
        selected_index = selection_indices[0]
        self.logic.selected_topic = self.topics_data[selected_index]
        self.topic_selection_frame.pack_forget()
        self.concept_management_frame.pack(fill="both", expand=True)
        self.populate_concepts_list()

    def populate_concepts_list(self):
        self.concepts_listbox.delete(0, tk.END)
        if self.logic.selected_topic:
            concepts = self.logic.get_concepts_for_topic(self.logic.selected_topic[0])
            for concept in concepts:
                self.concepts_listbox.insert(tk.END, concept[2])

    def add_new_concept(self):
        concept_content = self.concept_entry.get()
        if concept_content and self.logic.selected_topic:
            if self.logic.add_new_concept(self.logic.selected_topic[0], concept_content) is None:
                messagebox.showerror("Database Error", "Failed to add the new concept.")
                self.status_bar.config(text="Error: Failed to add new concept.")
            else:
                self.concept_entry.delete(0, tk.END)
                self.populate_concepts_list()
                self.status_bar.config(text="Concept added successfully.")

    def show_topic_selection(self):
        self.concept_management_frame.pack_forget()
        self.topic_selection_frame.pack(fill="both", expand=True)
        self.logic.selected_topic = None

    def on_closing(self):
        self.logic.close_connection()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
