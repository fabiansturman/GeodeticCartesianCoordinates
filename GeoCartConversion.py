# -*- coding: utf-8 -*-
"""
This code provides functionality for conversion between cartesian coordinates and geodetic coordinates. It is a python implementation of the algorithm proposed by Ligas and Banasik [1].

The methodology descibed in their paper is replicated here, with their application of Newton's Rule replaced with a more generic function; I use scipy.optimize.root with several potentail root-finding algorithms, including Broyden's method.

The calculation of lat-long-height coordinates from cartestians is split into 3 steps:
1.	Take a cartesian point and find the longitude of this point using the closed form equation provided above (arctan(Y/X))
2.	Project the cartesian point onto the surface of the ellipsoid (as in [1], Figure 2)
3.	Calculate the latitude and height of the projected point, and use this to calculate the geodetic coordinates of the original cartesian point.

By default, this code uses WGS 84 to model the Earth, howeever these optional parameters can be overriden.



[1] Ligas, Marcin & Banasik, Piotr. (2011). Conversion between Cartesian and geodetic coordinates on a rotational ellipsoid by solving a system of nonlinear equations. Geodesy and Cartography. 60. 145-159. 10.2478/v10277-012-0013-x.
"""

import numpy as np
from scipy import optimize

#This function calculates (phi, h)
def step3(H, p_E, z_E, p_G,z_G):
  tan_phi = H*H*z_E / p_E
  phi = np.arctan(tan_phi) * (180/np.pi)
  h = np.sqrt(np.square(p_E -p_G) + np.square(z_E - z_G))
  if p_G + np.abs(z_G) < p_E + np.abs(z_E):
    h = -h
  return [phi,h]

def xyzllh(x,y,z,a=6378,b=6356, trace = False, method = 'broyden1'):
  """
  Converts from xyz coordinates to geodetic coordinates. Uses WGS 84 by default for a, b.
  Args:
    x,y,z: Cartesian input coordinates (km)
    a,b: Defines the elipse with respect to which the geodetic coordinates will lie.
    trace: We output the geodetic coordinate estimate at each stage of the iteration iff trace
    method: Optimisation algorithm we are using. See documentation for scipy.optimize.root

  Returns:
    (phi, lambda, h, iterations): 4-tuple of the geodetic coordinates (latitude, longitude, height) and #iterations needed to converge

  Angles are in degrees, distances are in km.
  """
  global iters;   iters = 0

  ##Step 1: find lambda using the standard closed form method
  lambda_1 = np.arctan(y/x) * (180/np.pi)

  w = np.sqrt(x*x + y*y)
  lambda_2 = 2 * np.arctan(y/(x+w))  * (180/np.pi)
    #lambda_1 is calculated more directly but this is less numerically stable than lambda_2 (Claesenns, 2019).
    #Ignoring numerical stability, we can expect lambda_1 == lambda_2
  if trace:
    print(f"Lambda calucalted directly = {lambda_1} , lambda calculated with numerical stability = {lambda_2}")


  ##Step 2a: Project (x,y,z) onto (p_G,z); as Step 2 can be completed in 2 dimensions
  p_G = np.sqrt(x*x + y*y)
  z_G = z

  ##Step 2b: Solve for (p_E, z_E). We use scipy's implementation of the Newton method.
  G = b/a ; H = a/b ; K=a*b

    #Function of which to find the root
  def fun(x):
    pe = x[0];ze = x[1]; s3 = step3(H, pe, ze, p_G, z_G)
    global iters; iters = iters+1
    if trace:
      print(f"TRACE: Current geodetic coordindates: (lat, long, height) = ({s3[0]}, {lambda_2}, {s3[1]})")
    return [(pe - p_G)*H*ze - (ze - z_G) * G * pe,
             G* pe*pe + H * ze*ze - K]

    #Jacobian of f. Not used for all optimisation methods (e.g. broyden approximates jacobian itself)
  def jac(x):
    pe = x[0];ze = x[1]
    return np.array([[H*ze - (ze-z_G) * G, (pe-p_G) * H - G*pe],
                     [2* G * pe          , 2 * H * ze         ]])

    #Starting point for applying iterative method
  r = 1/np.sqrt(p_G*p_G + z_G*z_G)
  p_start = a * p_G * r
  z_start = b * z_G * r

  root = optimize.root(fun, [p_start, z_start], jac=jac, method=method).x
  print(root)
  ##Step 3: Convert to, print, and return, geodetic coordinates
  toret = step3(H, root[0], root[1], p_G, z_G)

  if trace:
    print(f"\nFinal geodetic coordinates = {(toret[0], lambda_2, toret[1])}")
    print(f"lambda_1 = {lambda_1}")
    print(f"{iters} iterations until convergence")

  return (toret[0], lambda_2, toret[1], iters)


def llhxyz(lat, long, h, a=6378,b=6356):
  #Input/Output: All angles in degrees, all distances in km

  lat *= np.pi/180; long *= np.pi/180 #Convert to radians

  e_2 = 1-np.square(b/a) #first eccentricity squared
  N = a/np.sqrt(1 - e_2 * np.square(np.sin(lat))) #Radius of curvature in the prime vertical

  x = (N+h) * np.cos(lat) * np.cos(long)
  y = (N+h) * np.cos(lat) * np.sin(long)
  z = ((1-e_2)*N + h) * np.sin(lat)

  return (x,y,z)



def tester(trace = False):
  latitude = float(input("Enter latitude: "))
  longitude = float(input("Enter longitude: "))
  height = float(input("Enter height: "))

  (x,y,z) = llhxyz(latitude, longitude, height)
  (la, lo, h, iterations) = xyzllh(x,y,z, trace = trace)

  print()
  print("RESULTS:")
  print(f"Entered (lat, long, h) = {(latitude, longitude, height)}")
  print(f"Equivalent (x,y,z) = {(x,y,z)}")
  print(f"Converting these cartesian coords back to geodetic coords: {(la, lo, h)}")
  print(f"Numerical root finding took {iterations} iterations")
  print()

tester()
