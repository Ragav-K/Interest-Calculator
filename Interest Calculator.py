import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import io
from PIL import Image

try:
    import ttkbootstrap as tb
    root = tb.Window(themename="minty")
except ImportError:
    root = tk.Tk()

root.title("Interest Calculator")
root.geometry("600x900")
root.resizable(False, False)

# === Variables ===
principal_var = tk.StringVar()
rate_var = tk.StringVar()
time_var = tk.StringVar()
currency_var = tk.StringVar(value="₹")
type_var = tk.StringVar(value="Simple")
frequency_var = tk.StringVar(value="Annually")
note_type_var = tk.StringVar()
result_data = {}

# === Frequency Map ===
freq_map = {"Annually": 1, "Semi-Annually": 2, "Quarterly": 4, "Monthly": 12}

# === Notes Data ===
notes_data = {
    "FD - Compound": {
        "Recommended Rate (%)": 6.5,
        "Time (Years)": "1-5",
        "Remarks": "Interest compounded quarterly",
    },
    "Savings - Simple": {
        "Recommended Rate (%)": 3.5,
        "Time (Years)": "Flexible",
        "Remarks": "Low interest, simple interest"
    },
    "Home Loan - EMI": {
        "Recommended Rate (%)": 8.5,
        "Time (Years)": "20-30",
        "Remarks": "EMI-based long term"
    },
    "Education Loan - EMI": {
        "Recommended Rate (%)": 9.0,
        "Time (Years)": "5-15",
        "Remarks": "EMI after study period"
    }
}

# === PDF Image Buffer ===
chart_img_data = None


def calculate():
    global result_data, chart_img_data
    try:
        P = float(principal_var.get())
        R = float(rate_var.get())
        T = float(time_var.get())
        currency = currency_var.get()
        calc_type = type_var.get()

        if P <= 0 or R < 0 or T <= 0:
            raise ValueError("Values must be positive.")

        if calc_type == "Simple":
            interest = (P * R * T) / 100
            amount = P + interest
            result_data = {"Principal": P, "Interest": interest, "Total Amount": amount, "Currency": currency}
            result_label.config(text=f"Interest: {currency}{interest:.2f}\nTotal: {currency}{amount:.2f}")

        elif calc_type == "Compound":
            freq = freq_map[frequency_var.get()]
            amount = P * (1 + R / (100 * freq)) ** (freq * T)
            interest = amount - P
            result_data = {"Principal": P, "Interest": interest, "Total Amount": amount, "Currency": currency}
            result_label.config(text=f"Compound Interest: {currency}{interest:.2f}\nTotal: {currency}{amount:.2f}")

        elif calc_type == "EMI":
            months = int(T * 12)
            monthly_rate = R / 12 / 100
            emi = (P * monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
            total = emi * months
            interest = total - P
            result_data = {
                "Principal": P, "Monthly EMI": emi,
                "Total Interest": interest, "Total Payment": total,
                "Currency": currency
            }
            result_label.config(text=f"EMI: {currency}{emi:.2f}/month\nTotal: {currency}{total:.2f}")
        else:
            raise ValueError("Choose a calculation type.")

        draw_pie_chart(P, interest, currency)

    except Exception as e:
        result_data = {}
        messagebox.showerror("Error", str(e))


def draw_pie_chart(P, interest, currency):
    global chart_img_data
    chart_fig = Figure(figsize=(4, 3), dpi=100)
    ax = chart_fig.add_subplot(111)
    ax.pie([P, interest], labels=["Principal", "Interest"], autopct="%1.1f%%", colors=["#66b3ff", "#ff9999"])
    ax.set_title("Breakup of Amount")

    for widget in chart_frame.winfo_children():
        widget.destroy()

    canvas_widget = FigureCanvasTkAgg(chart_fig, master=chart_frame)
    canvas_widget.draw()
    canvas_widget.get_tk_widget().pack()

    buf = io.BytesIO()
    chart_fig.savefig(buf, format="png")
    chart_img_data = buf.getvalue()
    buf.close()


def export_pdf():
    if not result_data:
        return messagebox.showwarning("No Data", "Calculate something first.")
    path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
    if path:
        try:
            c = canvas.Canvas(path, pagesize=letter)
            text = c.beginText(50, 750)
            text.setFont("Helvetica", 12)
            text.textLine("Loan/EMI Calculation:")
            text.textLine("")

            for k, v in result_data.items():
                if isinstance(v, float):
                    v = f"{result_data['Currency']}{v:.2f}"
                text.textLine(f"{k}: {v}")
            c.drawText(text)

            if chart_img_data:
                img = Image.open(io.BytesIO(chart_img_data))
                img_path = path.replace(".pdf", "_chart.png")
                img.save(img_path)
                c.drawImage(img_path, 150, 400, width=300, height=225)
            c.save()
            messagebox.showinfo("Success", "PDF saved!")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))


def show_note_details(*args):
    key = note_type_var.get()
    if key in notes_data:
        data = notes_data[key]
        note_output.config(state="normal")
        note_output.delete("1.0", tk.END)
        for k, v in data.items():
            note_output.insert(tk.END, f"{k}: {v}\n")
        note_output.config(state="disabled")


def jump_focus(event, next_widget):
    next_widget.focus()
    return "break"


# === UI ===
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# === Calculator Tab ===
calc_tab = ttk.Frame(notebook)
notebook.add(calc_tab, text="Calculator")

main_frame = ttk.Frame(calc_tab, padding=20)
main_frame.pack(fill="both", expand=True)

entry1 = ttk.Entry(main_frame, textvariable=principal_var)
entry2 = ttk.Entry(main_frame, textvariable=rate_var)
entry3 = ttk.Entry(main_frame, textvariable=time_var)

widgets = [
    ("Principal", entry1),
    ("Rate (%)", entry2),
    ("Time (Years)", entry3)
]

for i, (label, widget) in enumerate(widgets):
    ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky="w")
    widget.grid(row=i, column=1, pady=5)

entry1.bind("<Return>", lambda e: jump_focus(e, entry2))
entry2.bind("<Return>", lambda e: jump_focus(e, entry3))
entry3.bind("<Return>", lambda e: jump_focus(e, export_btn))

ttk.Label(main_frame, text="Currency").grid(row=3, column=0, sticky="w")
ttk.Combobox(main_frame, textvariable=currency_var, values=["₹", "$", "€", "£"]).grid(row=3, column=1, pady=5)

ttk.Label(main_frame, text="Type").grid(row=4, column=0, sticky="w")
ttk.Combobox(main_frame, textvariable=type_var, values=["Simple", "Compound", "EMI"]).grid(row=4, column=1, pady=5)

ttk.Label(main_frame, text="Frequency").grid(row=5, column=0, sticky="w")
ttk.Combobox(main_frame, textvariable=frequency_var, values=list(freq_map.keys())).grid(row=5, column=1, pady=5)

ttk.Button(main_frame, text="Calculate", command=calculate).grid(row=6, columnspan=2, pady=15)

result_label = ttk.Label(main_frame, text="", font=("Arial", 12), wraplength=450, foreground="green")
result_label.grid(row=7, columnspan=2, pady=10)

chart_frame = ttk.Frame(main_frame)
chart_frame.grid(row=8, columnspan=2)

export_btn = ttk.Button(main_frame, text="Export to PDF", command=export_pdf)
export_btn.grid(row=9, columnspan=2, pady=10)

# === Notes Tab ===
note_tab = ttk.Frame(notebook)
notebook.add(note_tab, text="Notes")

note_frame = ttk.Frame(note_tab, padding=20)
note_frame.pack(fill="both", expand=True)

ttk.Label(note_frame, text="Select Note Category:").pack(anchor="w")
ttk.Combobox(note_frame, textvariable=note_type_var, values=list(notes_data.keys()), state="readonly").pack(fill="x", pady=5)
ttk.Button(note_frame, text="Show Settings", command=show_note_details).pack(pady=5)

note_output = tk.Text(note_frame, height=10, wrap='word', state='disabled')
note_output.pack(fill="both", expand=True)

note_type_var.trace_add("write", show_note_details)

root.mainloop()
