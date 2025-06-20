import sqlite3
import pandas as pd

db_path = "C:\cygwin64\home\charl\25CERN\CassetteReception\csvDB.db"
def createDB(db_path):
    initialize_db = [  #Add any other statements needed here
            """CREATE TABLE IF NOT EXISTS module_ids (
            module_name TEXT NOT NULL UNIQUE PRIMARY KEY
            );"""
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

    except sqlite3.OperationalError as e:
        print("failed to initialize db: ", e)


def addModstoDB(db_name, mod_list):
    #db_name should be in quotes
    #mod_list should be only the serial codes of modules to add to db. 
    #make sure that csvs have been created and stored in CSVFiles for each module before running

    #insert_row = """ INSERT INTO module_csvs (module_name, i_vs_v, adc_stdd, adc_mean)
    #             VALUES (?,?,?,?) """
    
    #ADDS module to sqlite db

    for mod in mod_list:
        try:
            with sqlite3.connect(db_name) as conn:
                print("mod: ", mod)
                cursor = conn.cursor()
                mod_data = pd.read_csv(f"{mod}.csv")
                print("found file")
                mod_data.to_sql(f"{mod}", conn, if_exists = "replace")
                print("table created")
                cursor.execute("INSERT INTO module_ids VALUES(?)", (mod,))
                print("inserted")
                conn.commit()
            print("connected to db, file(s) uploaded, mod_id updated")

        except sqlite3.OperationalError as e:
            print("failed to add to module_ids: ", e)