class SCPICommands:
    def __init__(self, client):
        self.client = client

    # Genel Komutlar
    def identify(self):
        return self.client.send_command("*IDN?")
    
    def reset(self):
        return self.client.send_command("*RST", expect_response=False)

    # Sistem Komutları
    def system_remote(self):
        return self.client.send_command("SYST:REM", expect_response=False)

    def system_local(self):
        return self.client.send_command("SYST:LOC", expect_response=False)

    def system_version(self):
        return self.client.send_command("SYST:VERS?")

    def system_error(self):
        return self.client.send_command("SYST:ERR?")

    # Çıkış Komutları
    def output_on(self):
        return self.client.send_command("OUTP ON", expect_response=False)

    def output_off(self):
        return self.client.send_command("OUTP OFF", expect_response=False)

    def set_voltage(self, voltage):
        return self.client.send_command(f"VOLT {voltage}", expect_response=False)

    def get_voltage(self):
        return self.client.send_command("VOLT?")

    def set_current(self, current):
        return self.client.send_command(f"CURR {current}", expect_response=False)

    def get_current(self):
        return self.client.send_command("CURR?")
