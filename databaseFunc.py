import sqlite3
import pandas as pd

db_path = r"C:\cygwin64\home\charl\25CERN\CassetteReception\csvDB.db"

def createDB(db_path):
    #def createDB(db_path):
    initialize_db = [  #Add any other statements needed here
        """
        CREATE TABLE IF NOT EXISTS tested_module_ids (
        module_id TEXT NOT NULL UNIQUE PRIMARY KEY );
        """,
        """
        CREATE TABLE IF NOT EXISTS manuf_module_ids (
        module_id TEXT NOT NULL UNIQUE PRIMARY KEY );
        """
        ]

        #i_vs_v TEXT NOT NULL,
        #adc_stdd TEXT NOT NULL,
        #adc_mean TEXT NOT NULL

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for statement in initialize_db:
                cursor.execute(statement)
            conn.commit()
            print("database initialized")
        conn.close()
    except sqlite3.OperationalError as e:
        print("failed to initialize db: ", e)

def setTestedMods(mod_list): #given a modules list and csv has been created, add mod to db
    #db_name should be in quotes
    #mod_list should be only the serial codes of modules to add to db. 
    #make sure that csvs have been created and stored in CSVFiles for each module before running

    #insert_row = """ INSERT INTO module_csvs (module_name, i_vs_v, adc_stdd, adc_mean)
    #             VALUES (?,?,?,?) """
    #ADDS module to sqlite db

    try:
        with sqlite3.connect("test.db") as conn:
            for mod in mod_list:
                print("mod: ", mod)
                cursor = conn.cursor()
                mod_data = pd.read_csv(f"CSVFiles/{mod}.csv")
                print("found file")
                mod_data.to_sql(f"tested_{mod}", conn, if_exists = "replace", index = False)
                print("table created")
                try:
                    cursor.execute("INSERT INTO tested_module_ids VALUES(?)", (mod,))
                    print("inserted")
                except sqlite3.IntegrityError as e:
                    print(f"you are trying to replace data in tested_{mod}", e)
                conn.commit()
        print("connected to db, file(s) uploaded, mod_id updated")
        conn.close()
    except sqlite3.OperationalError as e:
        print("failed to add to module_ids: ", e)

def getTestedMods(): #Returns list of tested mods in db
    try:
        with sqlite3.connect("test.db") as conn:
            print("Opened database successfully")
            conn.row_factory = lambda cursor, row: row[0]
            cur = conn.cursor()
            mod_ids = cur.execute("Select module_id from tested_module_ids").fetchall()
        conn.close()
    except sqlite3.OperationalError as e:
        print("failed to access to module_ids: ", e)
    return mod_ids

def getDataFromTestedMod(mod): #Returns data from one mod as lists of meas_i,meas_v,adc_stdd,adc_mean 
    meas_i = []
    meas_v = []
    adc_stdd = []
    adc_mean = []
    try:
        with sqlite3.connect("csvDB.db") as conn:
            print("Opened database successfully")
            table = conn.execute(f"SELECT meas_i, meas_v, adc_stdd, adc_mean from tested_{mod}")
            for data_row in table:
                meas_i.append(data_row[0])
                meas_v.append(data_row[1])
                adc_stdd.append(data_row[2])
                adc_mean.append(data_row[3])
        conn.close()
        print("full table printed")
    except sqlite3.OperationalError as e:
        print("failed to access to module_ids: ", e)
    return meas_i, meas_v, adc_stdd, adc_mean

def setManufMods(mod_list): #given a modules list and csv has been created, add mod to db
    #db_name should be in quotes
    #mod_list should be only the serial codes of modules to add to db. 
    #make sure that csvs have been created and stored in CSVFiles for each module before running

    #insert_row = """ INSERT INTO module_csvs (module_name, i_vs_v, adc_stdd, adc_mean)
    #             VALUES (?,?,?,?) """
    #ADDS module to sqlite db

    try:
        with sqlite3.connect("csvDB.db") as conn:
            for mod in mod_list:
                print("mod: ", mod)
                cursor = conn.cursor()
                mod_data = pd.read_csv(f"CSVFiles/{mod}.csv")
                print("found file")
                mod_data.to_sql(f"manuf_{mod}", conn, if_exists = "replace", index = False)
                print("table created")
                try:
                    cursor.execute("INSERT INTO manuf_module_ids VALUES(?)", (mod,))
                    print("inserted")
                except sqlite3.IntegrityError as e:
                    print(f"you are trying to replace data in manuf_{mod}", e)
                conn.commit()
        print("connected to db, file(s) uploaded, mod_id updated")
        conn.close()
    except sqlite3.OperationalError as e:
        print("failed to add to module_ids: ", e)
    return 0

def getManufMods(): #Returns list of tested mods in db
    try:
        with sqlite3.connect("csvDB.db") as conn:
            print("Opened database successfully")
            conn.row_factory = lambda cursor, row: row[0]
            cur = conn.cursor()
            mod_ids = cur.execute("Select module_id from manuf_module_ids").fetchall()
        conn.close()
    except sqlite3.OperationalError as e:
        print("failed to access to module_ids: ", e)
    return mod_ids

def getDataFromManufMod(mod): #Returns data from one mod as lists of meas_i,meas_v,adc_stdd,adc_mean 
    meas_i = []
    meas_v = []
    adc_stdd = []
    adc_mean = []
    try:
        with sqlite3.connect("csvDB.db") as conn:
            print("Opened database successfully")
            table = conn.execute(f"SELECT meas_i, meas_v, adc_stdd, adc_mean from manuf_{mod}")
            for data_row in table:
                meas_i.append(data_row[0])
                meas_v.append(data_row[1])
                adc_stdd.append(data_row[2])
                adc_mean.append(data_row[3])
        conn.close()
        print("full table printed")
    except sqlite3.OperationalError as e:
        print("failed to access to module_ids: ", e)
    return meas_i, meas_v, adc_stdd, adc_mean

def removeModFromDB(mod): #given mod name, remove from db
    try:
        with sqlite3.connect("csvDB.db") as conn:
            cur = conn.cursor()
            cur.execute(f"DROP TABLE IF EXISTS tested_{mod}")
            print(f"tested_{mod} table deleted")
            cur.execute("DELETE FROM tested_module_ids WHERE module_name = ?", (mod,))
            print(f"tested_{mod} id deleted")
            conn.commit()
        conn.close()    
    except sqlite3.OperationalError as e:
        print("failed to access to module_ids: ", e)
