R.Version()$version.string

ipak <- function(pkg){
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg)) 
        install.packages(new.pkg, dependencies = TRUE)
    sapply(pkg, require, character.only = TRUE)
}

packages <- c('fields', 'plot3D', 'sp', 'rhdf5', 'xts', 'zoo', 'signal', 'maptools', 'polynom', 'geoR', 'phylin')
ipak(packages)

# imodel=c("AT-ugrid/TH-ringold-alluvium/")
imodel= c("HFR-thorne_150m/")

data_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/data/"

# # geoframework data

fname_bath= paste0(data_dir, "newbath_10mDEM_grid.ascii")
fname_EV= paste0(data_dir, "300A_EV_surfaces_012612.dat")
fname_tube_loc = paste0(data_dir, "Aquifer_Tube_Location.csv")

HFR_data_dir = "/global/project/projectdirs/m1800/pin/HFR-thermal/data/"
# mass1 data
fname_mass1_coord = paste(HFR_data_dir, "MASS1/Mass1_datum_shift.csv", sep = "")
fname_mass1_pts = paste(HFR_data_dir, "MASS1/transient_1976_2019/", sep = "")
fname_mass.info = paste(HFR_data_dir, "MASS1/mass_info.csv", sep = "") 

# fname_300A_well = "/global/project/projectdirs/m1800/pin/AT-model/data/all_wells_2017-2018.csv"
# fname_300A_well_coord = "/global/project/projectdirs/m1800/pin/AT-model/data/300A_well_coordinates_all.csv"
# #river geometry
fname_river.geo = paste(HFR_data_dir, "river_geometry.csv", sep = "") 

# # if statement
# is.plot = T
# is.smooth = T
# ## ------------------------output figures
figure_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/figures/"

fig.model_map = paste0(figure_dir, "model_map_20x10m.jpg")
fig.model_map_zoom = paste0(figure_dir, "model_map_20x10m-zoom.jpg")



##----------------------- R object files
result_dir = paste0("/global/project/projectdirs/m1800/pin/HFR-thorne/results/", imodel)

fname_model_inputs.r = paste(result_dir, "model_inputs.r", sep = "")
fname_geoFramework.r = paste(result_dir,"geoframework.r", sep = "")
fname_dem.r = "/global/project/projectdirs/m1800/pin/HFR-thorne/results/dem.r"

# fname_mass1_xts = "/global/project/projectdirs/m1800/pin/HFR-thermal/results/mass.data.xts_2007_2019.r"
fname_mass1_xts = "/global/project/projectdirs/m1800/pin/HFR-thorne/results/mass.data.xts_2007_2019.r"
fname_mass1_data.r = "/global/project/projectdirs/m1800/pin/HFR-thermal/results/mass.data_1976_2019.r"

fname_BC_head.r = paste0(result_dir, "BC_head.r")
fname_BC_temp.r = paste0(result_dir, "BC_temp.r")
##----------------------- PFLOTRAN input files
input_dir = paste0("/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/", imodel)

# fname_material_h5 = paste(input_dir, "AT_material_river.h5", sep = "")
# fname_initial.h5 = paste(input_dir, "AT_H_Initial.h5", sep = "")
# fname.BC.h5 = paste(input_dir, "AT_H_BC.h5", sep = "")

# fname_initial_temp.h5 = paste(input_dir, "AT_Temp_Initial.h5", sep = "")
# fname.BC_Temp.h5 = paste(input_dir, "AT_Temp_BC.h5", sep = "")
# fname_inland_temp = paste(input_dir, "inland_temp.txt", sep = "")
# fname_DatumH = paste(input_dir, "DatumH_River_", sep = "")
# fname_Gradients = paste(input_dir, "Gradients_River_", sep = "")
fname_DatumH = "/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/river_bc/stage_2015-2019/DatumH_River_"
fname_Gradients = "/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/river_bc/stage_2015-2019/Gradients_River_"
# fname_temperature = "/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/river_bc/Temp_River_"


output_dir = paste0("/global/project/projectdirs/m1800/pin/HFR-thorne/outputs/", imodel)

# load(fname_model_inputs.r)

# start.time = as.POSIXct("2007-01-01 00:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")
start.time = as.POSIXct("2015-01-01 00:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")

end.time =  as.POSIXct("2019-11-01 00:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")

mass.coord = read.csv(fname_mass1_coord)
# mass.coord[,"easting"] = mass.coord[,"easting"]-model_origin[1]
# mass.coord[,"northing"] = mass.coord[,"northing"]-model_origin[2]

rownames(mass.coord) = mass.coord[,'quadrant']

attach(fname_mass1_data.r)

##------------------------- compile all the mass1 data --------------------------
slice.list = as.character(mass.coord[,1])
  
mass.data = list()
for (islice in slice.list) {
  print(islice)
  mass.data[[islice]] = read.csv(paste(fname_mass1_pts,"mass1_",
                                       islice,".csv",sep=""))
}
names(mass.data) = slice.list

for (islice in slice.list) {
  print(islice)
  mass.data[[islice]][["date"]] =
    as.POSIXct(mass.data[[islice]][["date"]],format="%Y-%m-%d %H:%M:%S",tz='GMT')
  mass.data[[islice]][["stage"]] = mass.data[[islice]][["stage"]] + mass.coord[islice, "NGVD88Offse"] # convert datum from NGVD29 to NAVD88
}

# save raw mass1 data
save(mass.data, file=fname_mass1_data.r)

attach(fname_mass1_xts)

slice.list = names(mass.data)

time.index = seq(from=start.time,to=end.time,by="1 hour")
ntime = length(time.index)
simu.time = c(1:ntime-1)*3600

mass.data.xts = list()
for (islice in slice.list)
{
#   print(islice)
  mass.data.xts[[islice]] = xts(mass.data[[islice]],
                                order.by=mass.data[[islice]][["date"]], unique=TRUE, tz="GMT")
  
  #only store data within 5 min range of even hour, i.e. 04:59 stored as 05:00
  mass.data.xts[[islice]] = mass.data.xts[[islice]][
    .indexmin(mass.data.xts[[islice]][,"date"]) %in% c(56:59,0:5)] 

#   mass.data.xts[[islice]] = mass.data.xts[[islice]][c("2007","2008","2009",'2010','2011','2012','2013','2014','2015','2016')]  #time slice b/w 2008 ~ 2016

  index(mass.data.xts[[islice]]) = round(index(mass.data.xts[[islice]]), units="hours")
    
  mass.data.xts[[islice]] = mass.data.xts[[islice]][!duplicated(.index(mass.data.xts[[islice]]))]
  mass.data.xts[[islice]] = merge(mass.data.xts[[islice]], time.index, join = "inner") # NA in "date" column will be introduced, as xts is essentially matrix
  
}

# save formatted mass1 data
save(mass.data.xts, file=fname_mass1_xts)

time.index = seq(from=start.time,to=end.time,by="1 hour")
ntime = length(time.index)
simu.time = c(1:ntime-1)*3600

##------------------------- generate river bc-----------------------------------
slice.list = names(mass.data.xts)
# slice.list = c("321", "322")
# islice = slice.list
nslice = length(slice.list)


for (islice in slice.list)
{
    mass.data.xts[[islice]] = mass.data.xts[[islice]][index(mass.data.xts[[islice]])>=start.time,]
    mass.data.xts[[islice]] = mass.data.xts[[islice]][index(mass.data.xts[[islice]])<=end.time,]    
}

mass.gradient = rep(NA,ntime)
mass.level = array(NA,c(nslice,ntime))
rownames(mass.level) = slice.list
for (islice in slice.list) {
    mass.level[islice,] = mass.data.xts[[islice]][,"stage"]
}
# available.date = which(colSums(mass.level,na.rm=TRUE)>200)

mass.temp = array(NA,c(nslice,ntime))
rownames(mass.temp) = slice.list
for (islice in slice.list) {
    mass.temp[islice,] = mass.data.xts[[islice]][,"temperature"]
}

nwindows = 6 #hour
# nwindows = 24*1 #1d
# nwindows = 24*7 #1 week
dt = 3600
filt = Ma(rep(1/nwindows,nwindows))
# new.mass.level = array(NA,c(nslice,(ntime+1)))
new.mass.level = array(NA,c(nslice,ntime+1)) #moving average (ma) add 1 extra time to match the dim(ma_value)

for (islice in 1:nslice)
{
#     print(islice)
    ori_time = simu.time
    ori_value = mass.level[islice,]

    ma_value = filter(filt,ori_value)
    ma_time = ori_time-dt*(nwindows-1)/2 # ma_time offset by dt/2
    ma_value = tail(ma_value,-nwindows)
    ma_time = tail(ma_time,-nwindows)
    ma_value = c(ori_value[ori_time<min(ma_time)],ma_value)
    ma_time = c(ori_time[ori_time<min(ma_time)],ma_time)
    ma_value = c(ma_value,ori_value[ori_time>max(ma_time)])
    ma_time = c(ma_time,ori_time[ori_time>max(ma_time)])

    new.mass.level[islice,] = ma_value
}

original_mass_level = mass.level
original_time_series = simu.time
original_time_series = original_time_series + start.time

new_time_series = ma_time + start.time

# for (islice in 1:nslice) {
  islice = 1
#   jpeg(paste("figures/mass_original_vs_mvAve_", slice.list[islice], "_",nwindows,"h.jpg", sep=''),width=8,height=5,units='in', res = 300)


  plot(original_time_series, original_mass_level[islice, 1:length(original_time_series)], 
       type = "l", col= "black", axes = T, 
       xlab=NA,ylab="Hydaulic head (m)",
       xaxs = 'i'
      )
  box()

#   axis(2,at=seq(118,128,2),mgp=c(5,0.7,0),cex.axis=1)

#   axis.POSIXct(1,at=seq(as.Date("2007-01-01",tz="GMT"),
#                         to=as.Date("2019-01-01",tz="GMT"),by="year"),
#                format="%Y",mgp=c(5,0.7,0))
  

  lines(new_time_series, new.mass.level[islice,], col= "red")


  legend("topright",legend = c("original","mvAve"), col = c("black", "red"), lty = c("solid", "solid"), bty = "n")
  title(paste("mass_original_vs_ma_", slice.list[islice], sep=''))
#   dev.off()
# }

# if smoothed 
mass.level = new.mass.level
simu.time = ma_time
ntime = length(simu.time)

##------------------------calculate gradient--------------------------------##
# mass.gradient = array(NA,c(nslice,(ntime+1)))
mass.gradient.x = array(NA,c(nslice,ntime))
mass.gradient.y = array(NA,c(nslice,ntime))
rownames(mass.gradient.y) = slice.list
rownames(mass.gradient.x) = slice.list

for (islice in 1:(nslice-1)) #from top to bottom. 
{
  distance = sqrt((mass.coord[slice.list[islice+1],
                              "northing"]-mass.coord[slice.list[islice],"northing"])^2 +
                    (mass.coord[slice.list[islice+1],"easting"]-mass.coord[slice.list[islice],"easting"])^2)
  ## calculate grad based on x-direction
  mass.gradient.x[slice.list[islice],] = (mass.level[slice.list[islice+1],]-mass.level[slice.list[islice],]
  )/distance*(mass.coord[slice.list[islice+1],"easting"]-mass.coord[slice.list[islice],"easting"])/distance   
  
  ## calculate grad based on y-direction    
  mass.gradient.y[slice.list[islice],] = (mass.level[slice.list[islice+1],]-mass.level[slice.list[islice],]
  )/distance*(mass.coord[slice.list[islice+1],"northing"]-mass.coord[slice.list[islice],"northing"])/distance 
}


# gradient_314 is calcuated based on 315 and 314
for (islice in 1:(nslice-1))
{ 
#     print(islice)
    Gradients = cbind(simu.time,
                      mass.gradient.x[slice.list[islice],],
                      mass.gradient.y[slice.list[islice],],
                      rep(0,(ntime)))
    
    DatumH = cbind(simu.time,
                   rep(mass.coord[slice.list[islice],"easting"],ntime),
                   rep(mass.coord[slice.list[islice],"northing"],ntime),                                      
                   mass.level[islice,])

    write.table(DatumH, file=paste(fname_DatumH, slice.list[islice],'.txt',sep=""),col.names=FALSE,row.names=FALSE) 
    write.table(Gradients, file=paste(fname_Gradients, slice.list[islice],".txt",sep=''),col.names=FALSE,row.names=FALSE)
    
    
}
print(paste('Datum files are saved in :',fname_DatumH))
print(paste('Gradient files are saved in :',fname_Gradients))

for (islice in 1:(nslice-1))
{ 
    print(islice)
    Gradients = cbind(simu.time[1],
                      mass.gradient.x[islice, 1],
                      mass.gradient.y[islice, 1],
                      0)
    
    DatumH = cbind(simu.time[1],
                   mass.coord[islice,"easting"],
                   mass.coord[islice,"northing"],                                      
                   mass.level[islice, 1])

    write.table(DatumH, file=paste(fname_DatumH, slice.list[islice],'.txt',sep=""),col.names=FALSE,row.names=FALSE) 
    write.table(Gradients, file=paste(fname_Gradients, slice.list[islice],".txt",sep=''),col.names=FALSE,row.names=FALSE)
    
    
}

print(paste('Datum and gradient files are saved in :',fname_DatumH))

time.index = seq(from=start.time,to=end.time,by="1 hour")
ntime = length(time.index)
simu.time = c(1:ntime-1)*3600

for (islice in 1:(nslice-1))
{ 
    print(islice)

    iTemp = cbind(simu.time, mass.temp[islice,])
    write.table(iTemp, file=paste(fname_temperature, slice.list[islice],".txt",sep=''),col.names=FALSE,row.names=FALSE)
    
    
}

print(paste('Datum and gradient files are saved in :',fname_temperature))

for (islice in 1:(nslice-1))
{ 
    print(islice)
#     Gradients = cbind(simu.time,
#                       mass.gradient.x[islice,],
#                       mass.gradient.y[islice,],
#                       rep(0,(ntime)))
    
    iTemp = cbind(simu.time[1], mass.temp[islice, 1])

#     write.table(DatumH, file=paste(fname_DatumH, slice.list[islice],'.txt',sep=""),col.names=FALSE,row.names=FALSE) 
    write.table(iTemp, file=paste(fname_temperature, slice.list[islice],".txt",sep=''),col.names=FALSE,row.names=FALSE)
    
    
}


