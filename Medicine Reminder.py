import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

MEDICINE_FILE = "medicines.csv"
LOG_FILE = "medicine_log.csv"

try:
    from plyer import notification
except Exception:
    notification = None

try:
    import winsound
except Exception:
    winsound = None


def ensure_files():
    try:
        pd.read_csv(MEDICINE_FILE)
    except Exception:
        pd.DataFrame(columns=["Medicine","Dose","Time","Frequency"]).to_csv(MEDICINE_FILE,index=False)

    try:
        pd.read_csv(LOG_FILE)
    except Exception:
        pd.DataFrame(columns=["Medicine","Date","Time","Status"]).to_csv(LOG_FILE,index=False)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Medicine Reminder")
        self.root.geometry("900x600")

        frm = tk.Frame(root)
        frm.pack(pady=10)

        tk.Label(frm, text="Medicine").grid(row=0, column=0)
        tk.Label(frm, text="Dose").grid(row=0, column=1)
        tk.Label(frm, text="Time (HH:MM)").grid(row=0, column=2)
        tk.Label(frm, text="Frequency").grid(row=0, column=3)

        self.med = tk.Entry(frm)
        self.dose = tk.Entry(frm)
        self.time = tk.Entry(frm)
        self.freq = tk.Entry(frm)

        self.med.grid(row=1, column=0, padx=5)
        self.dose.grid(row=1, column=1, padx=5)
        self.time.grid(row=1, column=2, padx=5)
        self.freq.grid(row=1, column=3, padx=5)

        tk.Button(frm, text="Add Medicine", command=self.add_medicine).grid(row=1, column=4, padx=5)

        self.tree = ttk.Treeview(root, columns=("Medicine","Dose","Time","Frequency"), show="headings")
        for c in ("Medicine","Dose","Time","Frequency"):
            self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btns = tk.Frame(root)
        btns.pack()

        tk.Button(btns, text="Refresh", command=self.load_data).pack(side="left", padx=5)
        tk.Button(btns, text="Delete", command=self.delete_medicine).pack(side="left", padx=5)
        tk.Button(btns, text="Mark Taken", command=lambda: self.log_status("Taken")).pack(side="left", padx=5)
        tk.Button(btns, text="Mark Missed", command=lambda: self.log_status("Missed")).pack(side="left", padx=5)
        tk.Button(btns, text="Report", command=self.report).pack(side="left", padx=5)
        tk.Button(btns, text="Show Graph", command=self.graph).pack(side="left", padx=5)

        self.load_data()
        self.check_reminders()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        df = pd.read_csv(MEDICINE_FILE)
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

    def add_medicine(self):
        med = self.med.get().strip()
        dose = self.dose.get().strip()
        tm = self.time.get().strip()
        freq = self.freq.get().strip()

        if not med or not tm:
            messagebox.showerror("Error", "Medicine and Time required.")
            return

        df = pd.read_csv(MEDICINE_FILE)
        df.loc[len(df)] = [med, dose, tm, freq]
        df.to_csv(MEDICINE_FILE, index=False)

        self.load_data()
        self.med.delete(0, tk.END)
        self.dose.delete(0, tk.END)
        self.time.delete(0, tk.END)
        self.freq.delete(0, tk.END)

    def delete_medicine(self):
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0])["values"]
        med = values[0]

        df = pd.read_csv(MEDICINE_FILE)
        df = df[df["Medicine"] != med]
        df.to_csv(MEDICINE_FILE, index=False)

        self.load_data()

    def log_status(self, status):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a medicine.")
            return

        values = self.tree.item(sel[0])["values"]
        med = values[0]

        log = pd.read_csv(LOG_FILE)
        log.loc[len(log)] = [
            med,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M"),
            status
        ]
        log.to_csv(LOG_FILE, index=False)

        messagebox.showinfo("Saved", f"{med} marked as {status}.")

    def report(self):
        log = pd.read_csv(LOG_FILE)

        if len(log) == 0:
            messagebox.showinfo("Report", "No log data.")
            return

        total = len(log)
        taken = len(log[log["Status"].str.lower() == "taken"])
        missed = total - taken
        adherence = (taken / total) * 100

        messagebox.showinfo(
            "Report",
            f"Total Doses: {total}\nTaken: {taken}\nMissed: {missed}\nAdherence: {adherence:.2f}%"
        )

    def graph(self):
        log = pd.read_csv(LOG_FILE)

        if len(log) == 0:
            messagebox.showinfo("Graph", "No log data.")
            return

        counts = log["Status"].value_counts()
        plt.figure(figsize=(5,4))
        plt.bar(counts.index, counts.values)
        plt.title("Medicine Adherence")
        plt.xlabel("Status")
        plt.ylabel("Count")
        plt.show()

    def check_reminders(self):
        now = datetime.now().strftime("%H:%M")
        df = pd.read_csv(MEDICINE_FILE)

        for _, row in df.iterrows():
            if str(row["Time"]) == now:
                msg = f"Time to take {row['Medicine']} ({row['Dose']})"

                if notification:
                    try:
                        notification.notify(
                            title="Medicine Reminder",
                            message=msg,
                            timeout=10
                        )
                    except Exception:
                        pass

                if winsound:
                    try:
                        winsound.Beep(1000, 700)
                    except Exception:
                        pass

                messagebox.showinfo("Medicine Reminder", msg)

        self.root.after(30000, self.check_reminders)


ensure_files()
root = tk.Tk()
app = App(root)
root.mainloop()