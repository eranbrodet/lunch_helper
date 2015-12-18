from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from os.path import join
from sys import platform
from Tkinter import BOTH, W, N, E, S, END, DISABLED, VERTICAL, LEFT, NONE  # Positions, States, and Directions
from Tkinter import Tk, Text, Label, PhotoImage, Listbox, StringVar  # Elements
from ttk import Frame, Scrollbar, Style, Notebook, Separator, Button
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


#######################################################################################
####################################### Tabs  #########################################
#######################################################################################
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

        self.people_list = Listbox(self, selectmode='multiple', exportselection=0, activestyle='none')
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
            self.people_list.insert(END, person)
        self._flip_daffy(None)  # Load the first image
        self._calc_list(None)

    def _calc_list(self, event):
        """
            Calculates the list of restaurants for the selected people and updates the text box
            :param event: ignored
        """
        try:
            indices = self.people_list.curselection()
            selected_people = set()
            for index in indices:
                selected_people.add(self.people_list.get(index))
            results = CrossReferencer.find_restaurants(selected_people)
        except Exception as e:
            print "exception", e
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
        self.choose_user_label = Label(self, text="Choose user", padx=5)
        self.users_list = Listbox(self, selectmode='single', exportselection=0, activestyle='none', font=('Tahoma', 8))
        self.users_list_scrollbar = Scrollbar(self, command=self.users_list.yview)
        self.users_list.bind('<Double-Button-1>', self._user_list_doubleclick)
        self.users_list['yscrollcommand'] = self.users_list_scrollbar.set
        self.add_person_button = Button(self, text="Add new user", width=16, command=self._add_person_to_db)
        self.edit_person_button = Button(self, text="Edit user", width=16, command=self._edit_person_in_db)
        self.delete_person_button = Button(self, text="Delete user", width=16, command=self._delete_user_from_db)

        self.separator = Separator(self, orient=VERTICAL)

        self.choose_restaurant_label = Label(self, text="Choose restaurant", padx=5)
        self.restaurants_list = Listbox(self, selectmode='single', exportselection=0, activestyle='none', font=('Tahoma', 8))
        self.restaurants_list.bind('<Double-Button-1>', self._restaurant_list_doubleclick)
        self.restaurants_list_scrollbar = Scrollbar(self, command=self.restaurants_list.yview)
        self.restaurants_list['yscrollcommand'] = self.restaurants_list_scrollbar.set
        self.add_restaurant_button = Button(self, text="Add new restaurant", width=18, command=self._add_restaurant_to_db)
        self.edit_restaurant_button = Button(self, text="Edit restaurant", width=18, command=self._edit_restaurant_in_db)
        self.delete_restaurant_button = Button(self, text="Delete restaurant", width=18, command=self._delete_restaurant_from_db)

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(4, weight=1)
        self.columnconfigure(6, weight=1)
        self.columnconfigure(8, weight=2)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=4)
        self.rowconfigure(4, weight=4)

    def layout_ui(self):
        self.choose_user_label.grid(row=1, column=0, sticky=N + E)
        self.users_list.grid(row=1, column=1, rowspan=3, sticky=N + E + S + W)
        self.users_list_scrollbar.grid(row=1, column=2, rowspan=3, sticky=N + E + S)
        self.add_person_button.grid(row=1, column=3, sticky=N + E)
        self.edit_person_button.grid(row=2, column=3, sticky=N + E)
        self.delete_person_button.grid(row=3, column=3, sticky=N + E)

        self.separator.grid(row=0, column=4, rowspan=5, sticky=N + S)

        self.choose_restaurant_label.grid(row=1, column=5, sticky=N + W)
        self.restaurants_list.grid(row=1, column=6, rowspan=3, sticky=N + W + S + E)
        self.restaurants_list_scrollbar.grid(row=1, column=7, rowspan=3, sticky=N + W + S)
        self.add_restaurant_button.grid(row=1, column=8, sticky=N + W)
        self.edit_restaurant_button.grid(row=2, column=8, sticky=N + W)
        self.delete_restaurant_button.grid(row=3, column=8, sticky=N + W)

    def refresh(self):
        self.users_list.delete(0, END)
        for user in self._db.get_all_people():
            self.users_list.insert(END, user)
        self.restaurants_list.delete(0, END)
        for item in self._db.get_all_restaurants():
            self.restaurants_list.insert(END, item)

    def _add_person_to_db(self):
        dialogue = AddUserDialogue(self, self._db)
        self.wait_window(dialogue)

    def _user_list_doubleclick(self, event):
        self._edit_person_in_db()

    def _edit_person_in_db(self):
        index = self.users_list.curselection()
        if not index:
            tkMessageBox.showinfo("User must be selected", "Please select a user from the list")
            return
        user = self.users_list.get(index).strip()
        dialogue = EditUserDialogue(self, self._db, user)
        self.wait_window(dialogue)

    def _add_restaurant_to_db(self):
        dialogue = AddRestaurantDialogue(self, self._db)
        self.wait_window(dialogue)

    def _restaurant_list_doubleclick(self, event):
        self._edit_restaurant_in_db()

    def _edit_restaurant_in_db(self):
        index = self.restaurants_list.curselection()
        if not index:
            tkMessageBox.showinfo("Restaurant must be selected", "Please select a restaurant from the list")
            return
        restaurant = self.restaurants_list.get(index).strip()
        dialogue = EditRestaurantDialogue(self, self._db, restaurant)
        self.wait_window(dialogue)

    def _delete_restaurant_from_db(self):
        index = self.restaurants_list.curselection()
        if not index:
            tkMessageBox.showinfo("Restaurant must be selected", "Please select a restaurant from the list")
            return
        restaurant = self.restaurants_list.get(index).strip()
        dialogue = DeleteRestaurantDialogue(self, self._db, restaurant)
        self.wait_window(dialogue)

    def _delete_user_from_db(self):
        index = self.users_list.curselection()
        if not index:
            tkMessageBox.showinfo("User must be selected", "Please select a User from the list")
            return
        user = self.users_list.get(index).strip()
        dialogue = DeleteUserDialogue(self, self._db, user)
        self.wait_window(dialogue)


#######################################################################################
################################## User Dialogues #####################################
#######################################################################################
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
        self.restaurants_list = Listbox(self, selectmode='multiple', activestyle='none', exportselection=0, font=('Tahoma', 8))
        self.restaurants_list_scrollbar = Scrollbar(self, command=self.restaurants_list.yview)
        self.restaurants_list['yscrollcommand'] = self.restaurants_list_scrollbar.set
        self.choose_restaurants_label = Label(self, text="Restaurants:")

        self.user_label = Label(self, text="Person Name:")
        self.user_text = Text(self, height=1, width=18, wrap=NONE)
        self.user_text.bind('<Return>', self._user_text_enter)

        self.ok_button = Button(self, text="OK", command=self._ok_button)
        self.cancel_button = Button(self, text="Cancel", command=self._cancel_button)
        #TODO go over these
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        # Layout
        self.user_label.grid(row=0, column=0, sticky=E + N)
        self.user_text.grid(row=0, column=1, sticky=W + N)
        self.choose_restaurants_label.grid(row=2, column=0, sticky=E + N)
        self.restaurants_list.grid(row=2, column=1, sticky=W + E + S + N)
        self.restaurants_list_scrollbar.grid(row=2, column=2, sticky=W + S + N)
        self.ok_button.grid(row=3, column=1, sticky=E + S + N)
        self.cancel_button.grid(row=3, column=2, sticky=W + S + N)

        # Fill up fields
        available_restaurants = set(self._db.get_all_restaurants())
        self.restaurants_list.delete(0, END)
        for item in available_restaurants:
            self.restaurants_list.insert(END, item)

        self.fill_initial_values()

        self.wait_visibility()
        self.grab_set()  # Makes window modal

    def _user_text_enter(self, event):
        self._ok_button()

    def _ok_button(self):
        if self.button_ok_action():
            self.destroy()

    def _cancel_button(self):
        self.destroy()


class AddUserDialogue(UserDialogue):
    def button_ok_action(self):
        person_name = self.user_text.get("1.0", END).strip()

        if not person_name:
            tkMessageBox.showerror("Adding a person failed", "Person name cannot be empty!")
            return False

        indices = self.restaurants_list.curselection()
        selected_restaurants = set()
        for index in indices:
            selected_restaurants.add(self.restaurants_list.get(index))
        try:
            #TODO these should be all or nothing, meaning we need a transaction here
            self._db.add_person(person_name)
            self._db.add_person_to_restaurants(person_name, selected_restaurants)
            self.parent.refresh()
        except Exception as e:
            tkMessageBox.showerror("Adding a person failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)
            return False
        return True

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
            return False

        selected_restaurants = []
        indices = self.restaurants_list.curselection()
        for index in indices:
            selected_restaurants.append(self.restaurants_list.get(index))
        try:
            if person_name != self.user_name:
                self._db.change_person_name(self.user_name, person_name)
            self._db.delete_all_restaurants_from_user(person_name)
            self._db.add_person_to_restaurants(person_name, selected_restaurants)
            self.parent.refresh()
        except Exception as e:
            tkMessageBox.showerror("Editing person failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)
            return False
        return True

    def fill_initial_values(self):
        self.user_text.insert(END, self.user_name)
        restaurants = self._db.get_restaurants_for_person(self.user_name)
        for i, restaurant in enumerate(self.restaurants_list.get(0, END)):
            if restaurant in restaurants:
                self.restaurants_list.selection_set(i)


class DeleteUserDialogue(Toplevel, object): #TODO Eran dedup with DeleteRestaurantDialogue?
    def __init__(self, parent, db, name):
        Toplevel.__init__(self, parent)
        x = parent.winfo_rootx()
        y = parent.winfo_rooty()
        self.geometry("+%d+%d" % (x, y))
        self.parent = parent
        self._db = db
        self.transient(parent)  # Makes this window a child of the parent
        self.name = name

        self.label = Label(self, justify=LEFT, font=('Helvetica', 15), text="Are you sure you want to delete %s?\n"
                                      "This will remove it and all the restaurants he/she are connected to.\n"
                                      "This operation is not reversible!" % (name,))
        self.ok_button = Button(self, text="Delete", command=self._ok_button)
        self.cancel_button = Button(self, text="Cancel", command=self._cancel_button)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        #layout
        self.label.grid(row=0, column=0, sticky=E + N)
        self.cancel_button.grid(row=1, column=0, sticky=E + S)
        self.ok_button.grid(row=1, column=1, sticky=E + S)

        self.wait_visibility()
        self.grab_set()  # Makes window modal

    def _cancel_button(self):
        self.destroy()

    def _ok_button(self):
        try:
            self._db.delete_person(self.name)
            self.parent.refresh()
            self.destroy()
        except Exception as e:
            tkMessageBox.showerror("Deleting a restaurant failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)


#######################################################################################
################################## Restaurants Dialogues ##############################
#######################################################################################
#TODO: Add dialogue for editing restaurant name
class RestaurantDialogue(Toplevel, object): #TODO Eran dedup with user
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

        self.restaurant_label = Label(self, text="Restaurant Name:")
        self.restaurant_text = Text(self, height=1, width=18, wrap=NONE)
        self.restaurant_text.bind('<Return>', self._restaurant_text_enter)
        self.comment_label = Label(self, text="Comment:")
        self.comment_text = Text(self, height=5, width=18, wrap=NONE)
        self.ok_button = Button(self, text="OK", command=self._ok_button)
        self.cancel_button = Button(self, text="Cancel", command=self._cancel_button)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        #layout
        self.restaurant_label.grid(row=0, column=0, sticky=E + N)
        self.restaurant_text.grid(row=0, column=1, sticky=W + N + E + S)
        self.comment_label.grid(row=1, column=0, sticky=E + S)
        self.comment_text.grid(row=1, column=1, sticky=W + N + E + S)
        self.cancel_button.grid(row=2, column=1, sticky=E + S)
        self.ok_button.grid(row=2, column=2, sticky=E + S)

        self.fill_initial_values()

        self.wait_visibility()
        self.grab_set()  # Makes window modal

    def _cancel_button(self):
        self.destroy()

    def _restaurant_text_enter(self, event):
        self._ok_button()

    def _ok_button(self):
        if self.button_ok_action():
            self.destroy()

class AddRestaurantDialogue(RestaurantDialogue, object):
    def __init__(self, parent, db):
        super(self.__class__, self).__init__(parent, db)

    def button_ok_action(self):
        restaurant_name = self.restaurant_text.get("1.0", END).strip()
        restaurant_comment = self.comment_text.get("1.0", END).strip()

        if not restaurant_name:
            tkMessageBox.showerror("Editing a restaurant failed", "Restaurant name cannot be empty!")
            return False
        try:
            self._db.add_restaurant(restaurant_name, restaurant_comment)
            self.parent.refresh()
        except Exception as e:
            tkMessageBox.showerror("Adding a restaurant failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)
            return False
        return True

    def fill_initial_values(self):
        pass

class EditRestaurantDialogue(RestaurantDialogue, object):
    def __init__(self, parent, db, restaurant_name):
        self.restaurant_name = restaurant_name
        self.restaurant_comment = db.get_restaurant_comment(restaurant_name)
        super(self.__class__, self).__init__(parent, db)

    def button_ok_action(self):
        new_restaurant_name = self.restaurant_text.get("1.0", END).strip()
        new_restaurant_comment = self.comment_text.get("1.0", END).strip()
        if self.restaurant_name == new_restaurant_name and self.restaurant_comment == new_restaurant_comment:
            # no need to update anything
            return True

        if not new_restaurant_name:
            tkMessageBox.showerror("Editing a restaurant failed", "Restaurant name cannot be empty!")
            return False
        try:
            self._db.update_restaurant(self.restaurant_name, new_restaurant_name, new_restaurant_comment)
            self.parent.refresh()
        except Exception as e:
            tkMessageBox.showerror("Editing a restaurant failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)
            return False
        return True

    def fill_initial_values(self):
        self.restaurant_text.insert(END, self.restaurant_name)
        self.comment_text.insert(END, self.restaurant_comment)

class DeleteRestaurantDialogue(Toplevel, object): #TODO Eran dedup with AddRestaurantDialogue
    def __init__(self, parent, db, name):
        Toplevel.__init__(self, parent)
        x = parent.winfo_rootx()
        y = parent.winfo_rooty()
        self.geometry("+%d+%d" % (x, y))
        self.parent = parent
        self._db = db
        self.transient(parent)  # Makes this window a child of the parent
        self.name = name

        self.label = Label(self, justify=LEFT, font=('Helvetica', 15), text="Are you sure you want to delete %s?\n"
                                      "This will remove it from all users that are connected to it.\n"
                                      "This operation is not reversible!" % (name,))
        self.ok_button = Button(self, text="Delete", command=self._ok_button)
        self.cancel_button = Button(self, text="Cancel", command=self._cancel_button)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        #layout
        self.label.grid(row=0, column=0, sticky=E + N)
        self.cancel_button.grid(row=1, column=0, sticky=E + S)
        self.ok_button.grid(row=1, column=1, sticky=E + S)

        self.wait_visibility()
        self.grab_set()  # Makes window modal

    def _cancel_button(self):
        self.destroy()

    def _ok_button(self):
        try:
            self._db.delete_restaurant(self.name)
            self.parent.refresh()
            self.destroy()
        except Exception as e:
            tkMessageBox.showerror("Deleting a restaurant failed", "Operation failed!")
            print 'GOT AN EXCEPTION!' + str(e)


#######################################################################################
######################################### Main ########################################
#######################################################################################
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
