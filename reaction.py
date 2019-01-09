from  random import randint 
import numpy as np
from scipy.integrate import solve_ivp as solver
from sympy import Symbol,init_printing,Eq,Add,pprint as sympprint
from massplotter import mass_plot as mplot
init_printing()

class Reagent():
    def __init__(self,mw,name="Reagent"+str(randint(1,10**6)),c0=0):
        self.mw = mw
        self.name = name
        self.c0 = c0
    
    def __str__(self):
        return self.name
    __repr__ = __str__
    

class Reaction():
    def __init__(self,educts,products,name="Reaction"+str(randint(1,10**6)),k1=1,k2=0,rxnfunc=None):
        self.educts=educts
        self.products = products
        self.k2=k2
        self.k1=k1
        self.name = name
        if rxnfunc is None:
            rxnfunc = self._default_rxnfunc
        self.rxnfunc=rxnfunc
    
    def _default_rxnfunc(self,particles,is_nan_array=None,first_nans=None,randoms=None):
        if is_nan_array is None:
            is_nan_array=np.isnan(particles) 
            first_nans = np.argmax(is_nan_array,1)
        if first_nans is None:    
            first_nans = np.argmax(is_nan_array,1) 
            
        for n,r in self.educts:
            if n > 0:
                fnp=first_nans[r.position]
                if (fnp-n)<0:
                    return is_nan_array,first_nans, randoms
                particles[r.position][fnp-n:fnp]=np.nan
                is_nan_array[r.position][fnp-n:fnp]=True
                first_nans[r.position] -= n
                
        for n,r in self.products:
            if n > 0:
                fnp=first_nans[r.position]
                particles[r.position][fnp:fnp+n]=r.mw
                is_nan_array[r.position][fnp:fnp+n]=False
                first_nans[r.position] += n
        
        return is_nan_array,first_nans,randoms

    
    def reaction_string(self):
        s= " + ".join([(str(n)+" " if n > 1 else "")+(r.name)  for n,r in self.educts]) +\
        " "+("<" if self.k2 > 0 else "") +"--> " +\
        " + ".join([(str(n)+" " if n > 1 else "")+(r.name)  for n,r in self.products]) +\
         " ("+str(self.k1) + (","+str(self.k2) if self.k2>0 else "")+")"
        return s
    
    def __str__(self):
        return self.name
    
    
    def get_diff_functions_str(self,k_as_number=False):
        eqs={}
        for n,r in self.educts:
            f =  -n*(self.k1 if k_as_number else Symbol("k_1"+self.name))
            for ns,rs in self.educts:
                f=f*Symbol("["+str(rs)+"]")**ns
            eqs[r] =  eqs.get(r,[])+[f]
            
            f =  n*(self.k2 if k_as_number else Symbol("k_2"+self.name))
            for ns,rs in self.products:
                f=f*Symbol("["+str(rs)+"]")**ns
            eqs[r] =  eqs.get(r,[])+[f]
            
        for n,r in self.products:
            f =  n*(self.k1 if k_as_number else Symbol("k_1"+self.name))
            for ns,rs in self.educts:
                f=f*Symbol("["+str(rs)+"]")**ns
            eqs[r] =  eqs.get(r,[])+[f]
            
            f = -n*(self.k2 if k_as_number else Symbol("k_2"+self.name))
            for ns,rs in self.products:
                f=f*Symbol("["+str(rs)+"]")**ns
            eqs[r] =  eqs.get(r,[])+[f]
                        
        return eqs
    
    def _create_sub_diff(self,n,r,ed=True):
        fac1 = n*self.k1
        fac2 = -n*self.k2
        if ed:
            fac1 = - fac1
            fac2 = - fac2
            
        def f(cs,react_dic):
                b1 = b2 = 0
                if fac1 != 0:
                    b1 =  fac1
                    for ns,rs in self.educts:
                        b1 =b1 * cs[react_dic[rs]]**ns
                if fac2 != 0:
                    b2 =  fac2
                    for ns,rs in self.products:
                        b2 =b2 * cs[react_dic[rs]]**ns
                return b1+b2
            
        return f
        
    def get_diff_functions(self):
        eqs={}
        for n,r in self.educts:
            f = self._create_sub_diff(n,r,True)
            eqs[r] =  eqs.get(r,[])+[f]
          
        for n,r in self.products:
            f = self._create_sub_diff(n,r,False)
            eqs[r] =  eqs.get(r,[])+[f]
                        
        return eqs
    
    def get_rate(self,reacts):
        rate1=self.k1
        if rate1 != 0:
            for n,r in self.educts:
                rate1=rate1*reacts[r]**n
        
        rate2 = -self.k2
        if rate2 != 0:
            for n,r in self.products:
                rate2=rate2*reacts[r]**n
                
        return np.array([rate1,rate2])

class ReactionSet():
    def __init__(self,reactions):
        self.reactions = reactions
        self.prepared = False
        self.reacts_ord={}
        self.reacts = []
        self.c0s = []
        self.diff_eq = []
        self.diff_eq_str = []
        self.kinetic_solve = None
        
    def print_diff_equations(self,k_as_number=False):
        deqs={}
        r:Reaction
        for r in self.reactions:
            for reagent,subequations in r.get_diff_functions_str(k_as_number=k_as_number).items():
                deqs[reagent] = deqs.get(reagent,[]) + subequations
        
        dt_sym = Symbol("dt")
        for reac,eqs in deqs.items():
            e=Eq(Symbol("d["+str(reac)+"]")/dt_sym,Add(*eqs))
            try:
                display(e)
            except:
                sympprint(e)
            
        
        
        
    def __str__(self):
        return "\n".join([str(reaction)+": "+reaction.reaction_string() for reaction in self.reactions])
            
    
    def prepare(self):
        self.reacts_ord={}
        for rxn in self.reactions:
            for n,reac in (rxn.educts + rxn.products):
                if reac not in self.reacts_ord:
                    self.reacts_ord[reac] = len(self.reacts_ord)
        self.reacts = [None for i in self.reacts_ord]
        
        for r,p in self.reacts_ord.items():
            self.reacts[p]=r
        
        self.c0s = [r.c0 for r in self.reacts]

        self.diff_eq = [[] for r in self.reacts]
        self.rxn_functions = []
        self.diff_eq_str = [[] for r in self.reacts]

        for rxn in self.reactions:
            self.rxn_functions.append(rxn.rxnfunc)
            for reac,funcs in rxn.get_diff_functions().items():
                self.diff_eq[self.reacts_ord[reac]].extend(funcs)
            for reac,funcs in rxn.get_diff_functions_str().items():
                self.diff_eq_str[self.reacts_ord[reac]].extend(funcs)
        self.prepared=True

    def solve_kinetics(self,time=10,min_resolution=np.inf):
        if self.prepared==False:
            self.prepare()
        self.tp = 0
        def da(t,c):
            self.tp=t
            rates=[0 for i in self.reacts]
            for i in range(len(self.reacts)):
                rates[i] = rates[i] + sum([eq(c,self.reacts_ord) for eq in self.diff_eq[i]]) 
            return rates
        self.kinetic_solve = solver(da,(0,time),self.c0s,max_step=min_resolution)
        return self.kinetic_solve
    
    def plot_kinetics(self,add_normed=False):
        if self.kinetic_solve is None:
            self.solve_kinetics()
        mplot(self.kinetic_solve.t,self.kinetic_solve.y, title="kinetic",labels=self.reacts)
        if add_normed:
            mplot(self.kinetic_solve.t,self.kinetic_solve.y, title="kinetic normed",norm=True,labels=self.reacts)
