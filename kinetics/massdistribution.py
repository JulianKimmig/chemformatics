import sys
import warnings
import numpy as np

def get_reactioncounts(reactionset,ppC=10**5,t=None):

    if reactionset.kinetic_solve is None:
        if t is not None:
            reactionset.solve_kinetics(time=t.max(),min_resolution=(np.diff(t).min() if t.size > 1 else np.inf))
        else:
            reactionset.solve_kinetics()



    diff_t = np.diff(reactionset.kinetic_solve.t)

    rxncounts=np.zeros((len(reactionset.kinetic_solve.t),len(reactionset.reactions),2))

    rxnrates=np.zeros((len(reactionset.kinetic_solve.t),len(reactionset.reactions),2))

    for i in range(len(reactionset.kinetic_solve.y[0])-1):
        reacts=dict(zip(reactionset.reacts, reactionset.kinetic_solve.y[0:,i]))
        rxnrates[i] = np.concatenate([r.get_rate(reacts) for r in reactionset.reactions]).reshape(-1,2)
        rxncounts[i]=rxnrates[i]*diff_t[i]*ppC

    rxncounts=rxncounts.transpose(1, 0, 2)
    rxnrates=rxnrates.transpose(1, 0, 2)

    for c in rxncounts:
        c[:-1]=c[:-1]+np.diff(c,axis=0)/2

    for c in rxnrates:
        c[:-1]=c[:-1]+np.diff(c,axis=0)/2

    rxncounts = rxncounts.astype(int)

    return rxncounts,rxnrates

def get_mass_distribution(reactionset,ppC=10**4,t=None,tmin=0,tstep=None):
    defaultt = 10
    defaultsteps=20
    particle_overhead=1.01

    if not isinstance(t,(list,np.ndarray)):
        try:
            t=float(t)
            t=np.arange(tmin,t,(tstep if tstep is not None else (t-tmin)/defaultsteps))
        except:
            if reactionset.kinetic_solve is not None:
                t = reactionset.kinetic_solve.t
            else:
                t=defaultt
                t=np.arange(tmin,t,(tstep if tstep is not None else (t-tmin)/defaultsteps))
    t=np.array(t)
    if t.size < 2:
        if t.size == 0:
            t=np.arange(0,defaultt,defaultsteps)
        else:
            if t[0] == 0:
                t=np.arange(0,defaultt,defaultsteps)
    t = np.unique(np.sort(t))

    if reactionset.kinetic_solve is None:
            reactionset.solve_kinetics(time=t.max(),min_resolution=(np.diff(t).min() if t.size > 1 else np.inf))

    rxncounts,rxnrates = get_reactioncounts(reactionset,ppC=ppC)
    particles_t=[]
    time_set=set([(np.abs(reactionset.kinetic_solve.t - i)).argmin() for i in t])
    maxc=max(*[r.c0 for r in reactionset.reacts])
    for i in range(len(reactionset.reacts)):
        reactionset.reacts[i].position = i

    particles=np.empty((len(reactionset.reacts),int(maxc*ppC*particle_overhead))) * np.nan
    for react in reactionset.reacts:
        particles[react.position][:react.c0*ppC] = react.mw
    trxn = rxncounts.transpose(1,0,2)
    isnan = None
    first_nans = None
    rxnrates.transpose(1,0,2)[:,:,0]+rxnrates.transpose(1,0,2)[:,:,1]
    randoms = None
    pcount=np.zeros((trxn.shape[0],trxn.shape[1]))
    print(trxn.shape)
    for timepoint in range(trxn.shape[0]):
        print(reactionset.kinetic_solve.t[timepoint],end=" ")
        sys.stdout.flush()
        for reactionpoint in range(trxn.shape[1]):
            reaction = reactionset.reactions[reactionpoint]
            for t in range(trxn[timepoint][reactionpoint][0]):
                isnan,first_nans,randoms = reaction.rxnfunc(particles,is_nan_array=isnan,first_nans=first_nans,randoms=randoms)
        pcount[timepoint] = first_nans
        if timepoint in time_set:
            particle_copy=np.copy(particles[:,~np.isnan(particles).all(axis=0)]).transpose()
            particles_t.append(particle_copy)

    print("done")
    return particles_t,pcount.transpose(),np.sort([reactionset.kinetic_solve.t[t] for t in time_set])


#
#
# def plot_data(data="rates",normed=False,fw=True,bw=True,start=-np.inf,end=np.inf,title=None,lables=None):
#     if polymerization.kinetic_solve is None:
#         polymerization.solve_kinetics()
#
#     if polymerization.kinetic_solve.t[0]>=start:
#         index_start = 0
#     else:
#         index_start=np.argmax(polymerization.kinetic_solve.t>=start)
#
#     if polymerization.kinetic_solve.t[-1]<end:
#         index_end = len(polymerization.kinetic_solve.t)
#     else:
#         index_end=np.argmax(polymerization.kinetic_solve.t>end)
#
#     data_array=None
#     if data=="rates":
#         if fw and bw:
#             data_array = np.append(polymerization.rxnrates[:,index_start:index_end,0],polymerization.rxnrates[:,index_start:index_end,1]).reshape(polymerization.rxnrates[:,index_start:index_end,:].shape[0]*2,polymerization.rxnrates[:,index_start:index_end,:].shape[1])
#         elif fw:
#             data_array = polymerization.rxnrates[:,index_start:index_end,0]
#         elif bw:
#             data_array = polymerization.rxnrates[:,index_start:index_end,1]
#         if title is None:
#             title = "reaction rates"+(" (normed)" if normed else "")
#         if lables is None:
#             lables = ([str(r)+"_fwd" for r in polymerization.reactions] if fw else [])+([str(r)+"_bwd" for r in polymerization.reactions] if bw else [])
#     if data=="kinetics":
#         data_array=self.kinetic_solve.y
#     q<
#     else:
#     warnings.warn("invalid data, chooose: "+"rates, kinetics")
#     return
# if data_array is None:
#     warnings.warn("no data")
#     return
#
# plot(polymerization.kinetic_solve.t[index_start:index_end],data_array, title=title,norm=normed,labels=lables)
#
#
#
# get_mass_distribution()
# plot_data(data="kinetics",end=7,normed=True,bw=False)
# plot_data(data="rates",end=7,normed=True,bw=False)