import tkinter as tk
from tkinter import ttk, messagebox
from database import (create_connection, add_topic, get_all_topics,
                    add_concept, get_concepts_for_topic, get_all_topics_with_mastery,
                    get_next_concept_to_review, record_recall_session,
                    initialize_learning_data, update_learning_data)
from knowledge_base import allocate_technique, get_technique_id_by_name, update_concept_learning_progress
from fsrs import FSRS, default_params
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.conn = create_connection(DB_FILE)
        if self.conn is None:
            messagebox.showerror("Database Error", f"Could not create or connect to the database at {DB_FILE}")
            self.destroy()
            return
        self.create_widgets()
        self.populate_topics_list()
        self.current_concept = None
        self.current_technique = None

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

        # --- Autonomous Tab ---
        self.autonomous_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.autonomous_tab, text="Autonomous")
        self.create_autonomous_widgets(self.autonomous_tab)

        # --- Status Bar ---
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_autonomous_widgets(self, parent_frame):
        # Frame for displaying the next action
        action_frame = ttk.LabelFrame(parent_frame, text="Next Action")
        action_frame.pack(padx=10, pady=10, fill="x")

        get_action_button = ttk.Button(action_frame, text="Get Next Action", command=self.get_next_action)
        get_action_button.pack(pady=5)

        self.concept_label = ttk.Label(action_frame, text="", wraplength=780)
        self.concept_label.pack(pady=10)

        self.technique_label = ttk.Label(action_frame, text="", font=("tahoma", "10", "bold"))
        self.technique_label.pack(pady=5)

        # Frame for user response
        response_frame = ttk.LabelFrame(parent_frame, text="Your Response")
        response_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.response_text = tk.Text(response_frame, height=10, width=80)
        self.response_text.pack(padx=5, pady=5, fill="both", expand=True)

        submit_button = ttk.Button(response_frame, text="Submit", command=self.submit_response)
        submit_button.pack(pady=5)

    def get_next_action(self):
        next_concept = get_next_concept_to_review(self.conn)
        if next_concept:
            self.current_concept = next_concept
            concept_id, _, concept_content = next_concept

            technique = allocate_technique(self.conn, concept_id)
            self.current_technique = technique

            self.concept_label.config(text=f"Concept: {concept_content}")
            self.technique_label.config(text=f"Technique: {technique}")

            self.response_text.delete('1.0', tk.END)
        else:
            self.concept_label.config(text="No concepts to review. Add some new concepts!")
            self.technique_label.config(text="")
            self.current_concept = None
            self.current_technique = None

    def submit_response(self):
        if not self.current_concept:
            messagebox.showwarning("No Action", "There is no concept to submit a response for. Please click 'Get Next Action'.")
            return

        user_response = self.response_text.get("1.0", tk.END).strip()
        if not user_response:
            messagebox.showwarning("Empty Response", "Please enter a response.")
            return

        # For now, we'll use a fixed grade of 'Good' (3)
        grade = 3
        concept_id = self.current_concept[0]

        # 1. Record the recall session
        record_recall_session(self.conn, concept_id, user_response, grade)

        # 2. Update FSRS data
        fsrs = FSRS(default_params)

        # Check if the concept has existing learning data
        cur = self.conn.cursor()
        cur.execute("SELECT difficulty, stability FROM learning_data WHERE concept_id = ?", (concept_id,))
        result = cur.fetchone()

        if result:
            # Update existing FSRS data
            difficulty, stability = result

            # We need the last review date to calculate retrievability
            cur.execute("""
                SELECT MAX(rs.timestamp) FROM recall_sessions rs
                WHERE rs.concept_id = ? AND rs.id != (SELECT MAX(id) FROM recall_sessions WHERE concept_id = ?)
            """, (concept_id, concept_id))
            last_review_str = cur.fetchone()[0]

            if last_review_str:
                last_review_date = datetime.datetime.fromisoformat(last_review_str)
                days_since_review = (datetime.datetime.now() - last_review_date).days
            else:
                # This is the first review after being a new card
                days_since_review = 0


            retrievability = fsrs.retrievability(days_since_review, stability) if last_review_str else 1.0

            new_difficulty = fsrs.new_difficulty(difficulty, grade)
            new_stability = fsrs.new_stability(new_difficulty, stability, retrievability, grade)

            update_learning_data(self.conn, concept_id, new_difficulty, new_stability)
            self.status_bar.config(text=f"Updated concept {concept_id}. New D: {new_difficulty:.2f}, S: {new_stability:.2f}")

        else:
            # Initialize FSRS data for a new concept
            stability = fsrs.initial_stability(grade)
            difficulty = fsrs.initial_difficulty(grade)
            initialize_learning_data(self.conn, concept_id, difficulty, stability)
            self.status_bar.config(text=f"Initialized concept {concept_id}. D: {difficulty:.2f}, S: {stability:.2f}")

        # 3. Update concept learning progress
        technique_id = get_technique_id_by_name(self.conn, self.current_technique)
        if technique_id:
            update_concept_learning_progress(self.conn, concept_id, technique_id)

        # 4. Get the next action for the user
        messagebox.showinfo("Success", "Response recorded successfully!")
        self.get_next_action()

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

    def create_dashboard_widgets(self, parent_frame):
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

        topics_with_mastery = get_all_topics_with_mastery(self.conn)

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
        self.topics_data = get_all_topics(self.conn)
        for topic in self.topics_data:
            self.topics_listbox.insert(tk.END, topic[1])

    def add_new_topic(self):
        topic_name = self.topic_entry.get()
        if topic_name:
            if add_topic(self.conn, topic_name) is None:
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
        self.selected_topic = self.topics_data[selected_index]

        self.topic_selection_frame.pack_forget()
        self.concept_management_frame.pack(fill="both", expand=True)
        self.populate_concepts_list()

    def populate_concepts_list(self):
        self.concepts_listbox.delete(0, tk.END)
        if hasattr(self, 'selected_topic'):
            concepts = get_concepts_for_topic(self.conn, self.selected_topic[0])
            for concept in concepts:
                self.concepts_listbox.insert(tk.END, concept[2])

    def add_new_concept(self):
        concept_content = self.concept_entry.get()
        if concept_content and hasattr(self, 'selected_topic'):
            if add_concept(self.conn, self.selected_topic[0], concept_content) is None:
                messagebox.showerror("Database Error", "Failed to add the new concept.")
                self.status_bar.config(text="Error: Failed to add new concept.")
            else:
                self.concept_entry.delete(0, tk.END)
                self.populate_concepts_list()
                self.status_bar.config(text="Concept added successfully.")

    def show_topic_selection(self):
        self.concept_management_frame.pack_forget()
        self.topic_selection_frame.pack(fill="both", expand=True)
        if hasattr(self, 'selected_topic'):
            del self.selected_topic

    def on_closing(self):
        if self.conn:
            self.conn.close()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
