from converter.gui import FileConverterApp
from tkinterdnd2 import TkinterDnD

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileConverterApp(root)
    root.mainloop()