from tkinter import *
from tkinter.ttk import Notebook
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import threading
import queue
from colorclusters import image_utils as img_utils, mean_shift, closest_color, distance as dist_func
from colorclusters.k_means import KMeans
from ast import literal_eval

# the maximum size of the image labels
_img_size = (400, 400)
_msg_width = 300

# the amount of time between checking the thread_queue
_delay_time = 1000

# the default options for a distance function
_function_names = ['euclidean', 'manhattan', 'chebyshev', 'norm(3)']
# the parameter names that get interpreted as a distance
_dist_param_names = ('distance', 'dist')

# Deprecated. No longer have the dropdown linked to an editable field
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
        self.thread_run_flag = None

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

        ctrl = Menu(menu)
        ctrl.add_command(label="Suggest Stop", command=self.halt_thread)
        menu.add_cascade(label="Control", menu=ctrl)

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
        self.thread_run_flag = BooleanVar()
        self.thread_run_flag.set(True)
        if 'image' not in kwargs:
            kwargs['image'] = self.input_image
        if 'run_var' not in kwargs:
            kwargs['run_var'] = self.thread_run_flag
        if 'thread_queue' not in kwargs:
            kwargs['thread_queue'] = self.thread_queue

        # start the algorithm on a separate thread
        self.algorithm_thread = threading.Thread(
            target=algorithm_runner,
            kwargs=kwargs,
            daemon=True)
        self.algorithm_thread.start()
        self.after(_delay_time, self.listen_for_result)

    def halt_thread(self):
        if self.thread_run_flag is not None:
            self.thread_run_flag.set(False)

    def add_algorithm(self, name, algorithm, **kwargs):
        options = Frame(self.algorithms)
        options.pack(fill=BOTH, expand=1)
        message = StringVar()
        timer = StringVar()
        Label(options, textvariable=timer).pack(side=BOTTOM)
        Message(options, textvariable=message, width=_msg_width).pack(side=BOTTOM)

        arg_entries = {}
        for key in kwargs:
            if isinstance(kwargs[key][1],bool):
                var = BooleanVar()
                var.set(kwargs[key][1])
                arg_entries[key] = var
                Checkbutton(options, text=kwargs[key][0], variable=var).pack(pady=5)
            else:
                Label(options, text=kwargs[key][0]).pack()
                var = StringVar()
                var.set(str(kwargs[key][1]))
                arg_entries[key] = var
                if key in _dist_param_names:
                    OptionMenu(options, var, *_function_names).pack(pady=5)
                    Label(options, text="Scale factor:").pack()
                    var = StringVar()
                    var.set("(1,1,1,1)")
                    arg_entries[key+"_scale_"]=var

                    Entry(options, textvariable=var).pack(pady=5)
                else:
                    Entry(options, textvariable=var).pack(pady=5)

        # capture the algorithm. not sure if this is necessary to build the closure?
        algorithm_runner = algorithm

        def callback():
            self.messageString = message
            self.timerString = timer
            self.timerCount = 0
            args = {}
            for key in arg_entries:
                if key in _dist_param_names:
                    scale = literal_eval(arg_entries[key+"_scale_"].get())
                    func = dist_func.decode_string(arg_entries[key].get())
                    if scale.count(1) != len(scale):
                        print('using scale')
                        func = dist_func.scaled_distance(func,scale)
                    args[key] = func
                elif key.endswith("_scale_"):
                    pass #ignore the internally used scale field
                else:
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
                    self.thread_run_flag = None
        except queue.Empty:
            # continue waiting for an image result
            if self.algorithm_thread is not None and self.algorithm_thread.is_alive():
                self.master.after(_delay_time, self.listen_for_result)
            # if the thread stopped unexpectedly, stop checking for it
            elif self.algorithm_thread is not None:
                self.messageString.set("Error: Thread stopped unexpectedly.")
                self.set_button_state(NORMAL)
                self.algorithm_thread = None
                self.thread_run_flag = None

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
     'distance': ('Distance function:', 'euclidean'),
     'plus_plus': ('Use K-Means++', True)}
_mean_shift_args = \
    {'max_shift': ('End if shift less than:', 3),
     'max_centroids': ('Initial sampling (min 16, max 256):', 256),
     'distance': ('Distance function:', 'euclidean')}


def run_k_means(image, run_var, thread_queue, k_value=4, max_shift=3, plus_plus=False, distance=dist_func.euclidean):
    # args have to be converted from input strings
    k_value = int(k_value)
    max_shift = float(max_shift)
    plus_plus = bool(plus_plus)
    if isinstance(distance, str):
        distance = dist_func.decode_string(distance)

    # initialize algorithm
    thread_queue.put("Choosing initial centroids")
    k_means = KMeans(k_value, list(image.getdata()), distance, use_kmeans_plus_plus=plus_plus)
    shift = max_shift + 1  # arbitrary value greater than max, so that the loop is entered
    i = 0

    # run loop with display output
    thread_queue.put("Shifting centroids")
    while shift > max_shift and run_var.get():
        i += 1
        k_means.shift_centroids()
        shift = max(k_means.shift_distance)
        thread_queue.put("Iteration: %d, Shift: %.2f" % (i, shift))
    thread_queue.put("Iteration: %d, Shift: %.2f\nBuilding final image" % (i, shift))
    # create and send final result
    res_image = img_utils.map_index_to_paletted_image(
        image.size,
        k_means.get_clustering(),
        k_means.get_centroids())

    thread_queue.put(res_image)
    thread_queue.put("Iterations: %d\nSSE: %d" % (i,k_means.get_sum_square_error()))

def run_mean_shift(image, run_var, thread_queue, distance=dist_func.euclidean, max_shift=3, max_centroids=256):
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
    root.geometry(str(_img_size[0] * 2 + 200) + "x" + str(_img_size[1]))
    app = Window(root)
    app.add_algorithm("K-Means", run_k_means, **_k_mean_args)
    app.add_algorithm("Mean-Shift", run_mean_shift, **_mean_shift_args)
    root.mainloop()
