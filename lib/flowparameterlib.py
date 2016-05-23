import numpy as np
import sys
import os
import shutil
import distlib
import scipy
from scipy.spatial import cKDTree

def arrhenius(T):
  '''
  This function takes a temperature and outputs the flow parameter 
  following Cuffey and Paterson 2010, pg. 72.
  '''
  
  A=np.zeros_like(T)
  for i in range(0,len(T)):
    if (T[i] > 273.15):
      A[i]=2.4E-24
    elif (T[i] > 263.15):
      A[i]=3.5E-25* np.exp(-115.0E03/8.314 * (1/T[i] - 1/263.15))
    else:
      A[i]=3.5E-25 * np.exp(-60.0E03/8.314 * (1/T[i] - 1/263.15))
    	
  return A 

def load_kristin(glacier,x,y,type='A',dir='none'):

  # Load file if it already exists
  fileA = os.path.join(os.getenv("DATA_HOME"),"Climate/IceTemperature/"+glacier+"/flowA.xyz")
  fileT = os.path.join(os.getenv("DATA_HOME"),"Climate/IceTemperature/"+glacier+"/flowT.xyz")
  if (type=='A') and (os.path.isfile(fileA)):
    shutil.copy(fileA,dir+"flowA.xyz")
    output = 'success'
  elif (type=='T') and (os.path.isfile(fileT)):
    shutil.copy(fileT,dir+"flowT.xyz")  
    output = 'success' 
  else:
    # Get modeled temperatures from Kristin's work
    if glacier == 'Helheim':
      kristin_file=os.path.join(os.getenv("DATA_HOME"),"Climate/IceTemperature/Helheim/xyzTAhelheim_2016.txt")
    elif glacier == 'Kanger':
      kristin_file=os.path.join(os.getenv("DATA_HOME"),"Climate/IceTemperature/Kanger/xyzTAKanger_2016.txt")
    else:
      sys.exit('Unknown glacier')  
  
    # Get grid values for gridding Kristin's values
    nx = len(x)
    ny = len(y)
  
    dx = x[1]-x[0]
    dy = y[1]-y[0]
  
    xmin = x[0]
    xmax = x[-1]
    ymin = y[0]
    ymax = y[-1]

    # Variables for loading Kristin's values
    xT = []
    yT = []
    zT = []
    tT = []
    aT = []

    # Read in the data from a file
    fid = open(kristin_file, "r")
    line = fid.readline().split(',')
    line = fid.readline().split(',')

    while(line[0] != ""):
      xT.append(float(line[0]))
      yT.append(float(line[1]))
      zT.append(float(line[2]))
      tT.append(float(line[3]))
      aT.append(float(line[4][:-1]))
      line = fid.readline().split(',')
    fid.close()

    # Condense the list so that all the temperature / viscosity from the same
    # (x, y)-point is contained in one list, and the data in a list of lists
    X = []
    Y = []
    Z = []
    T = []
    A = []
    
    X.append(xT[0])
    Y.append(yT[0])
    Z.append([zT[0]])
    T.append([tT[0]])
    A.append([aT[0]])      
      
    k = 0
    
    for n in range(1, len(xT)):
      if xT[n] == xT[n - 1] and yT[n] == yT[n - 1]:
        Z[k].append(zT[n])
        T[k].append(tT[n])
        A[k].append(aT[n])
      else:
        X.append(xT[n])
        Y.append(yT[n])
        Z.append([zT[n]])
        T.append([tT[n]])
        A.append([aT[n]])
        k += 1
        
    nn = len(X)
    
    X = np.asarray(X)
    Y = np.asarray(Y)
    
    for k in range(nn):
      Z[k] = np.asarray(Z[k])
      T[k] = np.asarray(T[k])
      A[k] = np.asarray(A[k])

    Xn = []
    Yn = []
    Zn = []
    Tn = []
    An = []
    fracs = []
    
    D = distlib.transect(X,Y)
    for i in range(1,len(D)):
      if D[i] - D[i-1] < 5000.:
        dtot = D[i] - D[i-1]
        dn = np.arange(D[i-1],D[i],500)
        for j in range(0,len(dn)):
          Xn.append(float(np.interp(dn[j],[D[i-1],D[i]],[X[i-1],X[i]])))
          Yn.append(float(np.interp(dn[j],[D[i-1],D[i]],[Y[i-1],Y[i]])))
          frac = (D[i]-dn[j])/dtot
          fracs.append(frac)
          Zn.append(frac*np.asarray(Z[i-1])+(1-frac)*np.asarray(Z[i]))
          Tn.append(frac*np.asarray(T[i-1])+(1-frac)*np.asarray(T[i]))
          An.append(frac*np.asarray(A[i-1])+(1-frac)*np.asarray(A[i]))
      else:
        Xn.append(X[i])
        Yn.append(Y[i])
        Zn.append(Z[i])
        Tn.append(T[i])
        An.append(A[i])


    # Set the number of vertical layers
    nz = 21
    
    temp = np.zeros((ny,nx,nz)) # Kelvin
    temp[:,:,:] = 263.
    rate = np.zeros((ny,nx,nz))
    rate[:,:,:] = arrhenius([263.])

    # Make a KD-tree so we can do range searches fast
    tree = cKDTree(np.column_stack([Xn,Yn]))

		# Make a gridded data set from the model output

    # For each point in the grid,
    for i in range(ny):
      for j in range(nx):
		    
        #L = tree.query_ball_point( (x[j], y[i]), 5000 )
		    
		    # Find five closest points
		    dists = np.sqrt((x[j]-Xn)**2+(y[i]-Yn)**2)
		    allind = np.where(dists < 5000.)[0]
		    sortind = dists[allind].argsort()
		    ind = allind[sortind[0:10]]
		    #ind = ind[dists.sort < 5000.]
		    
		    # Initialize the weights to 0
		    weights = 1.0
		    
		    # For all the nearby model points,
		    if len(ind) > 0:
		      for l in ind:
		        xp = Xn[l]
		        yp = Yn[l]
		      
		        # find the distance to the current point and the
		        # appropriate weight
		        r = np.sqrt( (x[j] - xp)**2 + (y[i] - yp)**2 )
		        w = (5000./(r+dx))**3
		        weights += w
		      
		        # For each point within the current vertical column,
		        for k in range(nz):
		          # find which point within the nearby vertical
		          # column to interpolate from
		          m = (k * (len(Zn[l]) - 1)) / (nz - 1)
		        
		          # Add up the value to the running average
		          rate[i, j, k] += w * An[l][m]
		          temp[i, j, k] += w * Tn[l][m]
		    
		      # Normalize the running average by the weight sum
		      rate[i,j,:] /= weights  
		      temp[i,j,:] /= weights
		      if np.max(temp[i,j,:])>300.:
		        print i,j
    
    smoothtemp = np.zeros_like(temp)
    smoothrate = np.zeros_like(rate)
    for j in range(0,nz):
      smoothtemp[:,:,j] = scipy.ndimage.filters.gaussian_filter(temp[:,:,j],sigma=6,truncate=6)
      smoothrate[:,:,j] = scipy.ndimage.filters.gaussian_filter(rate[:,:,j],sigma=6,truncate=6)
    
    # Calculate flow law parameter for temperatures, using parameterization from Paterson 2010
    newrate = np.zeros_like(temp)
    for i in range(0,nx):
      for j in range(0,ny):
        newrate[j,i,:] = arrhenius(np.array(smoothtemp[j,i,:]))
    
    if dir != 'none':
      fidA = open(dir+"flowA.xyz", "w")
      fidA.write("{0}\n{1}\n{2}\n".format(len(x), len(y), len(newrate[0,0,:])))
      
      fidT = open(dir+"flowT.xyz", "w")
      fidT.write("{0}\n{1}\n{2}\n".format(len(x), len(y), len(temp[0,0,:])))

      for j in range(len(x)):
        for i in range(len(y)):
          fidA.write("{0} {1} ".format(x[j], y[i]))
          fidT.write("{0} {1} ".format(x[j], y[i]))
          for k in range(len(newrate[0,0,:])):
            fidA.write("{0} ".format(newrate[i, j, k]))
            fidT.write("{0} ".format(temp[i, j, k]))
          fidA.write("\n")
          fidT.write("\n")
      fidT.close()
      fidA.close()
      
  return output
  