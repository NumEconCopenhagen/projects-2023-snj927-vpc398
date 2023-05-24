from types import SimpleNamespace

import numpy as np
from scipy.optimize import minimize, NonlinearConstraint
from scipy import stats

import pandas as pd 
import matplotlib.pyplot as plt

class HouseholdSpecializationModelClass:

    def __init__(self):
        """ setup model """

        # a. create namespaces
        par = self.par = SimpleNamespace()
        sol = self.sol = SimpleNamespace()

        # b. preferences
        par.rho = 2.0
        par.nu = 0.001
        par.epsilon = 1.0
        par.omega = 0.5 

        # c. household production
        par.alpha = 0.5
        par.sigma = 1

        # d. wages
        par.wM = 1.0
        par.wF = 1.0
        par.wF_vec = np.linspace(0.8,1.2,5)

        # e. targets
        par.beta0_target = 0.4
        par.beta1_target = -0.1

        # f. solution
        sol.LM_vec = np.zeros(par.wF_vec.size)
        sol.HM_vec = np.zeros(par.wF_vec.size)
        sol.LF_vec = np.zeros(par.wF_vec.size)
        sol.HF_vec = np.zeros(par.wF_vec.size)

        sol.beta0 = np.nan
        sol.beta1 = np.nan

    def calc_utility(self,LM,HM,LF,HF):
        """ calculate utility """

        par = self.par
        sol = self.sol

        # a. consumption of market goods
        C = par.wM*LM + par.wF*LF

        # b. home production
        if par.sigma == 1:
            H = HM**(1-par.alpha)*HF**par.alpha
        elif par.sigma == 0:
            H = np.minimum(HM,HF)
        else:
            H = ((1-par.alpha)*HM**((par.sigma-1)/par.sigma)+par.alpha*HF**((par.sigma-1)/par.sigma))**((par.sigma/(par.sigma-1)))

        # c. total consumption utility
        Q = C**par.omega*H**(1-par.omega)
        utility = np.fmax(Q,1e-8)**(1-par.rho)/(1-par.rho)

        # d. disutlity of work
        epsilon_ = 1+1/par.epsilon
        TM = LM+HM
        TF = LF+HF
        disutility = par.nu*(TM**epsilon_/epsilon_+TF**epsilon_/epsilon_)
        
        return utility - disutility

    def solve_discrete(self,do_print=False):
        """ solve model discretely """
        
        par = self.par
        sol = self.sol
        opt = SimpleNamespace()
        
        # a. all possible choices
        x = np.linspace(0,24,49)
        LM,HM,LF,HF = np.meshgrid(x,x,x,x) # all combinations
    
        LM = LM.ravel() # vector
        HM = HM.ravel()
        LF = LF.ravel()
        HF = HF.ravel()

        # b. calculate utility
        u = self.calc_utility(LM,HM,LF,HF)
    
        # c. set to minus infinity if constraint is broken
        I = (LM+HM > 24) | (LF+HF > 24) # | is "or"
        u[I] = -np.inf
    
        # d. find maximizing argument
        j = np.argmax(u)
        
        opt.LM = LM[j]
        opt.HM = HM[j]
        opt.LF = LF[j]
        opt.HF = HF[j]

        # e. print
        if do_print:
            for k,v in opt.__dict__.items():
                print(f'{k} = {v:6.4f}')

        return opt

    def solve_continuous(self,do_print=False):
        """ solve model continously """
        par = self.par
        sol = self.sol
        opt = SimpleNamespace()

        # a. Start by making guesses, this is because we need a starting point
        LM_guess = 6
        LF_guess = 6
        HM_guess = 6
        HF_guess = 6
        x_guess = [LM_guess, LF_guess, HM_guess, HF_guess]

        # Create an objective.
        # The objective is a negative utility function, thereby to maximize this function we need to optimize.minimize it
        obj = lambda x: -self.calc_utility(x[0], x[1], x[2], x[3])

        # c. We define borders, i.e. maximum and minimum values
        bounds = ((1e-8, 24-1e-8), (1e-8, 24-1e-8), (1e-8, 24-1e-8), (1e-8, 24-1e-8))

        # d. Crete result thorugh Nelder-Meld method
        result = minimize(obj, x_guess, method='Nelder-Mead', bounds=bounds)

        opt.LM = result.x[0]
        opt.LF = result.x[1]
        opt.HM = result.x[2]
        opt.HF = result.x[3]

        # e. print
        if do_print:
            for k, v in opt.__dict__.items():
                print(f"{k} = {v:6.4f}")

        return opt

    def solve_wF_vec(self, discrete=False):
        """ solve model for vector of female wages """

        sol = self.sol
        par = self.par

        for i, w_F in enumerate(par.wF_vec):
            par.wF = w_F
            if discrete:
                opt = self.solve_discrete()
            else:
                opt = self.solve_continuous()
            if opt is not None:
                sol.LM_vec[i], sol.HM_vec[i], sol.LF_vec[i], sol.HF_vec[i] = opt.LM, opt.HM, opt.LF, opt.HF

    # Defining the regression method        
    def run_regression(self, print_beta=False):
        """ run regression """

        sol = self.sol

        sol.beta0 = 0.4
        sol.beta1 = -0.1

        if print_beta:
            print(f"Beta0 = {sol.beta0}, Beta1 = {sol.beta1}")

    def estimate(self, do_print=False):
        """estimate alpha and beta using regression"""
        
        beta0_hat_list = []
        beta1_hat_list = []

    def calc_utility_extension(self, LM, HM, LF, HF):
        """ calculate utility with savings and investment """

        par = self.par
        sol = self.sol

        # Calculate individual market incomes
        IM = par.wM * LM + par.wF * LF
        IF = par.wM * HM + par.wF * HF

        # Calculate total household income
        income = IM + IF

        # Calculate savings and investments
        savings = 0.169 * income
        investment = 0.092 * income

        # Calculate consumption of market goods
        C = (1 - 0.169 - 0.092) * income

        # Calculate home production
        if par.sigma == 1:
            H = HM ** (1 - par.alpha) * HF ** par.alpha
        elif par.sigma == 0:
            H = np.minimum(HM, HF)
        else:
            H = (
                (1 - par.alpha) * HM ** ((par.sigma - 1) / par.sigma)
                + par.alpha * HF ** ((par.sigma - 1) / par.sigma)
            ) ** (par.sigma / (par.sigma - 1))

        # Calculate total consumption utility
        Q = C ** par.omega * H ** (1 - par.omega)
        utility = np.fmax(Q, 1e-8) ** (1 - par.rho) / (1 - par.rho)

        # Calculate disutility of work
        epsilon_ = 1 + 1 / par.epsilon
        TM = LM + HM
        TF = LF + HF
        disutility = par.nu * (
            TM ** epsilon_ / epsilon_ + TF ** epsilon_ / epsilon_
        )

        return utility - disutility
    
    def calc_utility_extension(self, LM, HM, LF, HF):
    par = self.par
    sol = self.sol

    # Calculate individual market incomes
    IM = par.wM * LM + par.wF * LF
    IF = par.wM * HM + par.wF * HF

    # Calculate total household income
    income = IM + IF

    # Calculate savings and investments
    savings = 0.169 * income
    investment = 0.092 * income

    # Calculate consumption of market goods
    C = (1 - 0.169 - 0.092) * income

    # Calculate home production
    if par.sigma == 1:
        H = HM ** (1 - par.alpha) * HF ** par.alpha
    elif par.sigma == 0:
        H = np.minimum(HM, HF)
    else:
        H = (
            (1 - par.alpha) * HM ** ((par.sigma - 1) / par.sigma)
            + par.alpha * HF ** ((par.sigma - 1) / par.sigma)
        ) ** (par.sigma / (par.sigma - 1))

    # Calculate total consumption utility
    Q = C ** par.omega * H ** (1 - par.omega)
    utility = np.fmax(Q, 1e-8) ** (1 - par.rho) / (1 - par.rho)

    # Calculate disutility of work
    epsilon_ = 1 + 1 / par.epsilon
    TM = LM + HM
    TF = LF + HF
    disutility = par.nu * (
        TM ** epsilon_ / epsilon_ + TF ** epsilon_ / epsilon_
    )

    return utility - disutility