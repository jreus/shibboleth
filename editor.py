import tkinter as tk


root = tk.Tk()

# specify size of window.
root.geometry("550x570")

# Create text widget and specify size.
T = tk.Text(root, height = 35, width = 80)

# Create label
l = tk.Label(root, text = "Fact of the Day")
l.config(font =("Courier", 14))

Fact = """A man can be arrested in
Italy for wearing a skirt in public."""

# Create button for next text.
b1 = tk.Button(root, text = "Next", )

# Create an Exit button.
b2 = tk.Button(root, text = "Exit",
			command = root.destroy)

l.pack()
T.pack()
b1.pack()
b2.pack()

# Insert The Fact.
T.insert(tk.END, Fact)

tk.mainloop()
