'''

The following functions help convert different time formats to 
fractional year (and then back again).

LMK, UW, 16 July 2015

'''

import jdcal
import numpy as np

def date_to_fracyear(year,month,day):
  
  try:
    # If we have multiple dates
    N = len(year)
    
    fracyear = np.zeros(N)
  
    for i in range(0,N):
      day0 = jdcal.gcal2jd(year[i],month[i],day[i])
      day2 = jdcal.gcal2jd(year[i]+1,1,1)
      day1 = jdcal.gcal2jd(year[i],1,1)
      doy = day0[1]+day0[0]-day1[1]-day1[0]
  
      fracyear[i] = year[i] + doy/(day2[1]+day2[0]-day1[0]-day1[1])
    
  except:
    # If we only have one date

    N = 1
  
    day0 = jdcal.gcal2jd(year,month,day)
    day2 = jdcal.gcal2jd(year+1,1,1)
    day1 = jdcal.gcal2jd(year,1,1)
    doy = day0[1]+day0[0]-day1[1]-day1[0]
  
    fracyear = year + doy/(day2[1]+day2[0]-day1[0]-day1[1])

  return fracyear
  
def doy_to_fracyear(year,doy):

  day1 = jdcal.gcal2jd(year,1,1) # Get length of year
  day2 = jdcal.gcal2jd(year+1,1,1)

  fracyear = year + (doy-1)/(day2[1]+day2[0]-day1[0]-day1[1])

  return fracyear

def fracyear_to_date(input):
  
  try:
    # Check to see if input is array. If it is, iterate through array.
    N = len(input)
    year = np.zeros(N)
    month = np.zeros(N)
    day = np.zeros(N)
    for i in range(0,N):
      year[i] = np.floor(input[i])
  
      day1 = jdcal.gcal2jd(year[i],1,1) # Get length of year
      day2 = jdcal.gcal2jd(year[i]+1,1,1)
      dayfrac[i] = (input[i]-year[i])*float(day2[1]+day2[0]-day1[0]-day1[1])

      year[i],month[i],day[i],frac = jdcal.jd2gcal(day1[0]+day1[1],dayfrac[i])

      day[i] = day[i]+frac
  except:
    # If input has no length (i.e., it's a float), then just calculate 
    # the date for that number.
    year = np.floor(input)
    day1 = jdcal.gcal2jd(year,1,1) # Get length of year
    day2 = jdcal.gcal2jd(year+1,1,1)
  
    dayfrac = (input-year)*float(day2[1]+day2[0]-day1[0]-day1[1])

    year,month,day,frac = jdcal.jd2gcal(day1[0]+day1[1],dayfrac)

    day = day+frac

  return year,month,day
  
def fracyear_to_doy(input):

  year = np.floor(input)
  
  day1 = jdcal.gcal2jd(year,1,1) # Get length of year
  day2 = jdcal.gcal2jd(year+1,1,1)
  
  doy = (input-year)*float(day2[1]+day2[0]-day1[0]-day1[1])+1

  return year,doy

def date_to_doy(year,month,day):

  day0 = jdcal.gcal2jd(year,month,day)
  day2 = jdcal.gcal2jd(year+1,1,1)
  day1 = jdcal.gcal2jd(year,1,1)
  doy = day0[1]+day0[0]-day1[1]-day1[0]+1
  
  return year,doy

def doy_to_date(year,doy):
  
  frac = doy_to_fracyear(year,doy)
  
  year,month,day = fracyear_to_date(frac)
  
  return year,month,day

def month(string):
  # Return number of month given the first three letters of the month

  if string == 'Jan':
    num = 1
  elif string == 'Feb':
    num = 2
  elif string == 'Mar':
    num = 3
  elif string == 'Apr':
    num = 4
  elif string == 'May':
    num = 5
  elif string == 'Jun':
    num = 6
  elif string == 'Jul':
    num = 7
  elif string == 'Aug':
    num = 8
  elif string == 'Sep':
    num = 9
  elif string == 'Oct':
    num = 10
  elif string == 'Nov':
    num = 11
  elif string == 'Dec':
    num = 12

  return num
  
def month_to_string(num):

# Return string of month for number

  if num == 1:
    string = 'Jan'
  elif num == 2:
    string = 'Feb'
  elif num == 3:
    string = 'Mar'
  elif num == 4:
    string = 'Apr'
  elif num == 5:
    string = 'May'
  elif num == 6:
    string = 'Jun'
  elif num == 7:
    string = 'Jul'
  elif num == 8:
    string = 'Aug'
  elif num == 9:
    string = 'Sep'
  elif num == 10:
    string = 'Oct'
  elif num == 11:
    string = 'Nov'
  elif num == 12:
    string = 'Dec'
    
  return string

def yearlength(year):
  '''
  Return number of days for year (depending on whether or not it is a leap year)
  '''
  
  day1 = jdcal.gcal2jd(year,1,1) # Get length of year
  day2 = jdcal.gcal2jd(year+1,1,1)
  
  days = day2[1]-day1[1]
  
  return days

def monthly_stats(time,variable):
  '''
  Get average monthly values for variable
  '''

  month = range(1,14)
  averages = np.zeros(12)
  samples = np.zeros(12)
  std = np.zeros(12)
  for j in range(1,len(month)):
    values = []
    n = 0
    for i in range(0,len(time)):
      if (time[i] >= date_to_fracyear(np.floor(time[i]),month[j-1],1)) and (time[i] < date_to_fracyear(np.floor(time[i]),month[j],1)):
        values.append(variable[i])
        n = n+1
    averages[j-1] = np.sum(values)/n
    std[j-1] = np.std(values)
    samples[j-1] = n
    
  return range(1,13),averages,std,samples