import tkinter
from datetime import datetime
from time import time, sleep
import threading
from itertools import cycle
from random import randint
from requests_futures.sessions import FuturesSession
from PIL import ImageTk, Image
import requests
import json


class InvalidAccountError(Exception):
    pass


class Name:

    def __init__(self, request_name, email, password, username, delay):
        # Try to Authenticate
        try:
            self.username = username
            self.password = password
            self.email = email
            self.request_name = request_name
            self.uuid = None
            self.token = None
            self.client_token = None
            self.status = None
            self.superss = None
            self.sent_time = None
            self.authenticate()
            self.refresh = time()
            self.hold = 3196800000
            if delay == "":
                self.await_drop_time = .1
            else:
                try:
                    self.await_drop_time = float(delay)
                except:
                    gui.field_error(error_message="Your Delay Must Be A Number!")

            self.session = FuturesSession()
            self.useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                             '(KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

            if self.token is not None:
                s = requests.get(f'https://api.mojang.com/user/security/location',
                                headers={'Authorization': "Bearer " + str(self.token),
                                         'User-Agent': self.useragent})
                sc = requests.get(f'https://api.mojang.com/user/security/challenges',
                                headers={'Authorization': "Bearer " + str(self.token),
                                         'User-Agent': self.useragent})

                if s.status_code != 403 or not sc.content:
                    target_availability = self.check_availabilty(request_name)
                    if target_availability is not None:
                        self.target_availability = target_availability
                        gui.clear_fields()
                        gui.display_availability(target_availability)
                        snipe_thread = threading.Thread(target=self.await_snipe, args=(self.target_availability,))
                        snipe_thread.start()
                    else:
                        gui.field_error(error_message="Target Username Is Unavailable!")
                else:
                    gui.field_error(error_message=f"Login To Minecraft.net\n IP Not Authorized For This Account!")
            else:
                gui.field_error(error_message="Your Information Is Incorrect!")

        except:
            gui.field_error(error_message="Your Information Is Incorrect!")

    def get_uuid(self, timestamp, username):
        if timestamp is None:
            timestamp_now = int(time() * 1000.0)
            timestamp = int((timestamp_now - self.hold) / 1000)

        resp = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}?at={timestamp}")
        if resp.ok:
            try:
                return resp.json()["id"]
            except json.decoder.JSONDecodeError:
                return None
        return None

    def authenticate(self):
        res = requests.post(
            "https://authserver.mojang.com/authenticate",
            json={
                "agent": {"name": "Minecraft", "version": 1},
                "username": self.email,
                "password": self.password,
            },
            headers={"Content-Type": "application/json"},
        )

        if res.status_code == 403:
            raise InvalidAccountError
        else:
            jsondata = res.json()
            self.token = jsondata["accessToken"]
            self.client_token = jsondata["clientToken"]
            try:
                self.uuid = jsondata["selectedProfile"]["id"]
            except KeyError:
                pass

    def refresh_authentication(self):
        payload = {
            'accessToken': f"Bearer {self.token}",
            "clientToken": self.client_token,
        }
        res = requests.post('https://authserver.mojang.com/refresh', json=payload)
        jsondata = res.json()
        print(jsondata)
        return jsondata["accessToken"]

    def get_drop_stamp(self):
        uuid = self.get_uuid(timestamp=None, username=self.request_name)
        if not uuid:
            raise InvalidAccountError
        resp = requests.get(f"https://api.mojang.com/user/profiles/{uuid}/names")
        name_changes = [name_change for name_change in reversed(resp.json())]
        for i, name_info in enumerate(name_changes):
            if name_info["name"].lower() == self.request_name.lower():
                try:
                    name_changed_timestamp = name_changes[i - 1]["changedToAt"]
                    drop_timestamp = (name_changed_timestamp + self.hold) / 1000
                    return drop_timestamp
                except KeyError:
                    return None

    def get_challenges(self):
        res = requests.get(
            "https://api.mojang.com/user/security/challenges",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return res.json()

    def check_availabilty(self, username):
        try:
            target_availability = self.get_drop_stamp()
            if target_availability is None:
                if self.request_name.lower() == username.lower():
                    return 0
                else:
                    return None
            else:
                return target_availability

        except:
            return 0

    def update_token(self):
        if time() - self.refresh >= 260:
            try:
                token = self.refresh_authentication()
                self.token = token
                self.get_challenges()
                self.refresh = time()
            except:
                self.authenticate()
                self.get_challenges()

    def check_name(self):
        try:
            future_one = self.session.get(f"https://api.mojang.com/users/profiles/minecraft/{self.request_name}")
            response_one = future_one.result().json()
            response_one = str(response_one['id'])
            if response_one == str(self.uuid):
                gui.congratulations(message=f"Snipe Successful, Your name was successfully changed to {self.request_name}")
                return False
            else:
                gui.sad()
                return False
        except:
            return True
        # if username is assoicated with some1 elses uuid and not equal to player .uuid break
        # use mojang package if return None or error pass {else}

    def await_snipe(self, availability):
        super_snipe_thread = threading.Thread(target=self.supersnipe, args=(self.target_availability,))
        super_snipe_thread.start()
        drop = availability - time()
        while drop >= self.await_drop_time:
            sleep(.01)
            self.update_token()
            drop = availability - time()

        gui.display_snipe()
        self.snipe()

    def snipe(self):
        self.quicksnipe()
        x = self.check_name()
        try:
            with open('Response.txt', 'w') as f:
                f.write(f'{self.superss.content}, {self.superss.status_code}, {self.sent_time}')
        except:
            pass
        sleep(660)
        snipes = 0
        snipe_time = time()
        while x:
            self.session.post(f'https://api.mojang.com/user/profile/{self.uuid}/name',
                              headers={'Authorization': f"Bearer {self.token}", 'User-Agent': self.useragent},
                              json={"name": self.request_name, "password": self.password})

            self.update_token()
            if snipes >= 595:
                x = self.check_name()
                sleep_time_2 = time() - snipe_time
                if sleep_time_2 <= 600:
                    sleep((600 - sleep_time_2 + 1))
                snipes = 1
                snipe_time = time()
            else:
                snipes += 1
            sleep_time = randint(0, 20)
            sleep((sleep_time / 10))  # numbers between 0 and 2

    def quicksnipe(self):
        for number in range(0, 560):
            s = self.session.post(f'https://api.mojang.com/user/profile/{self.uuid}/name',
                              headers={'Authorization': f"Bearer {self.token}", 'User-Agent': self.useragent},
                              json={"name": self.request_name, "password": self.password})

            if time() - self.target_availability >= 3 or self.target_availability == 0:
                break
            num = randint(0, 10)
            num = num / 1000
            sleep(num)
        sleep(5)

    def supersnipe(self, availability):
        delay = .01 + self.request_delay()
        drop = (availability - time() - delay)
        if drop > 0:
            sleep(drop)
        self.sent_time = time()
        self.send_super_snipe()

    def send_super_snipe(self):
        self.superss = requests.post(f'https://api.mojang.com/user/profile/{self.uuid}/name',
                              headers={'Authorization': f"Bearer {self.token}", 'User-Agent': self.useragent},
                              json={"name": self.request_name, "password": self.password})

    def request_delay(self):
        rt = time()
        self.superss = requests.post(f'https://api.mojang.com/user/profile/{self.uuid}/name',
                              headers={'Authorization': f"Bearer {self.token}", 'User-Agent': self.useragent},
                              json={"name": self.request_name, "password": self.password})
        at = time()
        return ((at - rt) / 2) - .05


class Tk:

    def __init__(self):
        # Initialize Tkinter
        self.tk = tkinter.Tk()
        self.tk.title("QSNIPE")
        self.tk.geometry("920x680")
        self.lable = tkinter.Label(self.tk, text="QSNIPE V5\t QUICKSNIPE", bg="#3C3939", fg="white", font="none 22 bold").place(anchor='nw')
        self.tk.configure(bg='#3C3939')

        # Target
        self.label_target = tkinter.Label(self.tk, text="Target Username:", bg="#3C3939", fg="white",
                                            font="none 18 bold")
        self.field_request_name = tkinter.Entry(self.tk, width=16)

        # Logo
        self.logo = ImageTk.PhotoImage(Image.open("logo.png"))
        self.logo_image = tkinter.Label(self.tk, image=self.logo, borderwidth=0, relief="flat", bg="#3C3939")

        # User Information
        self.label_information = tkinter.Label(self.tk, text="Your Information", bg="#3C3939", fg="white",
                                            font="none 17 bold")

        self.label_username = tkinter.Label(self.tk, text="Your Username:", bg="#3C3939", fg="white", font="none 14 bold")
        self.field_username = tkinter.Entry(self.tk, width=20, bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939")

        self.label_email = tkinter.Label(self.tk, text="Your Email:", bg="#3C3939", fg="white", font="none 14 bold")
        self.field_email = tkinter.Entry(self.tk, width=20, bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939")

        self.label_password = tkinter.Label(self.tk, text="Your Password:", bg="#3C3939", fg="white", font="none 14 bold")
        self.field_password = tkinter.Entry(self.tk, width=20, bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939")

        self.label_delay = tkinter.Label(self.tk, text="Leave Blank For Default Delay:", bg="#3C3939", fg="white", font="none 14 bold")
        self.field_delay = tkinter.Entry(self.tk, width=3, bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939")

        # Submit
        self.field_submit_button = tkinter.Button(self.tk, text="Submit", highlightbackground="black", fg='black', font="none 24 bold", command=self.field_submit)

        # Error
        self.error = tkinter.Label(self.tk, bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939", text="ERROR")

        # Text
        self.text = cycle(["#.........", "##........", "###.......", "####......", "#####.....", "######....", "#######...", "########..", "#########.", "##########"])
        self.label_symbol = tkinter.Label(self.tk, text="|", bg="#3C3939", fg="green", font="none 19 bold")

        # Main Menu
        self.main_button_snipe = tkinter.Button(self.tk, highlightbackground="grey", text="Snipe", font="none 24 bold", command=self.snipe_quick, padx=194.5, pady=40)
        self.main_button_quit = tkinter.Button(self.tk, text="Quit", highlightbackground="grey", font="none 24 bold", command=self.tk.destroy, padx=200, pady=40)

    def snipe_quick(self):
        self.clear_main_menu()
        self.grid_fields()

    def clear_main_menu(self):
        self.main_button_snipe.place_forget()
        self.main_button_quit.place_forget()

    def main_menu(self):
        self.main_button_snipe.place(relx=0.5, rely=0.3, anchor='center')
        self.main_button_quit.place(relx=0.5, rely=0.85, anchor='s')

    def run(self):
        self.main_menu()
        self.tk.mainloop()

    def check_status(self):
        status = requests.get('https://status.mojang.com/check')
        status = status.json()
        status = status[5]
        self.status = status['api.mojang.com']

    def field_submit(self):
        self.check_status()
        self.error.place_forget()
        target = self.field_request_name.get()
        email = self.field_email.get()
        password = self.field_password.get()
        username = self.field_username.get()
        delay = self.field_delay.get()

        if self.status == 'green':
            if username == target and username != "":
                self.field_error(error_message="You Cannot Snipe Your Own Name!")

            elif target != "" and email != "" and password != "" and username != "":
                self.snipe = Name(target, email, password, username, delay)
            else:
                self.field_error(error_message="Fill Out All Required Fields!")
        else:
            self.field_error(error_message="Cannot Connect To Mojang Services")

    def field_error(self, error_message):
        n = 0
        if n == 1:
            self.error.place_forget()
        self.error = tkinter.Label(self.tk,  bg="#565151", fg="white", font="none 14 bold", highlightbackground="#3C3939", text=error_message)
        self.error.place(relx=0.6, rely=0.9, anchor='sw')

    def display_availability(self, target_availability):
        self.target_availability = target_availability
        if self.target_availability == 0:
            text = f'{self.field_request_name.get()} Is Available!'
        else:
            unix_time = datetime.fromtimestamp(self.target_availability)
            unix_time = unix_time.strftime("%Y-%m-%d, %I:%M:%S %p")
            text = f'{self.field_request_name.get()} Is Available At {unix_time}'
            self.display_drop_event = self.tk.after(1000, self.display_drop)
            self.timer_object = self.tk.after(1000, self.update_symbol)
            self.logo_image.place_forget()

        self.label_available = tkinter.Label(self.tk, text=text, bg="#3C3939", fg="white", font="none 19 bold")
        self.label_available.grid(row=2, column=0, pady=60)

    def display_drop(self):
        text = f"Time Remaining Till Drop of {self.snipe.request_name}: {int(round(self.target_availability - time(), 0))} Seconds"
        self.label_drop = tkinter.Label(self.tk, text=text, bg="#3C3939", fg="white", font="none 16 bold")
        self.label_drop.grid(row=3, column=0, pady=10)
        self.display_drop_event = self.tk.after(1000, self.display_drop) #add more padding, remove sniper picture, fix cycle jeez, make sure quicksnipeworks, #maybe change congrats and sad to display something else if targetname.low == self.user.lower()

    def display_snipe(self):
        self.label_available.grid_forget()
        try:
            self.label_drop.grid_forget()
        except AttributeError:
            pass
        try:
            self.tk.after_cancel(self.display_drop_event)
        except:
            pass
        try:
            self.logo_image.place_forget()
        except:
            pass
        text = "Sniping Process Started And ACTIVE: "
        self.label_snipe = tkinter.Label(self.tk, text=text, bg="#3C3939", fg="white", font="none 19 bold")
        self.label_snipe.grid(row=3, column=0, pady=30)
        try:
            self.tk.after_cancel(self.timer_object)
        except:
            pass
        self.timer_object = self.tk.after(1000, self.update_symbol)

    def update_symbol(self):
        try:
            self.label_symbol.grid_forget()
        except:
            pass
        self.label_symbol.configure(text=next(self.text))
        self.label_symbol.grid(row=3, column=1)
        self.timer_object = self.tk.after(1000, self.update_symbol)

    def congratulations(self, message):
        try:
            self.tk.after_cancel(self.timer_object)
            self.label_symbol.grid_forget()
        except:
            pass
        self.label_congrats = tkinter.Label(self.tk, text=message, bg="#3C3939", fg="green", font="none 22 bold")
        self.label_congrats.grid(row=3, column=0)

    def sad(self):
        try:
            self.tk.after_cancel(self.timer_object)
            self.label_symbol.grid_forget()
        except:
            pass
        self.label_sad = tkinter.Label(self.tk, text="Someone Else Sniped The Name :(", bg="#3C3939", fg="red", font="none 22 bold")
        self.label_sad.grid(row=3, column=0)

    def grid_fields(self):
        self.logo_image.place(relx=.5, anchor='nw')

        self.label_target.grid(row=2, column=0, pady=90)
        self.field_request_name.grid(row=2, column=1, pady=90)

        self.label_information.grid(row=3, pady=5)

        self.label_username.grid(row=4, pady=20)
        self.field_username.grid(row=4, column=1, pady=20)

        self.label_email.grid(row=6, pady=20)
        self.field_email.grid(row=6, column=1, pady=20)

        self.label_password.grid(row=7, pady=6)
        self.field_password.grid(row=7, column=1, pady=20)

        self.field_submit_button.grid(row=6, column=2, pady=30, padx=120)

        self.label_delay.grid(row=3, column=2, padx=120)
        self.field_delay.grid(row=4, column=2, padx=120)

    def clear_fields(self):
        try:
            self.error.place_forget()
        except:
            pass
        self.field_request_name.grid_forget()
        self.label_information.grid_forget()
        self.field_email.grid_forget()
        self.field_password.grid_forget()
        self.field_username.grid_forget()
        self.field_submit_button.grid_forget()
        self.label_password.grid_forget()
        self.label_target.grid_forget()
        self.label_email.grid_forget()
        self.label_username.grid_forget()
        self.label_delay.grid_forget()
        self.field_delay.grid_forget()


if __name__ == '__main__':
    gui = Tk()
    gui.run()

