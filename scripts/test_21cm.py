#Compare calculation of 21cmFAST cube pspec to its calculated pspec.

from eorsky import box_dft_pspec
import pylab as p
import numpy as np
pi = np.pi

ref_file = "../eorsky/data/pspec_21cmFAST_z008.00.dat"
dat_file = "../eorsky/data/21cmFAST_z008.00_256_300Mpc"
L = 300.   #Mpc
N = 256    #Pixels

dat = np.fromfile(dat_file,dtype=np.float32).reshape((N,N,N))
dat -= np.mean(dat)

r_mpc = np.linspace(0,300,N)    # Test the DFT mode.
ks, pk = box_dft_pspec(dat,L, r_mpc = r_mpc, cosmo=True)
pk *= (ks**3/2*np.pi**2)


#Nz = N
#dz = L/float(N)
#kfact = 2*np.pi
#kz = np.fft.fftfreq(Nz,d=dz)*kfact   #Mpc^-1

ref_spectrum = np.genfromtxt(ref_file)
ref_ks = ref_spectrum[:,0]
ref_pk = ref_spectrum[:,1]

p.plot(ks, pk/float(len(ks)),marker='.',label='Meas')
p.plot(ref_ks,ref_pk,marker='.',label="Ref")
p.yscale('log'); p.xscale('log')
p.xlabel(r"k [Mpc$^{-1}$]")
p.ylabel(r"$\Delta(k)$ [mK$^2$]")
p.legend()
p.show()
