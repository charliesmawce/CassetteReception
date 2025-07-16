import uproot
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime

def createDB(db_path):
    initialize_db = [  #Add any other statements needed here
        """
        CREATE TABLE IF NOT EXISTS Maj_Types (
        LD_Modules TEXT,
        HD_Modules TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS LD_Modules (
        barcode TEXT NOT NULL UNIQUE PRIMARY KEY,
        loc_at_fermi TEXT NOT NULL,
        qc_passed BOOLEAN,
        grade TEXT,
        alt_loc TEXT NOT NULL, 
        alt_adc_tests TEXT NOT NULL,
        alt_pedestal_meas TEXT NOT NULL,
        alt_yaml_file TEXT,
        fermi_adc_tests TEXT,
        fermi_yaml_file TEXT,
        fermi_pedestal_meas TEXT);
        """,
        """
        CREATE TABLE IF NOT EXISTS HD_Modules (
        barcode TEXT NOT NULL UNIQUE PRIMARY KEY,
        loc_at_fermi TEXT NOT NULL,
        qc_passed BOOLEAN,
        grade TEXT,
        alt_loc TEXT NOT NULL, 
        alt_adc_tests TEXT NOT NULL,
        alt_pedestal_meas TEXT NOT NULL,
        alt_yaml_file TEXT NOT NULL,
        fermi_adc_tests TEXT,
        fermi_yaml_file TEXT,
        fermi_pedestal_meas TEXT);
        """
        ] #after dev, change root_file to pedestal_meas

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for statement in initialize_db:
                cursor.execute(statement)
            conn.commit()
            print("\n database created \n")
    except sqlite3.OperationalError as e:
        print("\n ERROR in createDB(): failed to create db: \n", e)
    return 0

class ModData: #data for MD and LD modules. other parts will nee their own class, table, and db calls
    def __init__(self,
                barcode,
                alt_loc,
                alt_adc_tests,
                alt_pedestal_meas,
                alt_yaml_file,
                qc_passed=None,
                grade = None,
                loc_at_fermi="Reception",
                fermi_adc_test = None,
                fermi_yaml_file = None,
                fermi_pedestal_meas = None):
        self.barcode = barcode
        self.alt_loc = alt_loc
        self.alt_adc_tests = alt_adc_tests
        self.alt_pedestal_meas = alt_pedestal_meas
        self.alt_yaml_file = alt_yaml_file
        self.qc_passed = qc_passed
        self.grade = grade
        self.loc_at_fermi = loc_at_fermi
        self.fermi_adc_test = fermi_adc_test
        self.fermi_yaml_file = fermi_yaml_file
        self.fermi_pedestal_meas = fermi_pedestal_meas

class DBFuncs(): #consider making it so that the class is just a db???
    def __init__(self,
                db_path):        
        self.db_path = db_path

    def addPlainPart(self, barcode, loc_at_fermi="Reception"):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {barcode[3:5]}_modules VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL,NULL)", 
            (barcode,loc_at_fermi))
        return 0 #this func would add an empty part with a barcode and loc_at_fermi. other info would have to be added interactivley
    
    def editCell(self, table, col, idx_col, row, value):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(f"UPDATE {table} SET {col} = ? WHERE {idx_col} = ?", (value, row))
                conn.commit()
        except sqlite3.OperationalError as e:
            print("\n ERROR in editCell(): failed to edit cell: \n", e)
    
    def addNewModToDB(self,barcode,alt_loc,alt_pedestal_meas,alt_yaml_file,loc_at_fermi="Reception", qc_passed=True): 
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                with open(alt_yaml_file, 'r') as file: 
                    yaml_contents = file.read()
                cur.execute(f"INSERT INTO {barcode[3:5]}_modules VALUES(?,?,NULL,NULL,?,?,?,?,NULL,NULL,NULL)", 
                            (barcode,loc_at_fermi,alt_loc,f"{barcode}_{alt_loc}",alt_pedestal_meas,yaml_contents))
                alt_data = pd.DataFrame(uproot.open(alt_pedestal_meas)['runsummary/summary'].arrays(library='pd'))
                alt_df = alt_data[['chip', 'channel', 'channeltype', 'adc_mean', 'adc_stdd']].copy()
                try:
                    alt_df.to_sql(f"{barcode}_{alt_loc}", conn, index=False)
                    print(f"\n {alt_loc} data table added to sql \n")
                except sqlite3.IntegrityError as e:
                    print("\n ERROR in addNewModToDB(), nested try: ", e)
                conn.commit()
                print("\n connected to db, file(s) uploaded, barcodes updated \n")
        except sqlite3.OperationalError as e:
            print("\n ERROR in addNewModToDB(): failed to add to barcodes: \n", e) 

    def addYAMLToMod(self, barcode, yaml_path, test_loc):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                with open(yaml_path, 'r') as file: 
                    yaml_contents = file.read()
                if test_loc != "fermi": 
                    tbl_loc = "alt"
                else:
                    tbl_loc = test_loc
                cur.execute(f"UPDATE HD_modules SET {tbl_loc}_yaml_file = ? WHERE barcode = ?", (yaml_contents, barcode))
                conn.commit()
        except sqlite3.OperationalError as e:
            print("\n ERROR in addYAMLToMod(): failed to add yaml \n", e) 
        
        #use barcode to find correct mod table, then loc to find correct cell, insert yaml contents

    def addADCTestToMod(self, barcode, test_loc, root_file_path):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                #initialize data/col names for sqlite querys
                if test_loc == "fermi": 
                    tbl_col = "fermi"
                    cur.execute(f"SELECT fermi_adc_tests FROM {barcode[3:5]}_modules WHERE barcode = ?", (barcode,))
                    tbl_names = cur.fetchall()
                    
                    #create updated tests dict
                    now = datetime.now()
                    datetime_str = now.isoformat() 
                    if tbl_names[0][0] is None:
                        tbl_name = f"{barcode}_{test_loc}_v1"
                        tbl_names =  json.dumps({"v1":{"tbl_name":tbl_name, "date_time": datetime_str}})
                    else:
                        tmp_dict = json.loads(tbl_names[0][0])
                        ver = int(list(tmp_dict.keys())[-1][-1])+1
                        test_ver = "test"+str(ver)
                        tbl_name = f"{barcode}_{test_loc}_{test_ver}"
                        tmp_dict[test_ver] = {"tbl_name":tbl_name, "date_time": datetime_str}
                        tbl_names = json.dumps(tmp_dict)
                else:
                    tbl_col = "alt"
                    tbl_name = f"{barcode}_{test_loc}"
                    tbl_names = tbl_name
                    
                #add the data to maj_table and make new data table
                try: 
                    cur.execute(f"UPDATE {barcode[3:5]}_modules SET {tbl_col}_adc_tests = ? WHERE barcode = ?", (tbl_names, barcode))
                    data = pd.DataFrame(uproot.open(root_file_path)['runsummary/summary'].arrays(library='pd'))
                    data_df = data[['chip', 'channel', 'channeltype', 'adc_mean', 'adc_stdd']].copy()
                    data_df.to_sql(tbl_name, conn, index=False)
                    print(f"\n {tbl_name} data table added to sql, with {tbl_name} added to {barcode[3:5]}_modules \n")
                except sqlite3.IntegrityError as e:
                    print("\n ERROR: ", e)
                conn.commit()
        except sqlite3.OperationalError as e:
            print("\n ERROR in addADCTestToMod(): \n", e) 

    def getFermiTestsFromMod(self, barcode):
        with sqlite3.connect(self.db_path) as conn:
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT fermi_adc_tests FROM {barcode[3:5]}_modules WHERE barcode = ?", (barcode,))
                tbl_names = cur.fetchone()
                if tbl_names is None:
                    print(f"No entry found for barcode {barcode}")
                    return []
                tbl_str = tbl_names[0]
                if tbl_str is None:
                    print("No test data available.")
                    return []
                tbl_dict = json.loads(tbl_names[0])
                conn.commit()
                return tbl_dict
            except Exception as e:
                print("Error in getFermiTestsFromMod():", e)

    def getMods(self, maj_type = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                barcode_list = []
                if maj_type == None:
                    cur.execute("PRAGMA table_info(Maj_Types)")
                    rows = cur.fetchall()
                    for row in rows:
                        maj_type = row[1]
                        cur.execute(f"SELECT barcode FROM {maj_type}")
                        for item in cur.fetchall():
                            barcode_list.append(item[0])
                else:
                    cur.execute(f"SELECT barcode FROM {maj_type[:2]}_modules")
                    for item in cur.fetchall():
                            barcode_list.append(item[0])
                conn.commit()
                return barcode_list
        except sqlite3.OperationalError as e:
            print("\n ERROR in getMods(): failed to get barcodes.\n", e)

    def getADCTest(self, test):   #test is string in format barcode_loc_test#
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f'SELECT * FROM "{test}"'
                data = pd.read_sql(query, conn)
                chip = data["chip"]
                channel = data["channel"]
                channeltype = data["channeltype"]
                adc_mean = data["adc_mean"]
                adc_stdd = data["adc_stdd"]
            conn.commit()
            return chip, channel, channeltype, adc_stdd, adc_mean
        except sqlite3.OperationalError as e:
            print(f"\n ERROR in GetACDTest(): failed to get {test}: \n", e)
            return None, None, None, None, None


    def rmFermiADCTest(self, test):   #test is string in format barcode_loc_test#      
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(f"SELECT fermi_adc_test FROM {test[3:5]}_modules WHERE barcode = {test.split("_")[0]}")
                tbl_names = cur.fetchall()
                tbl_dict = json.loads(tbl_names)
                
                tbl_dict.pop(test,None)
                cur.execute(f"DROP TABLE IF EXISTS {test}")
                print(f"\n {test} deleted\n")
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"\n ERROR in rmFermiADCTests(): failed to remove {test}: \n", e)

    def rmMod(self, barcode):            
        try:
            print(barcode)
            tests = self.getFermiTestsFromMod(barcode)
            print(f"Are you certain you want to remove {barcode} from {self.db_path}? (y/n)")
            inp = input()
            if inp == "y":
                with sqlite3.connect(self.db_path) as conn:
                    cur = conn.cursor()
                    try:
                        for test in tests.values():
                            tbl_name = test["tbl_name"]
                            cur.execute(f'DROP TABLE IF EXISTS "{tbl_name}"')
                            print(f"{tbl_name} deleted")
                        try: 
                            table_name = f"{barcode[3:5]}_modules"
                            cur.execute(f"SELECT alt_adc_tests FROM {table_name} WHERE barcode = ?", (barcode,))
                            test = cur.fetchone()
                            cur.execute(f'DROP TABLE IF EXISTS "{test[0]}"')
                            print(f"{test[0]} deleted")
                            try:
                                cur.execute(f"DELETE FROM {barcode[3:5]}_modules WHERE barcode = ?", (barcode,))
                                print(f"{barcode} deleted")
                            
                            except Exception as e:
                                print("`Error deleting from main tbl:", e)
                        except Exception as e:
                            print("Error deleting adc_tbl:", e)
                    except Exception as e:
                        print("Error deleting main tbl:", e)
                conn.commit()
            else:
                pass 
        except Exception as e:
            print("ERROR in rmMod():", e)

class ComparePlots: #This class will mostly stay the same, just diff initialization/calls
    def __init__(self, db_path, barcode, alt_test_loc, test_ver): #test ver is version of test from fermi     
        self.db = DBFuncs(db_path)                            #test ver format => "test#"
        self.barcode = barcode
        self.test_ver = test_ver
        self.fermi_loc = "fermi"
        self.alt_loc = alt_test_loc
        self.fermi_test = f"{barcode}_fermi_{test_ver}"
        self.alt_test = f"{barcode}_{alt_test_loc}"
        self.fermi_dict = {}
        self.alt_dict = {}
        self.ratio_dict = {}

    #@classmethod
    def comparePlots(self): 
        result = self.db.getADCTest(self.fermi_test)
        if result[0] is None:
            print(f"Test table {self.fermi_test} not found or error occurred.")
            return
        fermi_chip, fermi_channel, fermi_channeltype, fermi_adc_stdd, fermi_adc_mean = result
                
        self.fermi_dict = {
                    "chip": fermi_chip, 
                    "channel": fermi_channel, 
                    "channeltype": fermi_channeltype, 
                    "adc_mean": fermi_adc_mean,
                    "adc_stdd": fermi_adc_stdd}
        
        alt_chip, alt_channel, alt_channeltype, alt_adc_stdd, alt_adc_mean = self.db.getADCTest(self.alt_test)
        self.alt_dict = {
                    "chip": alt_chip, 
                    "channel": alt_channel, 
                    "channeltype": alt_channeltype, 
                    "adc_mean": alt_adc_mean,
                    "adc_stdd": alt_adc_stdd}
        
        ratio_adc_mean = []
        ratio_adc_stdd =[]
        for fval_mean, fval_stdd, aval_mean, aval_stdd in zip(self.fermi_dict["adc_mean"], self.fermi_dict["adc_stdd"], self.alt_dict["adc_mean"], self.alt_dict["adc_stdd"]):
            if aval_mean == 0:
                ratio_adc_mean.append(0)
            else:
                ratio_adc_mean.append(fval_mean/aval_mean)
            if aval_stdd == 0:
                ratio_adc_stdd.append(0)
            else:
                ratio_adc_stdd.append(fval_stdd/aval_stdd)
        self.ratio_dict = {
                    "chip": alt_chip, 
                    "channel": alt_channel, 
                    "channeltype": alt_channeltype, 
                    "adc_mean": ratio_adc_mean,
                    "adc_stdd": ratio_adc_stdd}
        return 0

    def plotComparison(self):
        cols = ['chip{}'.format(row) for row in range(3)]
        rows = ["Fermi Noise","Alt Noise", "Ratio of Noise"]
        fig_stdd, axes_stdd = plt.subplots(nrows=3, ncols=3, sharex=True, constrained_layout=True)#sharey=True)
        fig_mean, axes_mean = plt.subplots(nrows=3, ncols=3, sharex=True, constrained_layout=True)#sharey=True, )
        
        data_stdd = {
            "data_type": "stdd",
            'chip0': {'fermi': self.fermi_dict["adc_mean"][:78], 'alt': self.alt_dict["adc_mean"][:78], 'ratio': self.ratio_dict["adc_mean"][:78]},
            'chip1': {'fermi': self.fermi_dict["adc_mean"][78:156], 'alt': self.alt_dict["adc_mean"][78:156], 'ratio': self.ratio_dict["adc_mean"][78:156]},
            'chip2': {'fermi': self.fermi_dict["adc_mean"][156:], 'alt': self.alt_dict["adc_mean"][156:], 'ratio': self.ratio_dict["adc_mean"][156:]}
        }
        
        data_stdd = {"data_type": "stdd"}
        init = 0
        for idx, val in enumerate(self.fermi_dict["chip"]):
            key = "chip" + str(self.fermi_dict["chip"][idx])
            if idx == len(self.fermi_dict["chip"]) - 1:
                data_stdd[key] = {'fermi': self.fermi_dict["adc_mean"][init:], 'alt': self.alt_dict["adc_mean"][init:], 'ratio': self.ratio_dict["adc_mean"][init:]}
            elif self.fermi_dict["chip"][idx] != self.fermi_dict["chip"][idx+1]:
                idx = idx+1
                data_stdd[key] = {'fermi': self.fermi_dict["adc_mean"][init:idx], 'alt': self.alt_dict["adc_mean"][init:idx], 'ratio': self.ratio_dict["adc_mean"][init:idx]}
                init = idx
        
        data_mean = {"data_type": "mean"}
        init = 0
        for idx, val in enumerate(self.fermi_dict["chip"]):
            key = "chip" + str(self.fermi_dict["chip"][idx])
            if idx == len(self.fermi_dict["chip"]) - 1:
                data_mean[key] = {'fermi': self.fermi_dict["adc_mean"][init:], 'alt': self.alt_dict["adc_mean"][init:], 'ratio': self.ratio_dict["adc_mean"][init:]}
            elif self.fermi_dict["chip"][idx] != self.fermi_dict["chip"][idx+1]:
                idx = idx+1
                data_mean[key] = {'fermi': self.fermi_dict["adc_mean"][init:idx], 'alt': self.alt_dict["adc_mean"][init:idx], 'ratio': self.ratio_dict["adc_mean"][init:idx]}
                init = idx
        
        data_mean = {
            "data_type": "mean",
            'chip0': {'fermi': self.fermi_dict["adc_stdd"][:78], 'alt': self.alt_dict["adc_stdd"][:78], 'ratio': self.ratio_dict["adc_stdd"][:78]},
            'chip1': {'fermi': self.fermi_dict["adc_stdd"][78:156], 'alt': self.alt_dict["adc_stdd"][78:156], 'ratio': self.ratio_dict["adc_stdd"][78:156]},
            'chip2': {'fermi': self.fermi_dict["adc_stdd"][156:], 'alt': self.alt_dict["adc_stdd"][156:], 'ratio': self.ratio_dict["adc_stdd"][156:]}
        }
        
        #actually adding data points
        for dtype, ftype, atype in zip([data_stdd,data_mean],[fig_stdd,fig_mean],[axes_stdd,axes_mean]):
            for row, place in enumerate(rows):
                for col, chip in enumerate(cols):
                    place = place.split(' ', 1)[0].lower()
                    
                    y = dtype[chip][place]
                    x = list(range(78))
                    
                    ax = atype[row,col]
                    ax.scatter(x,y, s=5)
                    ax.grid()
                    
                    #Styling axes 
                    if place == "ratio":
                        ax.set_ylim(-2,4)
                        ax.yaxis.set_ticks(np.arange(-2, 5, 1))
                    else:
                        if dtype["data_type"] == "mean":
                            ax.set_ylim(-2,10)
                            ax.yaxis.set_ticks(np.arange(-2, 11, 2))
                        elif dtype["data_type"] == "stdd":
                            ax.set_ylim(-2,400)
                            ax.yaxis.set_ticks(np.arange(0, 402, 100))
            #Setting Titles
            for ax, col in zip(atype[0], cols):
                ax.set_title(col)
            for ax, row in zip(atype[:,0], rows):
                ax.set_ylabel(row, size='large')
            
            #Plot style
            ftype.set_figwidth(12)
            ftype.suptitle(f"adc_{dtype["data_type"]} for {self.barcode} at Fermi and {self.alt_loc.upper()}")
        fig_mean.show()
        #print("Plot displayed — press Ctrl+C to quit")
        #input("Press Enter to continue...")
        fig_mean.savefig(f"Plots/{self.barcode}_adc_mean_{self.test_ver}.png")
        fig_stdd.show()
        #print("Plot displayed — press Ctrl+C to quit")
        #input("Press Enter to continue...")
        fig_stdd.savefig(f"Plots/{self.barcode}_adc_stdd_{self.test_ver}.png")

def main():    
    ###### Testing/Dev Suite. replace with dynamic file paths!! ######
    db_path = r"C:\cygwin64\home\charl\25CERN\CassetteReception\cassetteReception.db" #real
    #db_path = r"C:\cygwin64\home\charl\25CERN\CassetteReception\test.db" #rm after dev
    createDB(db_path)
    
    fermi_pedestal_meas = r"C:\cygwin64\home\charl\25CERN\CassetteReception\ROOTFiles\fermi_pedestal_run0.root" 
    fermi_yaml_file = r"C:\cygwin64\home\charl\25CERN\CassetteReception\YAMLFiles\fermi_initial_full_config.yaml" 
    
    cmu_pedestal_meas = r"C:\cygwin64\home\charl\25CERN\CassetteReception\ROOTFiles\cmu_pedestal_run0.root" 
    cmu_yaml_file = r"C:\cygwin64\home\charl\25CERN\CassetteReception\YAMLFiles\cmu_initial_full_config.yaml" 
#pedestal_run_date_time.root
    
    barcode = "320LDF3CXTT1003"
    loc = "cmu"
    ##################################################################
    """db = DBFuncs(db_path)
    db.rmMod(barcode)
    db.addNewModToDB(barcode,loc,cmu_pedestal_meas,cmu_yaml_file,loc_at_fermi="Reception")
    db.addYAMLToMod(barcode, fermi_yaml_file, "fermi")
    db.addYAMLToMod(barcode, cmu_yaml_file, "cmu")
    db.addADCTestToMod(barcode, "fermi", fermi_pedestal_meas)
    test = f"{barcode}_fermi_v1"

    test_results = db.getADCTest(test)
    print(type(test_results))
    
    
    fermi_tests = db.getFermiTestsFromMod(barcode)
    print("fermi_tests: ", fermi_tests)
    
    all_mods = db.getMods()
    print("all_mods: ", all_mods)
    """
    
    comp = ComparePlots(db_path, barcode, loc, "v1")
    print(comp.fermi_test)
    comp.comparePlots()
    comp.plotComparison()
    print("plots finished")

if __name__ == '__main__':
        main()