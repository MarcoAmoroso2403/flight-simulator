"""
compute_trim 
    - Chapter 5 assignment for Beard & McLain, PUP, 2012
    - Update history:  
        2/5/2019 - RWB
"""
import sys
sys.path.append('..')
import numpy as np
from scipy.optimize import minimize
from tools.tools import Euler2Quaternion

def compute_trim(mav, Va, gamma):
    # define initial state and input
    e = Euler2Quaternion(0, gamma, 0)
    state = mav._state
    state0 = np.vstack((state[0], state[1], state[2], mav._Va, 0, 0, e[0], e[1], e[2], e[3], 0, 0, 0))
    delta0 = np.vstack((0, 0, 0, 0.5))
    x0 = np.concatenate((state0, delta0), axis=0)
    # define equality constraints
    cons = ({'type': 'eq',
             'fun': lambda x: np.array([
                                x[3]**2 + x[4]**2 + x[5]**2 - Va**2,  # magnitude of velocity vector is Va
                                x[4],  # v=0, force side velocity to be zero
                                x[6]**2 + x[7]**2 + x[8]**2 + x[9]**2 - 1.,  # force quaternion to be unit length
                                x[7], # e1=0  - forcing e1=e3=0 ensures zero roll and zero yaw in trim
                                x[9], # e3=0
                                x[10], # p=0  - angular rates should all be zero
                                x[11], # q=0
                                x[12], # r=0
                                ]),
             'jac': lambda x: np.array([
                                [0., 0., 0., 2*x[3], 2*x[4], 2*x[5], 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 2*x[6], 2*x[7], 2*x[8], 2*x[9], 0., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0.],
                                ])
             })
    # solve the minimization problem to find the trim states and inputs
    res = minimize(trim_objective, x0, method='SLSQP', args = (mav, Va, gamma),
                   constraints=cons, options={'ftol': 1e-10, 'disp': True})
    # extract trim state and input and return
    trim_state = np.array([res.x[0:13]]).T
    trim_input = np.array([res.x[13:17]]).T
    return trim_state, trim_input

# objective function to be minimized
def trim_objective(x, mav, Va, gamma):
    state_vars = x[0:13]
    delta_vars = x[14:17]
    mav._state = state_vars
    mav._update_velocity_data()
    forces_moments = mav._forces_moments(delta_vars)
    f = mav._derivatives(mav._state, forces_moments)
    xdotdesired =  np.vstack((0,0, -Va*np.sin(gamma),0,0,0,0,0,0,0,0,0,0))
    result = f - xdotdesired
    J = np.linalg.norm(result[2:13])**2
    return J

