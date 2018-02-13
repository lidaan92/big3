 
import subprocess
import time
import os

glacier = 'Kanger'
#glacier = 'Helheim'

# Mesh geometry

meshshp = 'glacier_extent_inversion_front'
#bname = 'smith'
bname = 'morlighem'
bmodel = 'aniso'
bsmooth = '5'
bottomsurface = 'bed' # or 'iceshelf'
temperature = 'model'#'-10.0'#'model'
lc = '250 250 250 250'
#lc = '1000 1000 4000 5000'

if glacier == 'Helheim':
  dates = ['20070912']
  #dates = ['20120316']
  #dates = ['20070912',\
  #        '20110319','20110615','20110828','20111116',\
  #         '20120316','20120624','20120908','20121205',\
  #         '20130209','20130508','20130804','20131031',\
  #         '20140127','20140509','20140731','20141016']
elif glacier == 'Kanger':
#  dates = ['20070728']
  dates = ['20120213']
#  dates = ['20110308','20110708','20110826','20111106',\
#           '20120213','20120522','20121012','20121217',\
#           '20130210','20130714','20131004','20131204',\
#           '20140213',20150808]  

# Inversion options
method = 'adjoint'
itmax = 500
regpars = ['1e9']
#regpars = ['1e8','1e9','1e10','5e11','1e11','2e11','5e11','1e12','1e13','1e14'] 

nparts = 4

if meshshp.endswith('nofront'):
  frontBC = 'pressure'
else:
  frontBC = 'velocity'


#Loop over PBS jobs
for date in dates:

  # Output mesh name
  meshname = 'DEM'+date+'_modelT'

  # Create mesh
  command = "python "+os.path.join(os.getenv("CODE_HOME"),"big3/modeling/meshing/mesh_3d.py")+\
            " -glacier {0} -mesh {1}".format(glacier,meshshp)+\
            " -d {0} -bname {1} -bmodel {2}".format(date,bname,bmodel,bsmooth)+\
            " -bsmooth {0} -lc {1} -n {2}".format(bsmooth,lc,nparts)+\
            " -output {0} -zb {1}".format(meshname,bottomsurface)+\
            "  -temperature {0} -ssa True".format(temperature)
  print command
  os.system(command)

 
  for regpar in regpars:
    
    # Customize job options
    command = "python "+os.path.join(os.getenv("CODE_HOME"),"big3/modeling/inversions/inversion_ssa.py")+\
              " -glacier {0} -method {1} -regpar {2} -mesh {3} -front {4} -n {5} -temperature {6} -itmax {7} -sidewall velocity".format(glacier,method,regpar,meshname,frontBC,nparts,temperature,itmax)

    print command
    os.system(command)