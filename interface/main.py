from tkinter import *
from tkinter.ttk import Notebook
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import threading
import queue
import colorclusters.image_utils as img_utils
from colorclusters.k_means import KMeans
import colorclusters.mean_shift as mean_shift
import colorclusters.distance as dist_func
import colorclusters.closest_color as closest_color

# the maximum size of the image labels
_img_size = (400, 400)
_msg_width = 300

# the amount of time between checking the thread_queue
_delay_time = 1000

# the default options for a distance function
_function_names = ['euclidean', 'manhattan', 'chebyshev', 'norm(3)', 'scaled(euclidean,(1,2,3,4))']
# the parameter names that get interpreted as a distance
_dist_param_names = ('distance', 'dist')


# links two stringvars together.
# really dumb solution to get the dropdown menu to say "custom" when the user enters something else
class DistanceStringVar(StringVar):
    def __init__(self, parent):
        StringVar.__init__(self)
        self.set(parent.get())
        self.prevent_loop = False

        def parent_callback(*args):
            self.prevent_loop = True
            if parent.get() in _function_names:
                self.set(parent.get())
            else:
                self.set('custom')
            self.prevent_loop = False

        def distance_callback(*args):
            if not self.prevent_loop:
                parent.set(self.get())

        parent.trace("w", parent_callback)
        self.trace("w", distance_callback)


class Window(Frame):
    def __init__(self, master=None):
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

        self.button_list = []
        self.timerCount = 0
        self.messageString = None
        self.timerString = None
        self.thread_queue = queue.Queue()
        self.algorithm_thread = None

        self.algorithms = Notebook(self)
        self.algorithms.pack(fill=BOTH, expand=1)

    def init_menu(self):
        menu = Menu(self.master)
        self.master.config(menu=menu)

        file = Menu(menu)
        file.add_command(label="Load Image...", command=self.load_image)
        file.add_command(label="Save Image...", command=self.save_image)
        file.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file)

    def load_image(self):
        filename = filedialog.askopenfilename(initialdir="../tests/images", title="Choose an image")
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
            filetypes=(("PNG image", "*.png"),))
        if filename is "":
            return
        self.output_image.save(filename)

    def reload_image_label(self, image, label):
        if image.size[0] > _img_size[0] or image.size[1] > _img_size[1]:
            img = ImageOps.scale(image, min((expected / actual for expected, actual in zip(_img_size, image.size))))
        else:
            img = image

        if img.mode != "RGB":
            img = img_utils.add_transparency_grid(img)

        img_tk = ImageTk.PhotoImage(img)

        label.configure(image=img_tk)
        label.image = img_tk

    def set_button_state(self, state):
        for button in self.button_list:
            button.config(state=state)

    def run_algorithm(self, algorithm_runner, **kwargs):
        self.messageString.set("Running!")
        self.set_button_state(DISABLED)

        # set required arguments
        if 'image' not in kwargs:
            kwargs['image'] = self.input_image
        if 'thread_queue' not in kwargs:
            kwargs['thread_queue'] = self.thread_queue

        # start the algorithm on a separate thread
        self.algorithm_thread = threading.Thread(
            target=algorithm_runner,
            kwargs=kwargs,
            daemon=True)
        self.algorithm_thread.start()
        self.after(_delay_time, self.listen_for_result)

    def add_algorithm(self, name, algorithm, **kwargs):
        options = Frame(self.algorithms)
        options.pack(fill=BOTH, expand=1)
        message = StringVar()
        timer = StringVar()
        Label(options, textvariable=timer).pack(side=BOTTOM)
        Message(options, textvariable=message, width=_msg_width).pack(side=BOTTOM)

        arg_entries = {}
        for key in kwargs:
            Label(options, text=kwargs[key][0]).pack()
            var = StringVar()
            var.set(str(kwargs[key][1]))
            arg_entries[key] = var
            if key in _dist_param_names:
                OptionMenu(options, DistanceStringVar(var), *_function_names).pack()
            Entry(options, textvariable=var).pack()

        # capture the algorithm. not sure if this is necessary to build the closure?
        algorithm_runner = algorithm

        def callback():
            self.messageString = message
            self.timerString = timer
            self.timerCount = 0
            args = {}
            for key in arg_entries:
                args[key] = arg_entries[key].get()
            self.run_algorithm(algorithm_runner, **args)

        button = Button(options, text="Run %s" % name, command=callback)
        button.pack()
        self.button_list.append(button)
        self.algorithms.add(options, text=name)

    def listen_for_result(self):
        self.timerCount += 1
        self.timerString.set("Time Elapsed: %.1f seconds" % (self.timerCount * _delay_time / 1000))

        try:
            # empty the queue
            while True:
                result = self.thread_queue.get_nowait()
                if isinstance(result, str):
                    self.messageString.set(result)
                elif isinstance(result, Image.Image):
                    self.output_image = result
                    self.messageString.set("Done!")
                    self.set_button_state(NORMAL)
                    self.reload_image_label(self.output_image, self.out_label)
                    # wait for the thread to finish
                    self.algorithm_thread.join()
                    # clear the thread
                    self.algorithm_thread = None
        except queue.Empty:
            # continue waiting for an image result
            if self.algorithm_thread is not None and self.algorithm_thread.is_alive():
                self.master.after(_delay_time, self.listen_for_result)
            # if the thread stopped unexpectedly, stop checking for it
            elif self.algorithm_thread is not None:
                self.messageString.set("Error: Thread stopped unexpectedly.")
                self.set_button_state(NORMAL)
                self.algorithm_thread = None

    def client_exit(self):
        if self.algorithm_thread is not None:
            # do we need to do anything with unfinished threads?
            pass
        exit()


# supply parameters for everything except image and thread_queue for the following algorithm running methods
# each value is a (display_string, initial_value) tuple
# make sure the parameter for the distance function is in _dist_param_names (e.g.: 'distance')
_k_mean_args = \
    {'k_value': ('K Value:', 4),
     'max_shift': ('End if shift less than:', 3),
     'distance': ('Distance function:', 'euclidean')}
_mean_shift_args = \
    {'max_shift': ('End if shift less than: ', 3),
     'max_centroids': ('Initial sampling (min 16, max 256): ', 256),
     'distance': ('Distance function:', 'euclidean')}


def run_k_means(image, thread_queue, k_value=4, max_shift=3, distance=dist_func.euclidean):
    # args have to be converted from input strings
    k_value = int(k_value)
    max_shift = int(max_shift)
    if isinstance(distance, str):
        distance = dist_func.decode_string(distance)

    # initialize algorithm
    k_means = KMeans(k_value, list(image.getdata()), distance)
    shift = max_shift + 1  # arbitrary value greater than max, so that the loop is entered
    i = 0

    # run loop with display output
    while shift > max_shift:
        i += 1
        k_means.shift_centroids()
        shift = max(k_means.shift_distance)
        thread_queue.put("Iteration: %d, Shift: %.2f" % (i, shift))

    # create and send final result
    res_image = img_utils.map_index_to_paletted_image(
        image.size,
        k_means.get_clustering(),
        k_means.get_centroids())

    thread_queue.put(res_image)
    thread_queue.put("SSE: %d" % k_means.get_sum_square_error())


def run_mean_shift(image, thread_queue, distance=dist_func.euclidean, max_shift=3, max_centroids=256):
    # convert args from input strings
    max_shift = int(max_shift)
    if isinstance(distance, str):
        distance = dist_func.decode_string(distance)

    pixels = list(image.getdata())
    color_palette = mean_shift.mine(pixels, thread_queue, distance_alg=distance, min_movement=max_shift, max_centroids=max_centroids)
    new_image = img_utils.map_to_paletted_image(image, color_palette, distance=distance, output_queue=thread_queue)

    thread_queue.put(new_image)
    thread_queue.put("Colours used: %d\nSSE: %d" %
                     (len(color_palette),
                      closest_color.get_sum_squared_error(pixels, list(new_image.getdata()), color_palette, distance)))


if __name__ == '__main__':
    root = Tk()
    root.geometry(str(_img_size[0] * 3) + "x" + str(_img_size[1]))
    app = Window(root)
    app.add_algorithm("K-Means", run_k_means, **_k_mean_args)
    app.add_algorithm("Mean-Shift", run_mean_shift, **_mean_shift_args)
    root.mainloop()
