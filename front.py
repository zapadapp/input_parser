import tkinter
import tkinter.messagebox
from unicodedata import name
import customtkinter
from PIL import Image, ImageTk
import os
import recorder
from threading import Thread
import time
import pyaudio

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATH = os.path.dirname(os.path.realpath(__file__))

class App(customtkinter.CTk):

    WIDTH = 1024
    HEIGHT = 780

    def __init__(self):
        super().__init__()

        self.audio = pyaudio.PyAudio()
        self.title("zapadapp")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        # ============ create two frames ============

        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_rowconfigure(0, minsize=10)   # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(5, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)    # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        self.label_1 = customtkinter.CTkLabel(master=self.frame_left,
                                              text="ZAPADAPP",
                                              text_font=("Roboto Medium", -16))  # font name and size in px
        self.label_1.grid(row=1, column=0, pady=10, padx=10)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Play!",
                                                command=self.button_event)
        self.button_1.grid(row=2, column=0, pady=10, padx=20)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Saved",
                                                command=self.button_event)
        self.button_2.grid(row=3, column=0, pady=10, padx=20)

        self.label_mode = customtkinter.CTkLabel(master=self.frame_left, text="Appearance Mode:")
        self.label_mode.grid(row=9, column=0, pady=0, padx=20, sticky="w")

        self.optionmenu_1 = customtkinter.CTkOptionMenu(master=self.frame_left,
                                                        values=["Light", "Dark", "System"],
                                                        command=self.change_appearance_mode)
        self.optionmenu_1.grid(row=10, column=0, pady=10, padx=20, sticky="w")

        # ============ frame_right ============

        # configure grid layout (3x7)
        self.frame_right.rowconfigure((0, 1, 2, 3), weight=1)
        self.frame_right.rowconfigure(7, weight=10)
        self.frame_right.columnconfigure((0, 1), weight=1)
        self.frame_right.columnconfigure(2, weight=0)

    
        # ============ frame_info ============


        self.frame_info = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_info.grid(row=2, column=0, columnspan=3, rowspan=4, pady=20, padx=20, sticky="we")
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)

        # self.label_info_1 = customtkinter.CTkLabel(master=self.frame_right,
        #                                            text="CTkLabel: Lorem ipsum dolor sit,\n" +
        #                                                 "amet consetetur sadipscing elitr,\n" +
        #                                                 "sed diam nonumy eirmod tempor" ,
        #                                            height=100,
        #                                            fg_color=("white", "gray38"),  # <- custom tuple-color
        #                                            justify=tkinter.LEFT)
        # self.label_info_1.grid(column=1, row=2, sticky="nwe", padx=15, pady=15)


        image = Image.open(PATH + "/tmp/score.png").resize((500, 200))
        self.bg_image = ImageTk.PhotoImage(image)

        self.image_label = tkinter.Label(master=self.frame_info, image=self.bg_image)
        self.image_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        # ============ frame_right ============
       
        self.combobox_1 = customtkinter.CTkComboBox(master=self.frame_right,
                                                    values=[ "Device 1", "Device 2"], command=self.combobox_func)
        self.combobox_1.grid(row=0, column=0, columnspan=1, pady=10, padx=20, sticky="we")

        recordImg = ImageTk.PhotoImage(Image.open("img/record.png"))
        stopImg = ImageTk.PhotoImage(Image.open("img/stop.png"))
        saveImg = ImageTk.PhotoImage(Image.open("img/save.png"))

        self.recButton = customtkinter.CTkButton(master=self.frame_right, image=recordImg, text="", bg_color="#FFF", command=self.record_action)
        self.recButton.grid(row=6, column=0, columnspan=1, pady=20, padx=20, sticky="we")

        self.stopButton = customtkinter.CTkButton(master=self.frame_right, image=stopImg, text="", command=self.stop_action)
        self.stopButton.grid(row=6, column=1, columnspan=1, pady=20, padx=20, sticky="we")
 
        self.saveButton = customtkinter.CTkButton(master=self.frame_right, image=saveImg, text="",command=self.refresh_score)
        self.saveButton.grid(row=6, column=2, columnspan=1, pady=20, padx=20, sticky="we")

        # set default values
        self.optionmenu_1.set("Dark")
        #self.button_3.configure(state="disabled", text="Disabled CTkButton")
        self.combobox_1.set("Select device")
        #self.radio_button_1.select()
        #self.slider_1.set(0.2)
        #self.slider_2.set(0.7)
        #self.progressbar.set(0.5)
        #self.switch_2.select()
        #self.radio_button_3.configure(state=tkinter.DISABLED)
        #self.check_box_1.configure(state=tkinter.DISABLED, text="CheckBox disabled")
        #self.check_box_2.select()

    def button_event(self):
        print("Button pressed")

    def record_action(self):
        self.rec = recorder.Recorder("file.wav", "score")
        self.rec.setup(self.deviceChoice)
        recorderThread = Thread(target = self.rec.record, args =())
        
        recorderThread.start()

        imgUpdater = Thread(target = self.refresh_score, args = ())
        imgUpdater.start()

    def stop_action(self):    
        print("stop button")
        self.rec.stop()
        self.rec.close()

    def refresh_score(self):
        while True:
            image = Image.open(PATH + "/tmp/score.png").resize((500, 200))
            self.bg_image = ImageTk.PhotoImage(image)

            self.image_label.configure(image=self.bg_image)
            self.image_label.image = image
            time.sleep(0.5)

    def update_devices(self):
        print("update devices")    

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)
    
    def get_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        newValues = []
        # show all input devices found.
        # print("Input Device id ", i, " - ", self.audio.get_device_info_by_host_api_device_index(0, i).get('name'))

        for i in range(0, numdevices):
            if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                newValues.append("{} #{}".format(self.audio.get_device_info_by_host_api_device_index(0, i).get('name'),i))

        self.combobox_1.configure(values= newValues)        
    
    def combobox_func(self, choice):
        if choice == "Select device":
            return

        s = choice.split("#")
        self.deviceChoice = int(s[1])

    def on_closing(self, event=0):
        self.destroy()
    


if __name__ == "__main__":
    app = App()
    app.get_devices()
    app.mainloop()