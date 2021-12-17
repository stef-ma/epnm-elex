from mylibs.MyGUI import *


def main():

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    appwindow=AppWindow()
    appwindow.mainloop()


if __name__ == '__main__':
    main()

