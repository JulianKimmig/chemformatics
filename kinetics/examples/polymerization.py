from scipy import interpolate

import reaction as rxn
import numpy as np
from  functools import partial
import matplotlib.pyplot as plt
import  kinetics.massdistribution as md
from mpl_toolkits import mplot3d
#Reagents
from massplotter import mass_plot

ini = rxn.Reagent(160,"Ini",1)
inirad = rxn.Reagent(ini.mw/2,ini.name+"*",0)
mono = rxn.Reagent(100.12,"M",100)

poly = rxn.Reagent(0,"P",0)
polyrad = rxn.Reagent(poly.mw,poly.name+"*",0)


def growfunc(particles,ed1,ed2,pd1,is_nan_array=None,first_nans=None,randoms=None):

    if is_nan_array is None:
        is_nan_array=np.isnan(particles)
        first_nans = np.argmax(is_nan_array,1)
    if first_nans is None:
        first_nans = np.argmax(is_nan_array,1)

    if randoms is None or randoms.size<10:
        randoms = np.random.rand(10**4)
    first_nan_1=first_nans[ed1.position]#


    if first_nan_1 == 0:
        if is_nan_array[ed1.position][-1]:
            return is_nan_array,first_nans,randoms
        first_nan_1 = is_nan_array.shape[1]

    ran,randoms=randoms[-1],randoms[:-1]
    i1 = int(first_nan_1 * ran)
    particles[ed1.position][i1],particles[ed1.position][first_nan_1-1] = particles[ed1.position][first_nan_1-1],particles[ed1.position][i1]
    mw1 = particles[ed1.position][first_nan_1-1]

    particles[ed1.position][first_nan_1-1] = np.nan
    is_nan_array[ed1.position][first_nan_1-1] = True
    first_nans[ed1.position] -= 1 #

    first_nan_2=first_nans[ed2.position]#

    if first_nan_2 == 0:
        if is_nan_array[ed2.position][-1]:
            particles[ed1.position][first_nan_1-1] = mw1
            is_nan_array[ed1.position][first_nan_1-1]=False
            first_nans[ed1.position] += 1
            return is_nan_array,first_nans,randoms
        first_nan_2 = is_nan_array.shape[1]

    ran,randoms=randoms[-1],randoms[:-1]
    i2 = int(first_nan_2 * ran)
    particles[ed2.position][i2],particles[ed2.position][first_nan_2-1] = particles[ed2.position][first_nan_2-1],particles[ed2.position][i2]
    mw2 = particles[ed2.position][first_nan_2-1]

    particles[ed2.position][first_nan_2-1] = np.nan
    is_nan_array[ed2.position][first_nan_2-1] = True
    first_nans[ed2.position] -= 1

    first_nan_3=first_nans[pd1.position]

    particles[pd1.position][first_nan_3] = mw1+mw2
    is_nan_array[pd1.position][first_nan_3] = False
    first_nans[pd1.position] += 1

    return is_nan_array,first_nans,randoms


ini_deg = rxn.Reaction([(1,ini)],[(2,inirad)],k1=1,k2=1,name="inideg")
initiation = rxn.Reaction([(1,inirad),(1,mono)],[(1,polyrad)],k1=0.8,name="ini",rxnfunc=partial(growfunc,ed1=inirad,ed2=mono,pd1=polyrad))
grow = rxn.Reaction([(1,polyrad),(1,mono)],[(1,polyrad),],k1=0.5,name="grow",rxnfunc=partial(growfunc,ed1=polyrad,ed2=mono,pd1=polyrad))
exit1= rxn.Reaction([(2,polyrad)],[(1,poly)],k1=0.2,name="ex1",rxnfunc=partial(growfunc,ed1=polyrad,ed2=polyrad,pd1=poly))
exit2= rxn.Reaction([(1,polyrad),(1,inirad)],[(1,poly)],name="ex2",k1=0.2,rxnfunc=partial(growfunc,ed1=polyrad,ed2=inirad,pd1=polyrad))

#create reaction set
polymerization = rxn.ReactionSet([ini_deg,initiation,grow,exit1,exit2])
print(polymerization)

#get diff equations
polymerization.print_diff_equations(k_as_number=True)

#solve kinetics
polymerization.solve_kinetics(time=20,min_resolution=0.01)


#plotted kinetics
polymerization.plot_kinetics()
polymerization.plot_kinetics(normed=True)

rxncounts,rxnrates = md.get_reactioncounts(polymerization,ppC=10**5)

rxnlabels=[str(r)+"_fwd" for r in polymerization.reactions]+[str(r)+"_bwd" for r in polymerization.reactions]


mass_plot(polymerization.kinetic_solve.t,np.append(rxnrates[:,:,0],rxnrates[:,:,1],axis=0), title="reaction rates",norm=True,labels=rxnlabels,hidezeros=True)
mass_plot(polymerization.kinetic_solve.t,np.append(rxncounts[:,:,0],rxncounts[:,:,1],axis=0), title="reaction counts",norm=True,labels=rxnlabels,hidezeros=True)

a,b,mt = md.get_mass_distribution(polymerization)

def plot_timep(reac_pos,t,res=40):
    global a,mt
    ti=np.abs(mt - t).argmin()
    c=(np.sort(a[ti][:,reac_pos][~np.isnan(a[ti][:,reac_pos])])/res).astype(int)*res
    unique, counts = np.unique(c, return_counts=True)

    mn=sum(unique*counts)/sum(counts)
    mw=sum(unique*counts*unique)/sum(unique*counts)
    d=mw/mn
    print(int(mw),int(mn),d)

    plt.plot(unique[:],counts[:])
    plt.axvline(x=mn)
    plt.axvline(x=mw)
    plt.show()

plot_timep(poly.position,10,mono.mw)

def plot3d(reac_pos,res=40):
    c=[(np.sort(ti[:,reac_pos][~np.isnan(ti[:,reac_pos])])/res).astype(int)*res for ti in a]
    unique_counts = []
    for i in range(len(c)):
        unique, counts = np.unique(c[i], return_counts=True)
        for j in range(unique.size):
            unique_counts.append((unique[j],mt[i],counts[j]))
    unique_counts = np.array(unique_counts)
    max_values = np.amax(unique_counts, axis=0)
    min_values = np.amin(unique_counts, axis=0)
    xy_size = max_values - min_values
    t_x, t_y = np.meshgrid(
        np.linspace(
            min_values[0], max_values[0], xy_size[0]/res
        ),
        np.linspace(
            min_values[1], max_values[1],xy_size[1]*10
        ),
    )
    t_z = interpolate.griddata(
        unique_counts[:, :2], unique_counts[:, 2], (t_x, t_y), method="linear"
    )
    mask = np.all(np.isnan(t_z), axis=1)
    t_x = t_x[~mask]
    t_y = t_y[~mask]
    t_z = t_z[~mask]
    mask = np.all(np.isnan(t_z), axis=0)
    X = t_x.transpose()[~mask].transpose()
    Y = t_y.transpose()[~mask].transpose()
    Z = t_z.transpose()[~mask].transpose()
    Z[np.isnan(Z)]=0
#mass_plot(polymerization.kinetic_solve.t,rxnrates[::][0])
#mass_plot(polymerization.kinetic_solve.t,rxncounts[::][1])
#mass_plot(polymerization.kinetic_solve.t,rxnrates[::][1])





