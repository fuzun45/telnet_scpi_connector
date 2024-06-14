import socket
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from scpi_commands import SCPICommands  # SCPI komutlarını içe aktarma

class SCPISocketClient:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        try:
            self.connection = socket.create_connection((self.host, self.port), timeout=5)
        except Exception as e:
            raise ConnectionError(f"Connection to {self.host}:{self.port} failed: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def send_command(self, command, expect_response=True, timeout=5):
        if not self.connection:
            raise ConnectionError(f"Not connected to {self.host}:{self.port}.")
        try:
            self.connection.sendall((command + '\n').encode('ascii'))
            if expect_response:
                self.connection.settimeout(timeout)
                response = self.connection.recv(1024).decode('ascii').strip()
                if not response:
                    raise TimeoutError("No response from the device.")
                return response
            return "No response expected"
        except socket.timeout:
            raise TimeoutError("Timeout waiting for response")
        except Exception as e:
            raise RuntimeError(f"Error sending command to {self.host}:{self.port}: {e}")

class SCPIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCPI Socket Client - Multiport")
        self.clients = {"loads": {}, "sources": {}}
        self.responses = {}

        self.create_widgets()
        self.create_layout()
        self.bind_placeholder_events()

    def create_widgets(self):
        self.ip_label = tk.Label(self.root, text="IP:")
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.insert(0, "10.3.200.10")

        self.load_ports_label = tk.Label(self.root, text="Load Ports (comma-separated):")
        self.load_ports_entry = tk.Entry(self.root)
        self.load_ports_entry.insert(0, "5000")

        self.source_ports_label = tk.Label(self.root, text="Source Ports (comma-separated):")
        self.source_ports_entry = tk.Entry(self.root)
        self.source_ports_entry.insert(0, "5000")

        self.voltage_label = tk.Label(self.root, text="Set Voltage (V):")
        self.voltage_entry = tk.Entry(self.root)
        self.current_label = tk.Label(self.root, text="Set Current (A):")
        self.current_entry = tk.Entry(self.root)

        self.load_file_button = tk.Button(self.root, text="Load from CSV", command=self.load_from_csv)
        self.connect_button = tk.Button(self.root, text="Connect", command=self.connect)
        self.disconnect_button = tk.Button(self.root, text="Disconnect", command=self.disconnect)

        self.command_listbox = tk.Listbox(self.root)
        self.command_listbox.insert(tk.END, "*IDN?")
        self.command_listbox.insert(tk.END, "*RST")
        self.command_listbox.insert(tk.END, "SYST:REM")
        self.command_listbox.insert(tk.END, "SYST:LOC")
        self.command_listbox.insert(tk.END, "SYST:VERS?")
        self.command_listbox.insert(tk.END, "SYST:ERR?")
        self.command_listbox.insert(tk.END, "OUTP ON")
        self.command_listbox.insert(tk.END, "OUTP OFF")
        self.command_listbox.insert(tk.END, "VOLT?")
        self.command_listbox.insert(tk.END, "CURR?")
        self.command_listbox.insert(tk.END, ":CHANnel 1")
        self.command_listbox.insert(tk.END, ":CHANnel 2")
        self.command_listbox.insert(tk.END, ":SOURce:INPut:STATe 1")
        self.command_listbox.insert(tk.END, ":SOURce:INPut:STATe 0")
        self.command_listbox.insert(tk.END, "STAT:CHAN:ENAB 1")
        self.command_listbox.insert(tk.END, ":FUNCtion CURR")
        self.command_listbox.insert(tk.END, ":FUNCtion RES")
        self.command_listbox.insert(tk.END, "CURR 5") #STAT:CHAN:ENAB 3
        self.command_listbox.insert(tk.END, "RES 5") #STAT:CHAN:ENAB 3
        
        self.load_button = tk.Button(self.root, text="Send Command to Loads", command=lambda: self.send_command("loads"))
        self.source_button = tk.Button(self.root, text="Send Command to Sources", command=lambda: self.send_command("sources"))

        self.set_voltage_button = tk.Button(self.root, text="Set Voltage", command=self.set_voltage)
        self.set_current_button = tk.Button(self.root, text="Set Current", command=self.set_current)

        self.response_text = tk.Text(self.root, height=10, width=50)
        self.save_button = tk.Button(self.root, text="Save Responses", command=self.save_responses)

    def create_layout(self):
        self.ip_label.grid(row=0, column=0, sticky=tk.W)
        self.ip_entry.grid(row=0, column=1, sticky=tk.EW)
        self.load_ports_label.grid(row=1, column=0, sticky=tk.W)
        self.load_ports_entry.grid(row=1, column=1, sticky=tk.EW)
        self.source_ports_label.grid(row=2, column=0, sticky=tk.W)
        self.source_ports_entry.grid(row=2, column=1, sticky=tk.EW)

        self.voltage_label.grid(row=3, column=0, sticky=tk.W)
        self.voltage_entry.grid(row=3, column=1, sticky=tk.EW)
        self.current_label.grid(row=4, column=0, sticky=tk.W)
        self.current_entry.grid(row=4, column=1, sticky=tk.EW)

        self.load_file_button.grid(row=5, column=0, columnspan=2, sticky=tk.EW)
        self.connect_button.grid(row=0, column=2, sticky=tk.EW)
        self.disconnect_button.grid(row=1, column=2, sticky=tk.EW)

        self.command_listbox.grid(row=6, column=0, columnspan=3, sticky=tk.EW)
        self.load_button.grid(row=7, column=0, columnspan=3, sticky=tk.EW)
        self.source_button.grid(row=8, column=0, columnspan=3, sticky=tk.EW)

        self.set_voltage_button.grid(row=3, column=2, sticky=tk.EW)
        self.set_current_button.grid(row=4, column=2, sticky=tk.EW)

        self.response_text.grid(row=9, column=0, columnspan=3, sticky=tk.EW)
        self.save_button.grid(row=10, column=0, columnspan=3, sticky=tk.EW)

    def bind_placeholder_events(self):
        self.ip_entry.bind("<FocusIn>", self.clear_ip_placeholder)
        self.load_ports_entry.bind("<FocusIn>", self.clear_load_ports_placeholder)
        self.source_ports_entry.bind("<FocusIn>", self.clear_source_ports_placeholder)

    def clear_ip_placeholder(self, event):
        if self.ip_entry.get() == "127.0.0.1":
            self.ip_entry.delete(0, tk.END)

    def clear_load_ports_placeholder(self, event):
        if self.load_ports_entry.get() == "5025":
            self.load_ports_entry.delete(0, tk.END)

    def clear_source_ports_placeholder(self, event):
        if self.source_ports_entry.get() == "5026":
            self.source_ports_entry.delete(0, tk.END)

    def load_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row['Name']
                ip = row['IP']
                port = int(row['Port'])
                device_type = row['Type'].lower()
                client = SCPISocketClient(name, ip, port)
                self.clients[device_type][port] = client

        messagebox.showinfo("Info", "Loaded configuration from CSV successfully.")

    def connect(self):
        ip = self.ip_entry.get()
        load_ports = self.load_ports_entry.get().split(',')
        source_ports = self.source_ports_entry.get().split(',')
        if not ip or not (load_ports or source_ports):
            messagebox.showerror("Error", "IP and Ports must be specified.")
            return

        for port in load_ports:
            try:
                port = int(port.strip())
                client = SCPISocketClient(f"Load-{port}", ip, port)
                client.connect()
                self.clients["loads"][port] = client
                messagebox.showinfo("Info", f"Connected to load at {ip}:{port} successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        for port in source_ports:
            try:
                port = int(port.strip())
                client = SCPISocketClient(f"Source-{port}", ip, port)
                client.connect()
                self.clients["sources"][port] = client
                messagebox.showinfo("Info", f"Connected to source at {ip}:{port} successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def disconnect(self):
        for port, client in self.clients["loads"].items():
            client.disconnect()
        for port, client in self.clients["sources"].items():
            client.disconnect()
        self.clients = {"loads": {}, "sources": {}}
        messagebox.showinfo("Info", "Disconnected all connections successfully.")

    def send_command(self, device_type):
        command = self.command_listbox.get(tk.ACTIVE)
        if not command:
            messagebox.showerror("Error", "No command selected.")
            return

        expect_response = command.endswith("?")
        self.responses.clear()
        threads = []

        for port, client in self.clients[device_type].items():
            thread = threading.Thread(target=self.send_command_to_client, args=(client, command, port, expect_response))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for port, response in self.responses.items():
            self.response_text.insert(tk.END, f"{self.clients[device_type][port].name} ({port}): {command} -> {response}\n")

    def send_command_to_client(self, client, command, port, expect_response):
        try:
            response = client.send_command(command, expect_response)
            self.responses[port] = response
        except ConnectionError as e:
            self.responses[port] = f"Connection Error: {str(e)}"
        except TimeoutError as e:
            self.responses[port] = f"Timeout Error: {str(e)}"
        except RuntimeError as e:
            self.responses[port] = f"Runtime Error: {str(e)}"
        except Exception as e:
            self.responses[port] = f"Error: {str(e)}"

    def set_voltage(self):
        voltage = self.voltage_entry.get()
        if not voltage:
            messagebox.showerror("Error", "Voltage value must be specified.")
            return
        command = f"VOLT {voltage}"
        self.send_custom_command(command)

    def set_current(self):
        current = self.current_entry.get()
        if not current:
            messagebox.showerror("Error", "Current value must be specified.")
            return
        command = f"CURR {current}"
        self.send_custom_command(command)

    def send_custom_command(self, command):
        device_type = "loads"  # veya "sources", duruma göre değiştirin
        self.responses.clear()
        threads = []

        for port, client in self.clients[device_type].items():
            thread = threading.Thread(target=self.send_command_to_client, args=(client, command, port, False))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for port, response in self.responses.items():
            self.response_text.insert(tk.END, f"{self.clients[device_type][port].name} ({port}): {command} -> {response}\n")

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
