from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from os.path import join
from sys import platform
from Tkinter import BOTH, W, N, E, S, END, DISABLED  # Positions, States, and Directions
from Tkinter import Tk, Text, Label, PhotoImage, Listbox, StringVar  # Elements
from ttk import Frame, Scrollbar, Style, Notebook, Combobox, Button
import tkMessageBox
from Tkinter import Toplevel
from cross_referencer import CrossReferencer
from db import DB


class LunchHelperUI(Frame, object):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self._loading_sequence()
        self.init_ui()
        self.parent.mainloop()

    def init_ui(self):
        # Init style
        self.style = Style()
        style = 'xpnative' if 'xpnative' in self.style.theme_names() else 'default'
        self.style.theme_use(style)
        # Layout this frame
        self.grid(row=0, column=0, sticky=N+S+W+E)

        # Define tabbed view
        notebook = Notebook(self.parent)
        self._tabs = OrderedDict((('Find restaurants', RestaurantsTab(notebook, self._db)),
                           ('Find people', PeopleTab(notebook, self._db)),
                           ('Manage DB', DbTab(notebook, self._db))))
        for tab_name, tab in self._tabs.iteritems():
            notebook.add(tab, text=tab_name)
            tab.init_ui()
            tab.layout_ui()
        notebook.bind("<<NotebookTabChanged>>", self._refresh_tab_on_change)
        notebook.pack(expand=1, fill=BOTH)
        # Initial state
        self._current_tab = 0
        self._tabs[self._tabs.keys()[0]].refresh()

    def _refresh_tab_on_change(self, event):
        tab = event.widget.tab(event.widget.select(), "text")
        self._tabs[tab].refresh()

    def _loading_sequence(self):
        """
            Shows a loading message while preparing the FoodFinder (which could take a while reading the excel file)
        """
        loading_label = Label(self.parent, text="Loading...   :)")
        loading_label.pack(fill=BOTH, expand=1)
        # Update UI to show the packed label
        self.parent.update_idletasks()
        self.parent.update()
        # Do work
        self._db = DB()
        # Remove label before continuing
        loading_label.pack_forget()


class Tab(Frame, object):
    __metaclass__ = ABCMeta

    def __init__(self, parent, db):
        Frame.__init__(self, parent)
        self._db = db

    @abstractmethod
    def refresh(self): pass
    @abstractmethod
    def init_ui(self): pass
    @abstractmethod
    def layout_ui(self): pass


class RestaurantsTab(Tab):
    def init_ui(self):
        self.restaurants_text_box = Text(self, background='white', state=DISABLED)
        self.restaurants_scrollbar = Scrollbar(self, command=self.restaurants_text_box.yview)
        self.restaurants_text_box['yscrollcommand'] = self.restaurants_scrollbar.set

        self.people_list = Listbox(self, selectmode='multiple', exportselection=0)
        self.people_list.bind("<<ListboxSelect>>", self._calc_list)
        self.people_scrollbar = Scrollbar(self, command=self.people_list.yview)
        self.people_list['yscrollcommand'] = self.people_scrollbar.set

        self.daffy = Label(self, bg="white")
        self.daffy.daffy = PhotoImage(file=join("images", 'daffy.gif'))
        self.daffy.daffy_i = PhotoImage(file=join("images", 'daffy_i.gif'))
        self.daffy.bind("<Button-1>", self._flip_daffy)

        # Define resizing of elements when window is resized
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=5)
        self.rowconfigure(0, weight=1)

    def layout_ui(self):
        # Arrange all the elements on the tab
        self.people_list.grid(row=0, column=0, sticky=E + W + S + N)
        self.people_scrollbar.grid(row=0, column=1, sticky=E + W + S + N)
        self.restaurants_text_box.grid(row=0, column=2, sticky=E + W + S + N)
        self.daffy.grid(row=0, column=2, sticky=E + S)
        self.restaurants_scrollbar.grid(row=0, column=3, sticky=E + W + S + N)

    def refresh(self):
        self.people_list.delete(0, END)
        for person in self._db.get_all_people():
            self.people_list.insert(END, person.title())
        self._flip_daffy(None)  # Load the first image
        self._calc_list(None)

    def _calc_list(self, event):
        """
            Calculates the list of restaurants for the selected people and updates the text box
            :param event: ignored
        """
        try:
            selected_people = [self._db.get_all_people()[int(x)] for x in self.people_list.curselection()]
            results = CrossReferencer.find_restaurants(set(selected_people))
        except:
            results = []

        self.restaurants_text_box.configure(state='normal')
        self.restaurants_text_box.delete('1.0', END)
        self.restaurants_text_box.insert(END, "\n".join(results))
        self.restaurants_text_box.configure(state='disabled')

    def _flip_daffy(self, event):
        """
            :param event: Ignored except when its bool value is false
                        For recognising the initial load.
        """
        if not event or self.daffy.image == self.daffy.daffy_i:
            self.daffy.configure(image=self.daffy.daffy)
            self.daffy.image = self.daffy.daffy
        else:
            self.daffy.configure(image=self.daffy.daffy_i)
            self.daffy.image = self.daffy.daffy_i


class PeopleTab(Tab):
    def init_ui(self):
        self.coming_soon = Label(self, text='Coming soon')

    def layout_ui(self):
        self.coming_soon.pack(fill=BOTH, expand=1)

    def refresh(self):
        pass


class DbTab(Tab):
    def init_ui(self):
        # Setting font since the default is weird and jumbles-up hebrew with apostrophe (stackoverflow.com/q/34220597/2134702)
        self.restaurants_list = Listbox(self, selectmode='multiple', exportselection=0, font=('Tahoma', 8))
        self.restaurants_list_scrollbar = Scrollbar(self, command=self.restaurants_list.yview)
        self.restaurants_list['yscrollcommand'] = self.restaurants_list_scrollbar.set
        self.choose_restaurants_label = Label(self, text="Choose restaurants\n(showing only ones\nyou haven't added)")

        self.choose_user_label = Label(self, text="Choose user")
        self.choose_user_value = StringVar()
        self.choose_user_combobox = Combobox(self, textvariable=self.choose_user_value, state='readonly')
        self.choose_user_combobox.bind("<<ComboboxSelected>>", self._user_selected)
        self.add_person_button = Button(self, text="Add new user", command=self._add_person_to_db)
        self.edit_person_button = Button(self, text="Edit user", command=self._edit_person_in_db)

        self.new_restaurant_label = Label(self, text="New restaurant")
        self.new_restaurant = Text(self, height=1, width=18)
        self.add_restaurant_button = Button(self, text="Add new restaurant")
        self.add_restaurant_button.bind("<Button-1>", self._add_restaurant_to_db)

        self.add_user_restaurants_button = Button(self, text="Add restaurants to user")
        self.add_user_restaurants_button.bind("<Button-1>", self._add_user_to_restaurants_in_db)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

    def layout_ui(self):
        self.choose_user_label.grid(row=0, column=0, sticky=E + N)
        self.choose_user_combobox.grid(row=0, column=1, sticky=W + N)
        self.add_person_button.grid(row=0, column=3, sticky=W + N)
        self.edit_person_button.grid(row=1, column=3, sticky=W + N)
        self.new_restaurant_label.grid(row=1, column=0, sticky=E + N)
        self.new_restaurant.grid(row=1, column=1, sticky=W + N)
        self.choose_restaurants_label.grid(row=2, column=0, sticky=E + N)
        self.restaurants_list.grid(row=2, column=1, sticky=W + E + S + N)
        self.restaurants_list_scrollbar.grid(row=2, column=2, sticky=W + S + N)
        self.add_restaurant_button.grid(row=2, column=3, sticky=W + N)
        self.add_user_restaurants_button.grid(row=2, column=3, sticky=W + N)

    def refresh(self):
        self.choose_user_combobox['values'] = self._db.get_all_people()
        self.choose_user_combobox.set("")
        self._user_selected(None)

    def _user_selected(self, event):
        user = self.choose_user_value.get()
        if not user:
            return
        available_restaurants = set(self._db.get_all_restaurants()) - set(CrossReferencer.find_restaurants({user}))
        self.restaurants_list.delete(0, END)
        for item in available_restaurants:
            self.restaurants_list.insert(END, item)

    def _add_person_to_db(self):
        dialogue = AddUserDialogue(self, self._db)
        self.wait_window(dialogue)

    def _edit_person_in_db(self):
        user = self.choose_user_value.get().strip()
        if not user:
            tkMessageBox.showinfo("User must be selected", "Please select a user from the combo box")
            return

        dialogue = EditUserDialogue(self, self._db, user)
        self.wait_window(dialogue)

    def _add_restaurant_to_db(self, event):
        restaurant = self.new_restaurant.get("1.0", END).strip()
        if not restaurant:
            return
        try:
            self._db.add_restaurant(restaurant)
            self.refresh()
        except Exception:  #TODO catch specific exceptions and handle appropriately
            tkMessageBox.showerror("Adding a restaurant failed", "Either this restaurant already exist or connecting to the database failed")
            return

    def _add_user_to_restaurants_in_db(self, event):
        user = self.choose_user_value.get().strip()
        selected_restaurants = [self._db.get_all_restaurants()[int(x)].lower() for x in self.restaurants_list.curselection()]
        try:
            self._db.add_person_to_restaurants(user, selected_restaurants)
            self.refresh()
        except Exception: #TODO catch specific exceptions and handle appropriately
            tkMessageBox.showerror("Adding user to restaurants failed", "Either we failed to connect to the database, or the user or one of the restaurants doesn't exist or the mapping already exists")
            return


class UserDialogue(Toplevel, object):
    __metaclass__ = ABCMeta
    @abstractmethod
    def button_ok_action(self): pass
    @abstractmethod
    def fill_initial_values(self): pass

    def __init__(self, parent, db):
        Toplevel.__init__(self, parent)
        x = parent.winfo_rootx()
        y = parent.winfo_rooty()
        self.geometry("+%d+%d" % (x, y))
        self.parent = parent
        self._db = db
        self.transient(parent)  # Makes this window a child of the parent

        # Setting font since the default is weird and jumbles-up hebrew with apostrophe (stackoverflow.com/q/34220597/2134702)
        self.restaurants_list = Listbox(self, selectmode='multiple', exportselection=0, font=('Tahoma', 8))
        self.restaurants_list_scrollbar = Scrollbar(self, command=self.restaurants_list.yview)
        self.restaurants_list['yscrollcommand'] = self.restaurants_list_scrollbar.set
        self.choose_restaurants_label = Label(self, text="Restaurants:")

        self.user_label = Label(self, text="Person Name:")
        self.user_text = Text(self, height=1, width=18)

        self.ok_button = Button(self, text="OK", command=self._ok_button)
        self.cancel_button = Button(self, text="Cancel", command=self._cancel_button)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        #layout
        self.user_label.grid(row=0, column=0, sticky=E + N)
        self.user_text.grid(row=0, column=1, sticky=W + N)
        self.choose_restaurants_label.grid(row=2, column=0, sticky=E + N)
        self.restaurants_list.grid(row=2, column=1, sticky=W + E + S + N)
        self.restaurants_list_scrollbar.grid(row=2, column=2, sticky=W + S + N)
        self.ok_button.grid(row=3, column=1, sticky=E + S + N)
        self.cancel_button.grid(row=3, column=2, sticky=W + S + N)

        #fill up fields
        available_restaurants = set(self._db.get_all_restaurants())
        self.restaurants_list.delete(0, END)
        for item in available_restaurants:
            self.restaurants_list.insert(END, item)

        self.fill_initial_values()

        self.wait_visibility()
        self.grab_set()  # Makes window modal

    def _ok_button(self):
        self.button_ok_action()
        self.destroy()

    def _cancel_button(self):
        self.destroy()


class AddUserDialogue(UserDialogue):
    def button_ok_action(self):
        person_name = self.user_text.get("1.0", END).strip()

        if not person_name:
            tkMessageBox.showerror("Adding a person failed", "Person name cannot be empty!")
            return

        selected_restaurants = [self._db.get_all_restaurants()[int(x)] for x in self.restaurants_list.curselection()]
        try:
            self._db.add_person(person_name)
            self._db.add_person_to_restaurants(person_name, selected_restaurants)
        except Exception as e:
            tkMessageBox.showerror("Adding a person failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)

    def fill_initial_values(self):
        pass


class EditUserDialogue(UserDialogue):
    def __init__(self, parent, db, user_name):
        self.user_name = user_name
        super(self.__class__, self).__init__(parent, db)

    def button_ok_action(self):
        person_name = self.user_text.get("1.0", END).strip()

        if not person_name:
            tkMessageBox.showerror("Editing person failed", "Person name cannot be empty!")
            return

        selected_restaurants = [self._db.get_all_restaurants()[int(x)] for x in self.restaurants_list.curselection()]
        try:
            if person_name != self.user_name:
                self._db.change_person_name(self.user_name, person_name)
            self._db.delete_all_restaurants_from_user(person_name)
            self._db.add_person_to_restaurants(person_name, selected_restaurants)
        except Exception as e:
            tkMessageBox.showerror("Editing person failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)

    def fill_initial_values(self):
        self.user_text.insert(END, self.user_name)
        all_restaurants = self._db.get_all_restaurants()
        restaurants = self._db.get_restaurants_for_person(self.user_name)
        for i, restaurant in enumerate(all_restaurants):
            if restaurant in restaurants:
                self.restaurants_list.selection_set(i)


def main():
    root = Tk()
    root.geometry("700x390+200+200")
    root.minsize(700, 390)

    # Set the root icon, for some reason Linux acts a bit special here. See http://stackoverflow.com/a/11180300/2134702
    if platform == "linux" or platform == "linux2":
        daffy_image = PhotoImage(file=join("images", 'daffy.png'))
        root.tk.call('wm', 'iconphoto', root._w, daffy_image)
    else:
        root.iconbitmap(join("images", 'daffy.ico'))

    root.title("F00D")
    LunchHelperUI(root)


if __name__ == '__main__':
    main()
