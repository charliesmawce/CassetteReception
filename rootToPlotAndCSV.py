import uproot
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib as mpl
mpl.rcParams['text.usetex'] = False

file_path = "c:/cygwin64/home/charl/25CERN/CassetteReception/ROOTFiles/summary_of_v3a_TTU_modules.root"
#input("Please enter the file path") 
#current path to test file! "c:/cygwin64/home/charl/25CERN/CassetteReception/summary_of_v3a_TTU_modules.root" 


############ script initializations ############
file = uproot.open(file_path) 
treenames = file.keys()
treenames = [t[:-2] for t in treenames]

tree_list = [] 
for treename in treenames: #structuring filenames for uproot.iterate
        tree_list.append(f"{file_path}:{treename}")
pdf_plots = PdfPages(f'{treenames[0]}_{treenames[-1][-4:]}plots.pdf')


############ i vs v data formatting and csv ############
dict_mods = {'module_name':[], 'meas_v':[], 'meas_i':[]}
i_v_list = []

for index_tree, branches in enumerate(uproot.iterate(tree_list)):
        mod_name = treenames[index_tree]    
        list_y = [(i*(10**6)) for i in branches["meas_i"].tolist()]
                        
        list_x = branches["meas_v"].tolist()[:len(list_y)] 

        dict_mods['module_name'].append(mod_name)
        dict_mods['meas_v'].append(list_x)
        dict_mods['meas_i'].append(list_y)

        dataframe = file[str(treenames[index_tree])].arrays(library = "pd")
        i_v_df= dataframe.drop(columns=["adc_stdd", "adc_mean"])
        i_v_df.to_csv(f"CSVFiles/{treenames[index_tree]}.csv", index = False)


############ i vs v plot for a group of modules ############
dict_mods = {key: val for key, val in dict_mods.items() if val != 0}
i_vs_v_df = pd.DataFrame.from_dict(dict_mods)

for i in range(len(i_vs_v_df.index)): #i vs v plotting
        row = i_vs_v_df.index[i]
        
        plt.plot(i_vs_v_df['meas_v'].loc[row], i_vs_v_df['meas_i'].loc[row], marker = ".", linewidth = 1, markersize = 4, label = i_vs_v_df['module_name'].loc[row])
        plt.grid(which='minor', color="#D1D1D1", linestyle='-', axis = 'x')
        plt.grid(which='major', color="#454545", linestyle='-')
        plt.minorticks_on()
        plt.title("Current vs Voltage")
        plt.yscale("log")
        plt.xlabel("Voltage (V)")
        plt.ylabel("Current (μA)")
        plt.xlim([0,1000])
plt.legend(loc = 'lower right',bbox_to_anchor=(1.4,0))
plt.savefig(f"Plots/{treenames[0]}_to_{treenames[-1][-4:]}_i_v.pdf", bbox_inches="tight")
plt.close()


############ adc_stdd and adc_mean data, csv, and plots ############
# initialize lists
x = []
y_mean = []
y_stdd = []
y_type = [y_mean,y_stdd]\

for index_tree, branches in enumerate(uproot.iterate(tree_list)):
        #formatting data for plots and building csvs
        for idx, adc in enumerate(["adc_stdd", "adc_mean"]):
                adc_list = branches[adc]
                #building csvs
                adc_df = pd.read_csv(f"CSVFiles/{treenames[index_tree]}.csv")
                try:
                        adc_df.insert(idx + 2, adc, adc_list)
                        adc_df.to_csv(f"CSVFiles/{treenames[index_tree]}.csv", index = False)
                except Exception as e:
                        print("Warning: you are trying to make a file that already exits. Please delete any files that you wish to rewrite.", e)

                #formatting data
                for index in range(len(adc_df.index)-1):
                        if adc == "adc_stdd":
                                y_stdd.append(adc_df.iat[index, 2])
                        else:
                                y_mean.append(adc_df.iat[index, 3])
                                x.append(index)
                
        #plots
        fig, (ax_stdd, ax_mean) = plt.subplots(2, sharex=True)
        ax_stdd.set_ylim(-2,6)
        ax_mean.set_ylim(-2,6)
        ax_stdd.scatter(x, y_stdd)
        ax_mean.scatter(x, y_mean)

        ax_stdd.set_ylabel("adc_stdd (noise)")
        ax_mean.set_ylabel("adc_mean (pedetance)")

        ax_stdd.grid(visible=None, which='major', axis='both')
        ax_stdd.xaxis.set_ticks(np.arange(0, 250, 20))
        ax_mean.grid(visible=None, which='major', axis='both')
        ax_mean.xaxis.set_ticks(np.arange(0, 250, 20))
        ax_stdd.grid(visible=None, which='minor', axis='x', linestyle = '-')
        ax_mean.grid(visible=None, which='minor', axis='x', linestyle = '-')
        
        fig.suptitle(str(treenames[index_tree]))
        fig.set_figwidth(9)
        plt.xlim([0,240])
        #plt.figure(treenames[index_tree])
        plt.savefig(f"Plots/{treenames[index_tree]}_adc.pdf")
        #pdf_plots.savefig()
        plt.close()
        #plt.show()





