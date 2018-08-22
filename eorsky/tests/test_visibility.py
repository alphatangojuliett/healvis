from eorsky import pspec_funcs, comoving_voxel_volume, comoving_radial_length, comoving_transverse_length
from eorsky import visibility
from astropy.cosmology import WMAP9
import nose.tools as nt
import numpy as np
import healpy as hp

# HERA site
latitude  = -30.7215277777
longitude =  21.4283055554

def test_pointings():
    t0 = 2451545.0      #Start at J2000 epoch
    dt_min = 20.0
    dt_days = dt_min * 1/60. * 1/24.  # 20 minutes in days

    time_arr = np.arange(20) * dt_days + t0
    obs = visibility.observatory(latitude, longitude)

    obs.set_pointings(time_arr)

    ras = np.array([ c[0] for c in obs.pointing_centers ])
    decs = np.array([ c[1] for c in obs.pointing_centers ])
    ind = np.where(np.diff(ras)<0)[0][0]
    ras[ind+1:] += 360.   # Deal with 360 degree wrap
    
    dts = np.diff(ras)/15.04106 * 60.
    nt.assert_true(np.allclose(dts, dt_min, atol=1e-1))   #Within 6 seconds. Not great...
    nt.assert_true(np.allclose(decs, latitude, atol=1e-1))   # Close enough for my purposes, for now.

def test_az_za():
    """
    Check the calculated azimuth and zenith angle of a point exactly 5 deg east on the sphere (az = 90d, za = 5d)
    """
    Nside=128
    obs = visibility.observatory(latitude, longitude)
    center = [0, 0]
    lon, lat = [5,0]
    ind0 = hp.ang2pix(Nside, lon, lat, lonlat=True)
    lon, lat = hp.pix2ang(Nside, ind0, lonlat=True)
    cvec = hp.ang2vec(center[0],center[1], lonlat=True)
    radius = np.radians(10.)
    obs.set_fov(20)
    pix = hp.query_disc(Nside, cvec, radius)
    za, az = obs.calc_azza(Nside, center)
    ind = np.where(pix == ind0)
    print(np.degrees(za[ind]), np.degrees(az[ind]))
    print(lon, lat)
    nt.assert_true(np.isclose(np.degrees(za[ind]), lon))
    nt.assert_true(np.isclose(np.degrees(az[ind]), lat + 90))

def test_vis_calc():
    # Construct a shell with a single point source at the zenith and confirm against analytic calculation.

    ant1_enu = np.array([0, 0, 0])
    ant2_enu = np.array([0.0, 14.6, 0])
    
    bl = visibility.baseline(ant1_enu, ant2_enu)

    freqs = np.array([1e8])
    nfreqs = 1

    fov=20  #Deg

    ## Longitude/Latitude in degrees.

    nside=128
    ind = 10
    center = list(hp.pix2ang(nside, ind, lonlat=True))
    centers = [center]
    npix = nside**2 * 12
    shell = np.zeros((npix, nfreqs))
#    ind = hp.ang2pix(nside, centers[0][0], centers[0][1], lonlat=True)
    shell[ind] = 1
#    import IPython; IPython.embed()

    obs = visibility.observatory(latitude, longitude, array=[bl], freqs=freqs)
    obs.pointing_centers = centers
    obs.set_fov(fov)
#    resol = np.sqrt(4*np.pi/float(npix))
    obs.set_beam('uniform')

    visibs = obs.make_visibilities(shell)
    print visibs

    nt.assert_true(np.real(visibs) == 1.0)   #Unit point source at zenith

def test_offzenith_vis():
    # Construct a shell with a single point source a known position off from zenith.
    #   Similar to test_vis_calc, but set the pointing center 5deg off from the zenith and adjust analytic calculation

    Nside = 64 
    freqs = [1.0e8]
    Nfreqs = 1
    fov = 60
    ##    hp.ang2pix(nside, azimuth, latitude, lonlat=True)
    ## OR hp.ang2pix(nside, colatitude, azimuth)
    ##    theta = latitude in degrees
    ##    phi   = azimuth in degrees
    ant1_enu = np.array([0, 0, 0])
    ant2_enu = np.array([0.0, 140.6, 0])
    
    bl = visibility.baseline(ant1_enu, ant2_enu)

    # Theta = angle above equator (latitude), phi = azimuth wrt vernal equinox at J2000 epoch
    # Pointing center = (azimuth, latitude) =  (phi, theta)

    ## Rewrite --- Choose pointing center. Place point source relative to it. Get lmn from that directly.
    ##  
    Nside=128
    ind = 9081
    center = list(hp.pix2ang(Nside, ind, lonlat=True))
    centers = [center]
    Npix = Nside**2 * 12
    shell = np.zeros((Npix, Nfreqs))

    # Choose an index 5 degrees off from the pointing center
    phi, theta = hp.pix2ang(Nside, ind, lonlat=True)
    ind = hp.ang2pix(Nside, phi, theta-5, lonlat=True)
    shell[ind] = 1

    import IPython; IPython.embed()
    obs = visibility.observatory(latitude, longitude, array=[bl], freqs=freqs)
    obs.pointing_centers = [[phi, theta]]
    obs.set_fov(fov)
    resol = np.sqrt(4*np.pi/float(Npix))
    obs.set_beam('uniform')

    vis_calc = obs.make_visibilities(shell)

    src_az, src_za = np.radians(phi), np.radians(90-theta)
#    c = obs.pointing_centers[0]
#    src_za -= np.radians(c[1])
    src_l = np.sin(src_az) * np.sin(src_za)
    src_m = np.cos(src_az) * np.sin(src_za)
    src_n = np.cos(src_za)
    print 'Analytic lmn: ', src_l, src_m, src_n 
#    import IPython; IPython.embed()
    u, v, w = bl.get_uvw(freqs[0])

    vis_analytic = (1) * np.exp(2j * np.pi * (u*src_l + v*src_m + w*src_n))
    
    ## Verify that az/za of the projected pixels are within resol of phi/theta
#    ogrid = pspec_funcs.orthoslant_project(shell, obs.pointing_centers[0], fov, degrees=True)
#    xind,yind, _ = np.where(ogrid > 0)
#    xi,yi = xind[0], yind[0]
#    print("Src az_za, deg, gridded: ", obs.az_arr[xi,yi]*180/np.pi, obs.za_arr[xi,yi]*180/np.pi)
#    print("Src az_za, deg, healpix: ", phi, theta)
#    import IPython; IPython.embed()

    print(vis_analytic)
    print(vis_calc)

    nt.assert_true(np.isclose(vis_analytic, vis_calc, atol=1e-5))


if __name__ == '__main__':
    #test_offzenith_vis()
    test_vis_calc()
    #test_az_za()

#!!! More tests:
#        Confirm the az_za calculation makes sense
#        Confirm that the angular distance between two point sources is conserved by the orthoslant_project
#        Look at how projection affects a diffuse gradient.


# scripts:
#   Script to calculate visibilities from a gaussian sky given gaussian beams of different widths. --- Confirm the relationship between beam width and covariance matrices
#   !Covariance per freq wrt an ensemble of gaussian skies with 24 hours -- (more demanding; may need mpi)
#   Get overlap between fields of view and primary beams for different centers --- how does that relate with correlation?
#   Look at effect of resolution and time cadence, with varying beam width
#   Covariance binning of random visibilities

