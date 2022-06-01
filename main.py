from mylibs.MyGUI import *

# This is the main program from which the whole GUI is instanced.
#
def main():
# bla
    os.chdir(os.path.dirname(os.path.abspath(__file__))) #Sets pythons working directory to the directory of this file
    appwindow=AppWindow() #create...
    appwindow.mainloop() #... and start the app window


if __name__ == '__main__':
    main()

