from tkinter import *
from tkinter import filedialog

from PIL import Image, ImageTk, ImageOps
import colorclusters.image_utils as img_utils
from colorclusters.k_means import KMeans

_img_size = (400,400)

class Window(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.master = master

        self.master.title("Color Clusters")
        self.pack(fill=BOTH, expand=1)
        self.init_menu()

        self.input_image = Image.new("RGBA", _img_size, 0)
        photo = ImageTk.PhotoImage(img_utils.add_transparency_grid(self.input_image))
        self.input_label = Label(self, image=photo)
        self.input_label.image = photo
        self.input_label.pack(side=LEFT)

        self.output_image = Image.new("RGBA", _img_size, 0)
        photo = ImageTk.PhotoImage(img_utils.add_transparency_grid(self.input_image))
        self.out_label = Label(self, image=photo)
        self.out_label.image = photo
        self.out_label.pack(side=RIGHT)

        options = Frame(self)
        Label(options, text="K value:").pack()
        entry = Entry(options, text="2")
        entry.pack()

        def callback():
            self.run_k_means(int(entry.get()))

        Button(options, text="Run K-Means", command=callback).pack()
        options.pack(side=LEFT, expand=1)
        self.message = StringVar()
        Label(options,textvariable=self.message).pack(side=BOTTOM)

    def init_menu(self):
        menu = Menu(self.master)
        self.master.config(menu=menu)

        file = Menu(menu)
        file.add_command(label="Load Image...", command=self.load_image)
        file.add_command(label="Save Image...", command=self.save_image)
        file.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file)

        edit = Menu(menu)
        edit.add_command(label="Show Text", command=self.show_text)
        menu.add_cascade(label="Edit", menu=edit)

    def load_image(self):
        filename = filedialog.askopenfilename(initialdir="../tests/images",title="Choose an image")
        if filename is "":
            return
        self.input_image = Image.open(filename)
        self.reload_image_label(self.input_image, self.input_label)

    def save_image(self):
        filename = filedialog.asksaveasfilename(
            parent=self,
            initialdir="../tests/images",
            initialfile="output.png",
            title="Save an image",
            defaultextension=".png",
            filetypes=(("PNG image","*.png"),))
        if filename is "":
            return
        self.output_image.save(filename)

    def show_text(self):
        text = Label(self, text="Testing!")
        text.pack()

    def reload_image_label(self, image, label):
        img = ImageOps.scale(image, min((expected/actual for expected,actual in zip(_img_size,image.size))))
        img = img_utils.add_transparency_grid(img)

        img_tk = ImageTk.PhotoImage(img)

        label.configure(image=img_tk)
        label.image = img_tk

    def run_k_means(self, k_value):
        self.message.set("Running!")
        kmeans = KMeans(k_value,list(self.input_image.getdata()))
        i=0
        def callback():
            nonlocal kmeans
            kmeans.shift_centroids()

            shift = max(kmeans.shift_distance)
            print(shift)
            if shift > 3:
                self.message.set("Shift: "+str(round(shift,1)))
                self.master.after_idle(callback)
            else:
                self.message.set("Done!")
                self.output_image = img_utils.map_index_to_paletted_image(
                    self.input_image.size,
                    kmeans.get_clustering(),
                    kmeans.get_centroids())

                self.reload_image_label(self.output_image, self.out_label)

        self.master.after_idle(callback)

    def client_exit(self):
        exit()

root = Tk()

root.geometry(str(_img_size[0]*3)+"x"+str(_img_size[1]))
app = Window(root)
root.mainloop()
