from os.path import join
from sys import platform
from Tkinter import BOTH, W, N, E, S, END, DISABLED  # Positions, States, and Directions
from Tkinter import Tk, Text, Label, PhotoImage, Listbox, StringVar  # Elements
from ttk import Frame, Scrollbar, Style, Notebook, Combobox, Button
from lunch import FoodFinder


class FoodFinderUi(Frame, object): #TODO Rename
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self._loading_sequence()
        self.init_ui()
        self.calc_list(None)
        self.parent.mainloop()

    def init_ui(self):
        self.style = Style()
        style = 'xpnative' if 'xpnative' in self.style.theme_names() else 'default'
        self.style.theme_use(style)
        self.pack(fill=BOTH, expand=1)

        # Define tabbed view
        #TODO extract frames to classes?
        self.notebook = Notebook(self.parent)
        self.restaurants_tab = Frame(self.notebook)
        self.people_tab = Frame(self.notebook)
        self.db_tab = Frame(self.notebook)
        self.notebook.add(self.restaurants_tab, text='Find restaurants')
        self.notebook.add(self.people_tab, text='Find people')
        self.notebook.add(self.db_tab, text='Manage DB')
        self.notebook.pack(expand=1, fill=BOTH)   #TODO tabs don't resize on Y

        # Define UI elements of first tab
        self.restaurants_text_box = Text(self.restaurants_tab)
        self.restaurants_text_box.config(state=DISABLED)
        restaurants_scrollbar = Scrollbar(self.restaurants_tab, command=self.restaurants_text_box.yview)
        self.restaurants_text_box['yscrollcommand'] = restaurants_scrollbar.set

        self.names_list = Listbox(self.restaurants_tab, selectmode='multiple', exportselection=0)
        for person in self.all_people:
            self.names_list.insert(END, person.title())
        self.names_list.bind("<<ListboxSelect>>", self.calc_list)
        names_scrollbar = Scrollbar(self.restaurants_tab, command=self.names_list.yview)
        self.names_list['yscrollcommand'] = names_scrollbar.set

        self.daffy = Label(self.restaurants_tab, bg="white")
        self.daffy.daffy = PhotoImage(file=join("images", 'daffy.gif'))
        self.daffy.daffy_i = PhotoImage(file=join("images", 'daffy_i.gif'))
        self.daffy.bind("<Button-1>", self.flip_daffy)
        self.flip_daffy(None)  # Load the first image

        # Define resizing of elements when window is resized
        self.restaurants_tab.columnconfigure(0, weight=1)
        self.restaurants_tab.columnconfigure(2, weight=5)
        self.restaurants_tab.rowconfigure(0, weight=1)

        # Arrange all the elements on the tab
        self.names_list.grid(row=0, column=0, sticky=E + W + S + N)
        names_scrollbar.grid(row=0, column=1, sticky=E + W + S + N)
        self.restaurants_text_box.grid(row=0, column=2, sticky=E + W + S + N)
        self.daffy.grid(row=0, column=2, sticky=E + S)
        restaurants_scrollbar.grid(row=0, column=3, sticky=E + W + S + N)

        # Define people tab elements
        Label(self.people_tab, text='Coming soon').pack(fill=BOTH, expand=1)

        # Define db tab elements
        #TODO bad font jumbled text (http://stackoverflow.com/q/34220597/2134702)
        self.restaurants_list = Listbox(self.db_tab, selectmode='multiple', exportselection=0)

        self.restaurants_list_scrollbar = Scrollbar(self.db_tab, command=self.restaurants_list.yview)
        self.restaurants_list['yscrollcommand'] = self.restaurants_list_scrollbar.set
        chose_rests_label = Label(self.db_tab, text="Choose restaurants\n(showing only ones\nyou haven't selected)")

        combo_label = Label(self.db_tab, text="Choose user")
        self.box_value = StringVar()
        self.combo = Combobox(self.db_tab, textvariable=self.box_value)
        self.combo['values'] = self.all_people
        self.combo.bind("<<ComboboxSelected>>", self._user_selected)
        add_person_button = Button(self.db_tab, text="Add new user")
        add_person_button.bind("<Button-1>", self._add_person_to_db)

        new_rest_label = Label(self.db_tab, text="New restaurant")
        self.new_restaurant = Text(self.db_tab, height=1, width=18)
        add_restaurant_button = Button(self.db_tab, text="Add new restaurant")
        add_restaurant_button.bind("<Button-1>", self._add_restaurant_to_db)

        add_user_restaurants_button = Button(self.db_tab, text="Add restaurants to user")
        add_user_restaurants_button.bind("<Button-1>", self._add_user_to_restaurants_in_db)

        self.db_tab.columnconfigure(0, weight=0)
        self.db_tab.columnconfigure(1, weight=0)
        self.db_tab.columnconfigure(2, weight=0)
        self.db_tab.columnconfigure(3, weight=0)
        self.db_tab.columnconfigure(4, weight=1)
        self.db_tab.rowconfigure(0, weight=0)
        self.db_tab.rowconfigure(1, weight=0)
        self.db_tab.rowconfigure(2, weight=1)

        combo_label.grid(row=0, column=0, sticky=E + N)
        self.combo.grid(row=0, column=1, sticky=W + N)
        add_person_button.grid(row=0, column=3, sticky=W + N)
        new_rest_label.grid(row=1, column=0, sticky=E + N)
        self.new_restaurant.grid(row=1, column=1, sticky=W + N)
        add_restaurant_button.grid(row=1, column=3, sticky=W + N)
        chose_rests_label.grid(row=2, column=0, sticky=E + N)
        self.restaurants_list.grid(row=2, column=1, sticky=W + E + S + N)
        self.restaurants_list_scrollbar.grid(row=2, column=2, sticky=W + S + N)
        add_user_restaurants_button.grid(row=2, column=3, sticky=W + N)

    def _user_selected(self, event):
        user = self.box_value.get()
        available_restaurants = set(self.all_restaurants) - set(self.food_finder.find_food(set([user])))
        self.restaurants_list.delete(0, END)
        for item in available_restaurants:
            self.restaurants_list.insert(END, item)

    def _add_person_to_db(self, event):
        #TODO verify user is new (if not popup a message)
        user = self.box_value.get().strip()
        if not user:
            return
        self.food_finder.add_user(user)
        #TODO show message if failed
        #TODO Eran only add if succes or simply reload list
        self.combo['values'] += (user,)

    def _add_restaurant_to_db(self, event):
        #TODO verify user is new (if not popup a message)
        res = self.new_restaurant.get("1.0", END).strip()
        if not res:
            return
        self.food_finder.add_restaurant(res)
        #TODO show message if failed
        #TODO Eran only add if succes or simply reload list
        self.restaurants_list.insert(END, res)

    def _add_user_to_restaurants_in_db(self, event):
        #TODO Eran verify user exists maybe don't use the combo box for text in[ut
        user = self.box_value.get().strip()
        selected_restaurants = [self.all_restaurants[int(x)].lower() for x in self.restaurants_list.curselection()]
        self.food_finder.add_user_to_restaurants(user, selected_restaurants)
        #TODO Eran update lists

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
        self.food_finder = FoodFinder()
        self.all_people = self.food_finder.get_all_people()
        self.all_restaurants = self.food_finder.get_all_restaurants()
        # Remove label before continuing
        loading_label.pack_forget()

    def calc_list(self, event):
        """
            Calculates the list of restaurants for the selected people and updates the text box
            :param event: ignored
        """
        try:
            selected_people = [self.all_people[int(x)].lower() for x in self.names_list.curselection()]
            results = self.food_finder.find_food(set(selected_people))
        except:
            results = []

        self.restaurants_text_box.configure(state='normal')
        self.restaurants_text_box.delete('1.0', END)
        self.restaurants_text_box.insert(END, "\n".join(results))
        self.restaurants_text_box.configure(state='disabled')

    def flip_daffy(self, event):
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
    FoodFinderUi(root)


if __name__ == '__main__':
    main()
