import tkinter as tk
import tkinter.filedialog as fd
import PIL.Image
import PIL.ImageTk
from PIL import Image # Image.NEARESTを使うためにインポート

def dispPhoto(path):
    # 画像を開く
    img = PIL.Image.open(path).convert("L")
    
    # 🌟 重要な修正点: resizeの引数はタプル (幅, 高さ) にする
    newImage = img.resize((32, 32)).resize((300, 300), resample=Image.NEAREST)
    
    imageData = PIL.ImageTk.PhotoImage(newImage)
    imageLabel.configure(image = imageData)
    imageLabel.image = imageData # 参照保持

# ... (openFile 関数とメインループは前回と同じ) ...

def openFile():
    fpath = fd.askopenfilename()
    if fpath:
        dispPhoto(fpath)

root = tk.Tk()
root.geometry("400x350")
root.title("モザイク写真ビューア")

btn = tk.Button(text="ファイルを開く", command = openFile)
imageLabel = tk.Label()

btn.pack(pady=10)
imageLabel.pack()

tk.mainloop()