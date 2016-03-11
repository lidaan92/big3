# This file takes the elevation data and plots it along a flowline.

import os
import sys
import glaclib, zslib, icefrontlib, floatlib, bedlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
import matplotlib
import scipy
from matplotlib.ticker import AutoMinorLocator

sys.path.append(os.path.join(os.getenv("CODE_HOME"),"Modules/demtools"))
import gmtColormap
cpt_rainbow = gmtColormap.get_rainbow()
plt.register_cmap(cmap=cpt_rainbow)

##########
# Inputs #
##########

args = sys.argv
glacier = args[1][:] # Options: Kanger, Helheim

x,y,zb,dists = glaclib.load_flowline(glacier,filt_len=2.0e3,verticaldatum='geoid',shapefilename='flowline_flightline')

xref,yref,zref = zslib.gimp_grid(np.min(x)-10.0e3,np.max(x)+10.0e3,np.min(y)-10.0e3,np.max(y)+10.0e3,glacier,verticaldatum='geoid')

plot_overview = 1.
plot_time = 1.

################
# Get terminus #
################

terminus_val, terminus_time = icefrontlib.distance_along_flowline(x,y,dists,glacier,type='icefront')

################
# Get ATM data #
################

atm_data = zslib.atm_along_flowline(x,y,glacier,'all',cutoff='none',maxdist=250,verticaldatum='geoid',filt_len='none')
zpt_atm,zpstd_atm,time_atm = zslib.atm_at_pts(x,y,glacier,years='all',maxdist=250,verticaldatum='geoid',method='average')

##############################
# Get Worldview and TDX Data #
############################## 

zs_dem,time_dem = zslib.dem_along_flowline(x,y,glacier,years='all',cutoff='none',verticaldatum='geoid',filt_len='none')
zpt_dem,zpt_std,time_zpt = zslib.dem_at_pts(x,y,glacier,years='all',verticaldatum='geoid',cutoff='terminus',method='average',radius=250)

############################
# GIMP elevation at points #
############################

gimp = zslib.gimp_at_pts(x,y,glacier,'geoid')

#################################
# Plot elevation along flowline #
#################################

if plot_overview:
  if glacier == 'Helheim':
    ind1 = np.where(time_dem[:,1] == 20130804)[0]
    ind2 = np.where(time_dem[:,1] == 20140127)[0]
  elif glacier == 'Kanger':
    ind1 = np.where(time_dem[:,1] == 20140628)[0]
    ind2 = np.where(time_dem[:,1] == 20141023)[0]

  # Get radar thicknesses close to flightline
  cresis = bedlib.cresis('all',glacier)
  if glacier == 'Helheim':
    cresis2001 = bedlib.cresis('2001',glacier)
    cresis = np.row_stack([cresis,cresis2001])

  cutoff = 200.
  dcresis = []
  zcresis = []
  tcresis = []
  for i in range(0,len(cresis[:,0])):
    mindist = np.min(np.sqrt((cresis[i,0]-x)**2+(cresis[i,1]-(y))**2))
    if mindist < cutoff:
      minind = np.argmin(np.sqrt((cresis[i,0]-x)**2+(cresis[i,1]-(y))**2))
      dcresis.append(dists[minind])
      zcresis.append(cresis[i,2])
      tcresis.append(cresis[i,4])
  dcresis = np.array(dcresis)
  zcresis = np.array(zcresis)

  fig = plt.figure(figsize=(4,3))
  gs = matplotlib.gridspec.GridSpec(2,1)
  matplotlib.rc('font',family='Arial')

  coloptions=['r','b','g','limegreen','gold']
 
  plt.subplot(gs[0])
  ax = plt.gca()
  plt.plot(dists/1e3,floatlib.height(zb),'k',linewidth=1.2,label='Flotation',dashes=[2,2,2,2])
  if glacier == 'Helheim':
    plt.plot(dists/1e3,atm_data['20010521'][:,2],'k',label='2001-05-21',lw=1.2)
  elif glacier == 'Kanger':
    plt.plot(dists/1e3,atm_data['20010520'][:,2],'k',label='2001-05-20',lw=1.2)
  plt.plot(dists/1e3,atm_data['20050518'][:,2],'0.8',label='2005-05-18',lw=1.2)
  date = str(int(time_dem[ind1,1]))
  plt.plot(dists/1e3,zs_dem[ind1,:].T,color='r',linewidth=1.2,label=date[0:4]+'-'+date[4:6]+'-'+date[6:])
  date = str(int(time_dem[ind2,1]))
  plt.plot(dists/1e3,zs_dem[ind2,:].T,color='b',linewidth=1.2,label=date[0:4]+'-'+date[4:6]+'-'+date[6:])
  plt.xticks(np.arange(-30,10,5),fontsize=8)
  ax.set_xticklabels([])
  plt.yticks(np.arange(-1000,1000,250),fontsize=8)
  plt.xlim([-21,6])
  if glacier == 'Helheim':
    plt.ylim([0,670])
    plt.text(-20,500,'b',fontsize=9,fontweight='bold')
  elif glacier == 'Kanger':
    plt.ylim([0,800])
    plt.text(-20,560,'b',fontsize=9,fontweight='bold')
  ax.xaxis.set_minor_locator(AutoMinorLocator(2))
  ax.yaxis.set_minor_locator(AutoMinorLocator(2))
  ax.tick_params('both', length=6, width=1.25, which='major')
  ax.tick_params('both', length=3, width=1, which='minor')
  plt.ylabel('Elevation (m asl)',fontsize=8)
  plt.legend(loc=1,fontsize=8,borderpad=0.2,numpoints=1,handlelength=0.6,labelspacing=0.1,handletextpad=0.3,markerscale=2)

  plt.subplot(gs[-1])
  ax = plt.gca()
  plt.plot(dcresis/1e3,zcresis,'.',c='0.7',markersize=2.5,label='CreSIS')
  if glacier == 'Helheim':
    plt.plot(dists/1e3,zb,color='k',linewidth=1.2,label='Bed')
  elif glacier == 'Kanger':
    ind = np.argmin(abs(dists--5e3))
    plt.plot(dists/1e3,zb,':',color='k',linewidth=1.5)
    plt.plot(dists[0:ind]/1e3,zb[0:ind],color='k',linewidth=1.5,label='Bed')
    plt.text(-3,-1050,'??',fontsize=8,fontname='arial')
    plt.text(3.2,-500,'??',fontsize=8,fontname='arial')
  plt.xlabel('Distance from mean terminus (km)',fontsize=8)
  plt.xticks(np.arange(-30,10,5),fontsize=8)
  plt.xlim([-21,6])
  plt.text(-20,-450,'c',fontsize=9,fontweight='bold')
  ax.xaxis.set_minor_locator(AutoMinorLocator(2))
  ax.yaxis.set_minor_locator(AutoMinorLocator(2))
  ax.tick_params('both', length=6, width=1.25, which='major')
  ax.tick_params('both', length=3, width=1, which='minor')
  plt.yticks(np.arange(-1250,-250,250),fontsize=8)
  plt.ylim([-1150,-300])
  plt.legend(loc=4,borderpad=0.2,fontsize=8,numpoints=1,handletextpad=0.3,handlelength=0.5,labelspacing=0.1,markerscale=2)

  # Save figure
  plt.tight_layout()
  plt.subplots_adjust(wspace=0.04,hspace=0.04)
  plt.savefig(os.path.join(os.getenv("HOME"),'Bigtmp/'+glacier+'_zs_flowline.pdf'),FORMAT='PDF',dpi=600)
  plt.close()


##########################################
# Plot elevation through time since 2000 #
##########################################

if plot_time:

  # Combine all elevation data into one data set
  all_time = np.r_[time_dem[:,0],time_atm]
  all_H = np.r_[zs_dem,zpt_atm]
  sortind = np.flipud(np.argsort(all_time))
  all_time = all_time[sortind]
  all_H = all_H[sortind]
  
  # Get colors
  cmapname = 'cpt_rainbow'
  cmap = plt.get_cmap(cmapname) 
  cNorm  = matplotlib.colors.Normalize(vmin=0, vmax=365)
  scalarMap = matplotlib.cm.ScalarMappable(norm=cNorm, cmap=cmap)
  
  years = range(2008,2016)
  gs = matplotlib.gridspec.GridSpec(2,4)
  fig = plt.figure(figsize=(7.5,4))
  
  filt_len=500.

  # Make plot
  im = plt.imshow(np.array([[0.,365.],[365,100.]]),cmap=cmap); plt.clf()
  for i in range(0,len(years)):
    
    plt.subplot(gs[i])
    ax = plt.gca()
    plt.plot(dists/1e3,floatlib.height(zb),'k:',lw=1.5)
    ind = np.where(np.floor(all_time)==years[i])[0]
    x_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
    for j in range(0,len(ind)):
      indterm = np.where(all_H[ind[j],:] < 10.)[0]
      zs_filt = np.zeros_like(dists)
      zs_filt[:] = float('nan')
      cutoff=(1/filt_len)/(1/((dists[1]-dists[0])*2))
      b,a=scipy.signal.butter(4,cutoff,btype='low')
      nonnan = np.where(~(np.isnan(all_H[ind[j],:])))[0]
      if len(nonnan) > 15.:
        zs_filt[nonnan] = scipy.signal.filtfilt(b,a,all_H[ind[j],nonnan])
        doy = int((all_time[ind[j]]-years[i])*365.)
        colorVal = scalarMap.to_rgba(doy)
        if len(indterm) > 0:
          plt.plot(dists[0:indterm[0]+1]/1e3,zs_filt[0:indterm[0]+1],c=colorVal,lw=1.5)
          plt.plot([dists[indterm[0]]/1e3,dists[indterm[0]]/1e3],[zs_filt[indterm[0]],0],c=colorVal,lw=1.5)
        else:
          plt.plot(dists/1e3,zs_filt,c=colorVal,lw=1.5)
    plt.xticks(np.arange(-10,10,2),fontsize=8)
    plt.yticks(np.arange(0,250,50),fontsize=8)
    if glacier == 'Helheim':
      plt.xlim([-4,2])
      plt.ylim([20,120])
      plt.text(-3.8,25,years[i],fontsize=9)
    elif glacier == 'Kanger':
      plt.xlim([-6,4])
      plt.ylim([20,150])
      plt.text(-5.7,30,years[i],fontsize=9)
    if i < 4:
      ax.set_xticklabels([])
    if (i == 0) or (i == 4):
      plt.ylabel('Elevation (m asl)',fontsize=8)
    else:
      ax.set_yticklabels([])

    plt.subplot(gs[0])
    colorbar_ax = fig.add_axes([0.14, 0.9, 0.15, 0.03])
    cb = plt.colorbar(im,cax=colorbar_ax,orientation='horizontal')
    colorbar_ax.set_xticks([])
    colorbar_ax.set_yticks([])
    cb.set_ticks(np.arange(0,400,100))
    cb.ax.tick_params(labelsize=8)
    cb.set_label('Day of year',fontsize=8)

  plt.tight_layout()
  plt.subplots_adjust(wspace=0.04,hspace=0.04)

  # Save figure
  plt.savefig(os.path.join(os.getenv("HOME"),'Bigtmp/'+glacier+'_zs_years.pdf'),FORMAT='PDF')
  plt.close()