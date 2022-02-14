## This script contains the classes and functions for the execution of the Arusha
## Assignment in PCRaster (www.pcraster.geo.uu.nl)

#In the exercise markdown document, there may contain simple functions necessary.


#All the input files were previously translated to .map (PCraster format) and adjusted to coincide.
from pcraster import *
from pcraster.framework import *
import numpy as np

class RechargeModel(DynamicModel):
    def __init__(self, land_use_map, climateyear):
        DynamicModel.__init__(self)
        setclone(land_use_map)
        self.climyear = climateyear
        self.year = re.search(r'\d{4}', land_use_map)[0]
        self.year = re.search(r'\d{2}$',self.year)[0]
        self.land_use_map = land_use_map
        
        
    
    def initial(self):
        land_use_folder = "LULC Input"
        other_folder = "Other input"
        self.land_use = self.readmap(self.land_use_map)
        self.soil = self.readmap(os.path.join(other_folder, "soil"))
        self.dem = self.readmap(os.path.join(other_folder,"elevation"))
        self.slope = self.readmap(os.path.join(other_folder,"slope"))
        self.threshold = lookupscalar(os.path.join(other_folder,"land_use_threshold.tbl"),self.land_use)
        self.soilcapacity = lookupscalar(os.path.join(other_folder, "soil_cap.tbl"),self.soil)
        self.soilextdepth = lookupscalar(os.path.join(other_folder,"soil_ext_depth.tbl"),self.land_use)
        self.cropcoef = lookupscalar(os.path.join(other_folder,"crop_coef.tbl"),self.land_use)
        self.initial_su = lookupscalar(os.path.join(other_folder,"initial_sto_pct.tbl"),self.land_use)
        #Initial Soil Storage:
        self.su = self.initial_su*self.soilcapacity*self.soilextdepth
        self.recharge_list = []
        
        self.suet = self.su
        
        #Initials Heads:
        self.gwheads = self.readmap(os.path.join(other_folder,"gwheads"))
        #Drawdown:
        self.abs_rate = lookupscalar(os.path.join(other_folder,"abs_rate.tbl"),self.land_use)
        #Sy:
        self.sy = 0.1
        
        #Initial Runoff(0):
        
        self.runoff = scalar(0)
        
        #Initial accumulated recharge:
        self.recharge_acc = scalar(0)
        
        #Initial accumulated actual evap:
        self.evap_acc = scalar(0)
        
    
    def dynamic(self):
        climate_folder = "Climate data"
        prec = timeinputscalar(os.path.join(climate_folder,"precipitation_20"+self.climyear+ ".tss"),1)
        refET = timeinputscalar(os.path.join(climate_folder,"et_20"+self.climyear+".tss"),1)
        potET = refET * self.cropcoef
        
        #Effective Precipitation:
        eff_prec = min(prec, self.threshold)
        
        #Runoff
        self.runoff = self.runoff + prec-eff_prec
        self.report(self.runoff, os.path.join("output","a_r_"+self.year))
        
        #Calculate soil storage
        self.su = self.su + eff_prec
        recharge = max(0, (self.su - self.soilcapacity*self.soilextdepth))
        recharge_map = recharge
        self.recharge_acc += recharge_map
        self.su = self.su - recharge
        #Actual ET calculated with Tibor linear model for reduction of potential ET with available storage
        actET = ifthenelse(self.su >= self.suet, potET, potET*self.su/self.suet)
        self.su = self.su - actET
        self.evap_acc = self.evap_acc + actET
        #Summarise recharge
        recharge = maptotal(recharge)*250**2/maparea(recharge)
        recharge = pcr2numpy(recharge,-10)
        recharge = recharge[50,50]
        self.recharge_list.append(recharge)
        self.report(self.recharge_acc, os.path.join("output","recc_"+self.year))
        
        
        #Calculate groundwater heads:
        #self.gwheads = self.gwheads + (recharge_map - self.abs_rate)*1e-3/self.sy
        #self.report(self.gwheads, os.path.join("output","heads_"+self.year))
        
        #Export Evapotranspiration:
        self.report(self.evap_acc, os.path.join("output", "evap_"+self.year))
    
