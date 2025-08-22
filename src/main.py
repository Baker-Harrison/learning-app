import tkinter as tk
from tkinter import ttk
from database import create_connection, add_topic, get_all_topics, add_concept, get_concepts_for_topic

DB_FILE = "data/learning_data.db"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Learning App")
        self.geometry("800x600")
        self.conn = create_connection(DB_FILE)
        self.create_widgets()
        self.populate_topics_list()

    def create_widgets(self):
        # Main frames
        self.topic_selection_frame = ttk.Frame(self)
        self.concept_management_frame = ttk.Frame(self)

        self.topic_selection_frame.pack(fill="both", expand=True)
        # self.concept_management_frame.pack(fill="both", expand=True) # Initially hidden

        # --- Topic Selection Widgets ---
        topic_frame = ttk.LabelFrame(self.topic_selection_frame, text="Topics")
        topic_frame.pack(padx=10, pady=10, fill="x")

        self.topic_entry = ttk.Entry(topic_frame, width=40)
        self.topic_entry.pack(side="left", padx=5, pady=5)

        add_topic_button = ttk.Button(topic_frame, text="Add Topic", command=self.add_new_topic)
        add_topic_button.pack(side="left", padx=5, pady=5)

        self.topics_listbox = tk.Listbox(self.topic_selection_frame, height=10)
        self.topics_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.topics_listbox.bind("<<ListboxSelect>>", self.on_topic_select)

        # --- Concept Management Widgets ---
        concept_frame = ttk.LabelFrame(self.concept_management_frame, text="Concepts")
        concept_frame.pack(padx=10, pady=10, fill="x")

        self.concept_entry = ttk.Entry(concept_frame, width=40)
        self.concept_entry.pack(side="left", padx=5, pady=5)

        add_concept_button = ttk.Button(concept_frame, text="Add Concept", command=self.add_new_concept)
        add_concept_button.pack(side="left", padx=5, pady=5)

        self.concepts_listbox = tk.Listbox(self.concept_management_frame, height=10)
        self.concepts_listbox.pack(padx=10, pady=10, fill="both", expand=True)

        back_button = ttk.Button(self.concept_management_frame, text="Back to Topics", command=self.show_topic_selection)
        back_button.pack(pady=5)

    def populate_topics_list(self):
        self.topics_listbox.delete(0, tk.END)
        self.topics_data = get_all_topics(self.conn)
        for topic in self.topics_data:
            self.topics_listbox.insert(tk.END, topic[1])

    def add_new_topic(self):
        topic_name = self.topic_entry.get()
        if topic_name:
            add_topic(self.conn, topic_name)
            self.topic_entry.delete(0, tk.END)
            self.populate_topics_list()

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
            add_concept(self.conn, self.selected_topic[0], concept_content)
            self.concept_entry.delete(0, tk.END)
            self.populate_concepts_list()

    def show_topic_selection(self):
        self.concept_management_frame.pack_forget()
        self.topic_selection_frame.pack(fill="both", expand=True)
        del self.selected_topic

    def on_closing(self):
        if self.conn:
            self.conn.close()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
