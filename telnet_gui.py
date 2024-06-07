import tkinter as tk
from tkinter import filedialog, messagebox
import telnetlib
import threading

class SCPITelnetClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        try:
            self.connection = telnetlib.Telnet(self.host, self.port)
        except Exception as e:
            raise ConnectionError(f"Connection to {self.host}:{self.port} failed: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def send_command(self, command):
        if not self.connection:
            raise ConnectionError(f"Not connected to {self.host}:{self.port}.")
        self.connection.write(command.encode('ascii') + b'\n')
        return self.connection.read_until(b'\n').decode('ascii').strip()

class SCPIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCPI Telnet Client - Multiport")
        self.clients = {}
        self.responses = {}

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.ip_label = tk.Label(self.root, text="IP:")
        self.ip_entry = tk.Entry(self.root)
        self.port_label = tk.Label(self.root, text="Ports (comma-separated):")
        self.port_entry = tk.Entry(self.root)

        self.connect_button = tk.Button(self.root, text="Connect", command=self.connect)
        self.disconnect_button = tk.Button(self.root, text="Disconnect", command=self.disconnect)

        self.command_listbox = tk.Listbox(self.root)
        self.command_listbox.insert(tk.END, "*IDN?")
        self.command_listbox.insert(tk.END, "MEAS:VOLT?")
        self.send_button = tk.Button(self.root, text="Send Command", command=self.send_command)

        self.response_text = tk.Text(self.root, height=10, width=50)
        self.save_button = tk.Button(self.root, text="Save Responses", command=self.save_responses)

    def create_layout(self):
        self.ip_label.grid(row=0, column=0, sticky=tk.W)
        self.ip_entry.grid(row=0, column=1, sticky=tk.EW)
        self.port_label.grid(row=1, column=0, sticky=tk.W)
        self.port_entry.grid(row=1, column=1, sticky=tk.EW)

        self.connect_button.grid(row=0, column=2, sticky=tk.EW)
        self.disconnect_button.grid(row=1, column=2, sticky=tk.EW)

        self.command_listbox.grid(row=2, column=0, columnspan=3, sticky=tk.EW)
        self.send_button.grid(row=3, column=0, columnspan=3, sticky=tk.EW)

        self.response_text.grid(row=4, column=0, columnspan=3, sticky=tk.EW)
        self.save_button.grid(row=5, column=0, columnspan=3, sticky=tk.EW)

    def connect(self):
        ip = self.ip_entry.get()
        ports = self.port_entry.get().split(',')
        if not ip or not ports:
            messagebox.showerror("Error", "IP and Ports must be specified.")
            return
        for port in ports:
            try:
                port = int(port.strip())
                client = SCPITelnetClient(ip, port)
                client.connect()
                self.clients[port] = client
                messagebox.showinfo("Info", f"Connected to {ip}:{port} successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def disconnect(self):
        for port, client in self.clients.items():
            client.disconnect()
        self.clients.clear()
        messagebox.showinfo("Info", "Disconnected all connections successfully.")

    def send_command(self):
        command = self.command_listbox.get(tk.ACTIVE)
        if not command:
            messagebox.showerror("Error", "No command selected.")
            return

        self.responses.clear()
        threads = []

        for port, client in self.clients.items():
            thread = threading.Thread(target=self.send_command_to_client, args=(client, command, port))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for port, response in self.responses.items():
            self.response_text.insert(tk.END, f"{port}: {command} -> {response}\n")

    def send_command_to_client(self, client, command, port):
        try:
            response = client.send_command(command)
            self.responses[port] = response
        except Exception as e:
            self.responses[port] = str(e)

    def save_responses(self):
        responses = self.response_text.get(1.0, tk.END)
        if not responses.strip():
            messagebox.showwarning("Warning", "No responses to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(responses)
            messagebox.showinfo("Info", "Responses saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SCPIApp(root)
    root.mainloop()
