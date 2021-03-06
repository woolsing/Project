from tkinter.ttk import Combobox

import mysql.connector
import pandas as pd
from mysql.connector import errorcode
import tkinter as tk


#Using MAMP to connect to MYSQL server
#Connection to the server
cnx = mysql.connector.connect(user='root',
                              password='root',
                              host='127.0.0.1',
                              )
databaseName = "Speedrunning"
cursor = cnx.cursor()

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)

viewExists = False
def topPlayer():
    #Create a view for top player for a specific game
    global viewExists
    if viewExists == False:

        cursor.execute("CREATE VIEW top AS "
                     "SELECT m.Player "
                     "FROM Mario m "
                     "WHERE Rank <= 1")
        viewExists = True


    cursor.execute("SELECT * FROM top")
    data = cursor.fetchall()
    for row in data:
        lbl_resulttopten.insert('end', "Top 1: ")
        lbl_resulttopten.insert('end', row)
        lbl_resulttopten.insert('end', "\n")

def printTopTen():
    #Creating a view
    cursor.execute("SELECT m.Rank, m.Player, z.Rank, z.Player, ma.Rank, ma.Player, mk.Rank, mk.Player "\
                   "FROM Mario m "\
                   "JOIN Zelda z "\
                   "ON m.Rank = z.Rank "\
                   "JOIN Mario70 ma "\
                   "ON m.Rank = ma.Rank "\
                   "JOIN Mariokart mk "\
                   "ON m.Rank = mk.Rank "\
                   "WHERE m.Rank <= 11 " \
                   "ORDER BY m.Rank ")

    #Using the view made just before this
    data = cursor.fetchall()
    lbl_resulttopten.insert('end', "Top 10: ")
    lbl_resulttopten.insert('end', "\n")
    lbl_resulttopten.insert('end', "Mario 120 stars - Zelda - Mario 70 stars - Mario kart")
    for row in data:
        lbl_resulttopten.insert('end', "\n")
        lbl_resulttopten.insert('end', row)
        lbl_resulttopten.insert('end', "\n")


def averageRunner():
    #Clear the window when button pressed again
    lbl_resultsum.delete('1.0', tk.END)
    cursor.execute("SELECT COUNT(RANK) "
                   "FROM {} ".format(combo.get())
                   )
    data = cursor.fetchall()
    for row in data:
        lbl_resulttimeandrank.insert('end', "\n")
        lbl_resultsum.insert('end', "Number of runners in this game: ")
        lbl_resultsum.insert('end', row)
        lbl_resulttimeandrank.insert('end', "\n")



def timeandrank():
    cursor.execute("SELECT Rank, Player, Time FROM {} WHERE Player = %s".format(combo.get()), (ent_player.get(),))
    data = cursor.fetchall()
    for row in data:
        lbl_resulttimeandrank.insert('end', "Game: {} ".format(combo.get()))
        lbl_resulttimeandrank.insert('end', "\n")
        lbl_resulttimeandrank.insert('end', row)
        lbl_resulttimeandrank.insert('end', "\n")


def printplayersingame():
    lbl_resultplayers.delete('1.0', tk.END)
    query = "SELECT Rank, Player " \
                "FROM {}  " \
                "ORDER BY Rank ".format(combo.get())
    cursor.execute(query)
    data = cursor.fetchall()
    for row in data:
        lbl_resultplayers.insert('end', row)
        lbl_resultplayers.insert('end', "\n")


def groupmario():
    cursor.execute("SELECT m.Player, m.Rank, ma.Player, ma.Rank "
                    "FROM Mario m "
                    "JOIN Mario70 ma "
                    "ON m.Player = ma.Player "
                    "WHERE m.Player = %s "
                    "GROUP BY m.Player ", (ent_group.get(),))
    data = cursor.fetchall()
    for row in data:
        lbl_resultgroup.insert('end', "Super Mario 64 120 stars vs Super Mario 64 70 stars \n")
        lbl_resultgroup.insert('end', row)
        lbl_resultgroup.insert('end', "\n")


def create_database(cursor, databaseName):
    try:
        #Creating the database here
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(databaseName))

    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)


def create_table(cursor):
    tablename = {}
    tablename['Mario'] = ("CREATE TABLE `Mario` ("
                            " `Rank` bigint(100), "
                            " `Player` char(100), "
                            " `Time` char(100), "
                            " `Verified` char(100), "
                            " `Platform` char(100), "
                            " `Date` char(100),"
                            "  PRIMARY KEY (`Player`)"
                            ") ENGINE=InnoDB" )

    tablename['Mario70'] =("CREATE TABLE `Mario70` ("
                           " `Rank` bigint(100), "
                           " `Player` char(100), "
                           " `Time` char(100), "
                           " `Verified` char(100), "
                           " `Platform` char(100), "
                           " `Date` char(100),"
                           "  PRIMARY KEY (`Player`)"
                           ") ENGINE=InnoDB")


    tablename['Zelda'] = ("CREATE TABLE `Zelda`("
                          " `Rank` bigint(100), "
                          " `Player` char(100), "
                          " `Time` char(100), "
                          " `Mode` char(100), "
                          " `Dlc` char(100), "
                          " `amiibo` char(100),"
                          " `Platform` char(100),"
                          " `Date` char(100),"
                          "  PRIMARY KEY (`Player`)"
                          ") ENGINE=InnoDB" )

    tablename['Mariokart'] = ("CREATE TABLE `Mariokart` ("
                            " `Rank` bigint(100), "
                            " `Player` char(100), "
                            " `Time` char(100), "
                            " `Version` char(100), "
                            " `Date` char(100),"
                            "  PRIMARY KEY (`Player`)"
                            ") ENGINE=InnoDB" )


    for table_name in tablename:
        table_description = tablename[table_name]
        try:
            print("Creating table: ")
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("Already exists.")
            else:
                print(err.msg)
    else:
        print("Ok.")

def insertintotables(cursor,datamario,datazelda,datamariokart,datamario70):

    for index, row in datamario.iterrows():
        try:
            #Remove the last characters in rank to sort easier
            x = ''.join(c for c in row[0] if c.isdigit())
            row[0] = x
            sql = "INSERT INTO Mario VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, tuple(row))
            cnx.commit()
        except mysql.connector.Error as err:
            print(err.msg)
        else:
            cnx.commit()

    for index, row in datamario70.iterrows():
        try:
            #Remove the last characters in rank to sort easier
            x = ''.join(c for c in row[0] if c.isdigit())
            row[0] = x
            sql = "INSERT INTO Mario70 VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, tuple(row))
            cnx.commit()
        except mysql.connector.Error as err:
            print(err.msg)
        else:
            cnx.commit()

    for index, row in datazelda.iterrows():
        try:
            #Remove the last characters in rank to sort easier
            x = ''.join(c for c in row[0] if c.isdigit())
            row[0] = x
            sql = "INSERT INTO Zelda VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, tuple(row))
            cnx.commit()
        except mysql.connector.Error as err:
            print(err.msg)
        else:
            cnx.commit()


    for index, row in datamariokart.iterrows():
        try:
            #Remove the last characters in rank to sort easier
            x = ''.join(c for c in row[0] if c.isdigit())
            row[0] = x
            sql = "INSERT INTO Mariokart VALUES (%s,%s,%s,%s,%s)"
            cursor.execute(sql, tuple(row))
            cnx.commit()
        except mysql.connector.Error as err:
            print(err.msg)
        else:
            cnx.commit()
#Replace the path with where you placed the different files.
datamario = pd.read_csv(r'C:\Users\chokl\Desktop\supermariospeedrunsheet.csv')
datamario = datamario.where((pd.notnull(datamario)), None)

datazelda = pd.read_csv(r'C:\Users\chokl\Desktop\zelda.csv')
datazelda = datazelda.where((pd.notnull(datazelda)), None)

datamariokart = pd.read_csv(r'C:\Users\chokl\Desktop\mariokart8.csv')
datamariokart = datamariokart.where((pd.notnull(datamariokart)), None)

datamario70 = pd.read_csv(r'C:\Users\chokl\Desktop\supermario70.csv')
datamario70 = datamario70.where((pd.notnull(datamario70)), None)



try:
    cursor.execute("USE {}".format(databaseName))

except mysql.connector.Error as err:
    print("Database {} does not exists.".format(databaseName))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Create Database here")
        create_database(cursor, databaseName)
        cnx.database = databaseName
        cursor.execute("USE {}".format(databaseName))
        print("Database {} created successfully.".format(databaseName))
        create_table(cursor)
        insertintotables(cursor,datamario,datazelda,datamariokart,datamario70)
    else:
        print(err)

def comparetime():
    lbl_result.delete('1.0', tk.END)
    cursor.execute("SELECT m.Rank, m.Player, m.Time, z.Rank, z.Player, z.Time, mk.Rank, mk.Player, mk.Time, ma.Rank, ma.Player, ma.Time "
                    "FROM Mario m "
                    "JOIN Zelda z "
                    "ON m.Rank = z.Rank "
                    "JOIN mariokart mk "
                    "ON m.rank = mk.Rank "
                    "JOIN Mario70 ma "
                    "ON m.Rank = ma.Rank "
                    "WHERE m.Rank = %s", (ent_playerrank.get(),))
    data = cursor.fetchall()
    for row in data:
        lbl_result.insert('end', "Comparing different games and players time at specific rank ")
        lbl_result.insert('end', "\n")
        lbl_result.insert('end', "Mario --- Zelda --- Mario Kart --- Mario 70")
        lbl_result.insert('end', "\n")
        lbl_result.insert('end', row)
        lbl_result.insert('end', "\n")


mainwin = tk.Tk()

entry = tk.Entry()
frm_entry = tk.Frame(master=mainwin)
ent_playerrank = tk.Entry(master=frm_entry, width=10)
lbl_playerrank = tk.Label(master=frm_entry, text="Rank:")

lbl_playerrank.grid(row=1,column=0)
ent_playerrank.grid(row=1,column=1)


btn_convert = tk.Button(
    master=mainwin,
    text="\N{RIGHTWARDS BLACK ARROW}",
    command = comparetime
)
lbl_result = tk.Text(master=mainwin)


frm_entry.grid(row=1, column=0)
btn_convert.grid(row=1, column=1)
lbl_result.grid(row=1, column=2)


#Making the combobox to keep track of which game it is
combo = Combobox(mainwin)
combo['values'] = ("Mario", "Mario70", "Zelda", "Mariokart")
combo.grid(row=0, column=1)
lbl_combo = tk.Label(master=mainwin, text="Choose game: ")
lbl_combo.grid(row=0, column=0)

button = tk.Button(
    master=mainwin,
    text='Print all players',
    command = printplayersingame
)
button.grid(row=0, column=3)
lbl_resultplayers = tk.Text(master=mainwin)
lbl_resultplayers.grid(row=1,column=3)



#Making the button to print out a specific player and that players time and rank
frm_entryplayer = tk.Frame(master=mainwin)
ent_player = tk.Entry(master=frm_entry, width=10)
lbl_player = tk.Label(master=frm_entry, text="Player:")

buttonTime = tk.Button(
    master=mainwin,
    text="\N{RIGHTWARDS BLACK ARROW}",
    command = timeandrank
)
lbl_resulttimeandrank = tk.Text(master=mainwin)

ent_player.grid(row=2,column=1)
lbl_player.grid(row=2,column=0)
frm_entryplayer.grid(row=2, column=1,stick="n")
buttonTime.grid(row=2, column=1)
lbl_resulttimeandrank.grid(row=2, column=2)



#Making a button to group together
frm_entrygroup = tk.Frame(master=mainwin)
ent_group = tk.Entry(master=frm_entry, width=10)
lbl_group = tk.Label(master=frm_entry, text="Compare player: ")

buttonGroup = tk.Button(
    master=mainwin,
    text="\N{RIGHTWARDS BLACK ARROW}",
    command = groupmario
)
lbl_resultgroup = tk.Text(master=mainwin)

ent_group.grid(row=3,column=1)
lbl_group.grid(row=3,column=0)
frm_entrygroup.grid(row=3, column=1,stick="n")
buttonGroup.grid(row=3, column=1)
lbl_resultgroup.grid(row=2, column=3)


#Making a button to calculate the average amount of speedrunners in these 4 games
frm_entrysum = tk.Frame(master=mainwin)
lbl_sum = tk.Label(master=frm_entry, text="Calculate average number of runners: ")

buttonAverage = tk.Button(
    master=mainwin,
    text="Calculate",
    command = averageRunner
)
lbl_resultsum = tk.Text(master=mainwin)
buttonAverage.grid(row=0, column=2)
lbl_resultsum.grid(row=3, column=2)

#Making a button to print top 10 in all games
frm_entrytopten = tk.Frame(master=mainwin)
lbl_sumtopten = tk.Label(master=frm_entry, text="Calculate average number of runners: ")

buttonTopTen = tk.Button(
    master=mainwin,
    text="Print top 10",
    command = printTopTen
)
lbl_resulttopten = tk.Text(master=mainwin)
buttonTopTen.grid(row=0, column=4)
lbl_resulttopten.grid(row=3, column=3)


#Creating a button to create a view for a specific game

buttonTop = tk.Button(
    master=mainwin,
    text="Top Player in Mario: ",
    command = topPlayer
)
lbl_resulttop = tk.Text(master=mainwin)
buttonTop.grid(row=2, column=0)
#Smoother resizing of the window
for i in range(3):
    mainwin.columnconfigure(i, weight=1, minsize=75)
    mainwin.rowconfigure(i, weight=1, minsize=50)

    for j in range(0, 3):
        frame = tk.Frame(
            master=mainwin,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=i, column=j, padx=5, pady=5)


mainwin.mainloop()
