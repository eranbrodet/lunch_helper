# lunch_helper

Usage:
======
1. Run ui.pyw
2. Populate the DB with restaurants and with users and let users link themselves to their favourite places
3. Use the “Find restaurants” and “Find people” tabs to cross reference and narrow down choices
4. Order lunch
5. Eat and live happily

Requirements:
=============
 - Python 2.7
 - Tkinter (usually comes built-in, otherwise install from pip)

Motivation:
===========
The story that happens over and over  
  Person A: “What are you ordering today?”  
  Person B: “What do you want?”  
  Person A: “Don't know, what do you want?”  
  Person C: “What are you guys ordering?”  
  Person A: “Open a list of options, let's see what's available”  
  # Person B opens a list with hundreds of places  
  Person B: “What about X?”  
  Person D: “Doesn't have anything I'll order.”  
  Person A: “We haven't ordered from Y for some time.”  
  Person C: “Nah”  
  # Later that day  
  Person A to Person E: So where are you ordering today? I'm really getting hungry.”  
  Person E: “I ordered from Z with Person B.”  
  Person A: “Oh, I would have joined.”  
  Person E: “Didn't know you liked that place.”  
So the need arises to have a clean and simple DB that narrows down the lists and let you cross references what any group of   people can agree on or who else might enjoy a certain place you order from.  
