import tkinter as tk
from PIL import Image, ImageTk
from colorclusters.image_utils import add_transparency_grid

root = tk.Tk()

img = Image.open("../tests/images/pre_map_test.png")
img = add_transparency_grid(img)
img_tk = ImageTk.PhotoImage(img)

tk.Label(root, image=img_tk).pack()

root.mainloop()
