# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2018 Caleb Bell <Caleb.Andrew.Bell@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

from __future__ import division
from math import cos, sin, tan, atan, pi, radians, exp, acos, log10
import numpy as np
from fluids.friction import friction_factor
from scipy.optimize import newton, brenth
from scipy.constants import g, inch

__all__ = ['C_Reader_Harris_Gallagher',
           'differential_pressure_meter_solver',
           'differential_pressure_meter_dP',
           'orifice_discharge', 'orifice_expansibility',
           'Reader_Harris_Gallagher_discharge',
           'discharge_coefficient_to_K', 'K_to_discharge_coefficient',
           'dP_orifice', 'velocity_of_approach_factor', 
           'flow_coefficient', 'nozzle_expansibility',
           'C_long_radius_nozzle', 'C_ISA_1932_nozzle', 'C_venturi_nozzle',
           'orifice_expansibility_1989', 'dP_venturi_tube',
           'diameter_ratio_cone_meter', 'diameter_ratio_wedge_meter',
           'cone_meter_expansibility_Stewart', 'dP_cone_meter',
           'C_wedge_meter_Miller',
           'C_Reader_Harris_Gallagher_wet_venturi_tube',
           ]


CONCENTRIC_ORIFICE = 'concentric'
ECCENTRIC_ORIFICE = 'eccentric'
SEGMENTAL_ORIFICE = 'segmental'
CONDITIONING_4_HOLE_ORIFICE = 'Rosemount 4 hole self conditioing'
ORIFICE_HOLE_TYPES = [CONCENTRIC_ORIFICE, ECCENTRIC_ORIFICE, SEGMENTAL_ORIFICE,
                      CONDITIONING_4_HOLE_ORIFICE]

ORIFICE_CORNER_TAPS = 'corner'
ORIFICE_FLANGE_TAPS = 'flange'
ORIFICE_D_AND_D_2_TAPS = 'D and D/2'



ISO_5167_ORIFICE = 'ISO 5167 orifice'

LONG_RADIUS_NOZZLE = 'long radius nozzle'
ISA_1932_NOZZLE = 'ISA 1932 nozzle'
VENTURI_NOZZLE = 'venuri nozzle'

AS_CAST_VENTURI_TUBE = 'as cast convergent venturi tube'
MACHINED_CONVERGENT_VENTURI_TUBE = 'machined convergent venturi tube'
ROUGH_WELDED_CONVERGENT_VENTURI_TUBE = 'rough welded convergent venturi tube'

CONE_METER = 'cone meter'
WEDGE_METER = 'wedge meter'
__all__.extend(['ISO_5167_ORIFICE', 'LONG_RADIUS_NOZZLE', 'ISA_1932_NOZZLE',
                'VENTURI_NOZZLE', 'AS_CAST_VENTURI_TUBE', 
                'MACHINED_CONVERGENT_VENTURI_TUBE',
                'ROUGH_WELDED_CONVERGENT_VENTURI_TUBE', 'CONE_METER',
                'WEDGE_METER'])


def orifice_discharge(D, Do, P1, P2, rho, C, expansibility=1.0):
    r'''Calculates the flow rate of an orifice plate based on the geometry
    of the plate, measured pressures of the orifice, and the density of the
    fluid.
    
    .. math::
        m = \left(\frac{\pi D_o^2}{4}\right) C \frac{\sqrt{2\Delta P \rho_1}}
        {\sqrt{1 - \beta^4}}\cdot \epsilon
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    C : float
        Coefficient of discharge of the orifice, [-]
    expansibility : float, optional
        Expansibility factor (1 for incompressible fluids, less than 1 for
        real fluids), [-]

    Returns
    -------
    m : float
        Mass flow rate of fluid, [kg/s]

    Notes
    -----
    This is formula 1-12 in [1]_ and also [2]_.

    Examples
    --------
    >>> orifice_discharge(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, rho=1.1646, 
    ... C=0.5988, expansibility=0.9975)
    0.01120390943807026

    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    dP = P1 - P2
    beta = Do/D
    return (pi*Do*Do/4.)*C*(2*dP*rho)**0.5/(1.0 - beta**4)**0.5*expansibility


def orifice_expansibility(D, Do, P1, P2, k):
    r'''Calculates the expansibility factor for orifice plate calculations
    based on the geometry of the plate, measured pressures of the orifice, and
    the isentropic exponent of the fluid.
    
    .. math::
        \epsilon = 1 - (0.351 + 0.256\beta^4 + 0.93\beta^8)
        \left[1-\left(\frac{P_2}{P_1}\right)^{1/\kappa}\right]
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    k : float
        Isentropic exponent of fluid, [-]

    Returns
    -------
    expansibility : float, optional
        Expansibility factor (1 for incompressible fluids, less than 1 for
        real fluids), [-]

    Notes
    -----
    This formula was determined for the range of P2/P1 >= 0.80, and for fluids
    of air, steam, and natural gas. However, there is no objection to using
    it for other fluids.

    Examples
    --------
    >>> orifice_expansibility(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, k=1.4)
    0.9974739057343425

    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    beta = Do/D
    return (1.0 - (0.351 + 0.256*beta**4 + 0.93*beta**8)*(
            1.0 - (P2/P1)**(1./k)))


def orifice_expansibility_1989(D, Do, P1, P2, k):
    r'''Calculates the expansibility factor for orifice plate calculations
    based on the geometry of the plate, measured pressures of the orifice, and
    the isentropic exponent of the fluid.
    
    .. math::
        \epsilon = 1- (0.41 + 0.35\beta^4)\Delta P/\kappa/P_1
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    k : float
        Isentropic exponent of fluid, [-]

    Returns
    -------
    expansibility : float
        Expansibility factor (1 for incompressible fluids, less than 1 for
        real fluids), [-]

    Notes
    -----
    This formula was determined for the range of P2/P1 >= 0.75, and for fluids
    of air, steam, and natural gas. However, there is no objection to using
    it for other fluids.
    
    This is an older formula used to calculate expansibility factors for 
    orifice plates.
    
    In this standard, an expansibility factor formula transformation in terms  
    of the pressure after the orifice is presented as well. This is the more
    standard formulation in terms of the upstream conditions. The other formula
    is below for reference only:
    
    .. math::
        \epsilon_2 = \sqrt{1 + \frac{\Delta P}{P_2}} -  (0.41 + 0.35\beta^4)
        \frac{\Delta P}{\kappa P_2 \sqrt{1 + \frac{\Delta P}{P_2}}}
        
    [2]_ recommends this formulation for wedge meters as well.

    Examples
    --------
    >>> orifice_expansibility_1989(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, k=1.4)
    0.9970510687411718

    References
    ----------
    .. [1] American Society of Mechanical Engineers. MFC-3M-1989 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2005.
    .. [2] Miller, Richard W. Flow Measurement Engineering Handbook. 3rd
       edition. New York: McGraw-Hill Education, 1996.
    '''
    return 1.0 - (0.41 + 0.35*(Do/D)**4)*(P1 - P2)/(k*P1)


def C_Reader_Harris_Gallagher(D, Do, rho, mu, m, taps='corner'):
    r'''Calculates the coefficient of discharge of the orifice based on the 
    geometry of the plate, measured pressures of the orifice, mass flow rate
    through the orifice, and the density and viscosity of the fluid.
    
    .. math::
        C = 0.5961 + 0.0261\beta^2 - 0.216\beta^8 + 0.000521\left(\frac{
        10^6\beta}{Re_D}\right)^{0.7}\\
        + (0.0188 + 0.0063A)\beta^{3.5} \left(\frac{10^6}{Re_D}\right)^{0.3} \\
        +(0.043 + 0.080\exp(-10L_1) -0.123\exp(-7L_1))(1-0.11A)\frac{\beta^4}
        {1-\beta^4} \\
        -  0.031(M_2' - 0.8M_2'^{1.1})\beta^{1.3}
        
    .. math::
        M_2' = \frac{2L_2'}{1-\beta}
        
        A = \left(\frac{19000\beta}{Re_{D}}\right)^{0.8}
        
        Re_D = \frac{\rho v D}{\mu}
        
        
    If D < 71.12 mm (2.8 in.):
        
    .. math::
        C += 0.11(0.75-\beta)\left(2.8-\frac{D}{0.0254}\right)
        
    If the orifice has corner taps:
        
    .. math::
        L_1 = L_2' = 0
        
    If the orifice has D and D/2 taps:
        
    .. math::
        L_1 = 1
        
        L_2' = 0.47
    
    If the orifice has Flange taps:
    
    .. math::
        L_1 = L_2' = \frac{0.0254}{D}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    mu : float
        Viscosity of fluid at `P1`, [Pa*s]
    m : float
        Mass flow rate of fluid through the orifice, [kg/s]
    taps : str
        The orientation of the taps; one of 'corner', 'flange', 'D', or 'D/2',
        [-]
        
    Returns
    -------
    C : float
        Coefficient of discharge of the orifice, [-]

    Notes
    -----
    The following limits apply to the orifice plate standard [1]_:
        
    The measured pressure difference for the orifice plate should be under
    250 kPa.
    
    There are roughness limits as well; the roughness should be under 6 
    micrometers, although there are many more conditions to that given in [1]_.
        
    For orifice plates with D and D/2 or corner pressure taps:
        
    * Orifice bore diameter muse be larger than 12.5 mm (0.5 inches)
    * Pipe diameter between 50 mm and 1 m (2 to 40 inches)
    * Beta between 0.1 and 0.75 inclusive
    * Reynolds number larger than 5000 (for :math:`0.10 \le \beta \le 0.56`)
      or for :math:`\beta \ge 0.56, Re_D \ge 16000\beta^2`
      
    For orifice plates with flange pressure taps:

    * Orifice bore diameter muse be larger than 12.5 mm (0.5 inches)
    * Pipe diameter between 50 mm and 1 m (2 to 40 inches)
    * Beta between 0.1 and 0.75 inclusive
    * Reynolds number larger than 5000 and also larger than
      :math:`170000\beta^2 D`.
      
    This is also presented in Crane's TP410 (2009)publication, whereas the
    1999 and 1982 editions showed only a graph for discharge coefficients.
    
    Examples
    --------
    >>> C_Reader_Harris_Gallagher(D=0.07391, Do=0.0222, rho=1.165, mu=1.85E-5, 
    ... m=0.12, taps='flange')
    0.5990326277163659
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.  
    .. [3] Reader-Harris, M. J., "The Equation for the Expansibility Factor for
       Orifice Plates," Proceedings of FLOMEKO 1998, Lund, Sweden, 1998: 
       209-214.
    .. [4] Reader-Harris, Michael. Orifice Plates and Venturi Tubes. Springer, 
       2015.
    '''
    A_pipe = pi/4.*D*D
    v = m/(A_pipe*rho)
    Re_D = rho*v*D/mu
    
    beta = Do/D
    if taps == 'corner':
        L1, L2_prime = 0.0, 0.0
    elif taps == 'D' or taps == 'D/2':
        L1 = 1.0
        L2_prime = 0.47
    elif taps == 'flange':
        L1 = L2_prime = 0.0254/D
    else:
        raise Exception('Unsupported tap location')
        
    beta2 = beta*beta
    beta4 = beta2*beta2
    beta8 = beta4*beta4
    
    A = (19000.0*beta/Re_D)**0.8
    M2_prime = 2*L2_prime/(1.0 - beta)
    
    delta_C_upstream = ((0.043 + 0.080*exp(-1E1*L1) - 0.123*exp(-7.0*L1))
            *(1.0 - 0.11*A)*beta4/(1.0 - beta4))
    
    # The max part is not in the ISO standard
    delta_C_downstream = (-0.031*(M2_prime - 0.8*M2_prime**1.1)*beta**1.3
                          *(1.0 + 8*max(log10(3700./Re_D), 0.0)))
    
    # C_inf is discharge coefficient with corner taps for infinite Re
    # Cs, slope term, provides increase in discharge coefficient for lower
    # Reynolds numbers.
    
    # max term is not in the ISO standard
    C_inf_C_s = (0.5961 + 0.0261*beta2 - 0.216*beta8 
                 + 0.000521*(1E6*beta/Re_D)**0.7
                 + (0.0188 + 0.0063*A)*beta**3.5*(
                 max((1E6/Re_D)**0.3, 22.7 - 4700.0*(Re_D/1E6))))
    
    C = (C_inf_C_s + delta_C_upstream + delta_C_downstream)
    if D < 0.07112:
        # Limit is 2.8 inches, .1 inches smaller than the internal diameter of
        # a sched. 80 pipe.
        # Suggested to be required not becausue of any effect of small
        # diameters themselves, but because of edge radius differences.
        # max term is given in [4]_ Reader-Harris, Michael book
        delta_C_diameter = 0.011*(0.75 - beta)*max((2.8 - D/0.0254), 0.0)
        C += delta_C_diameter
    
    return C


def Reader_Harris_Gallagher_discharge(D, Do, P1, P2, rho, mu, k, taps='corner'):
    r'''Calculates the mass flow rate of fluid through an orifice based on the 
    geometry of the plate, measured pressures of the orifice, and the density, 
    viscosity, and isentropic exponent of the fluid. This solves an equation
    iteratively to obtain the correct flow rate.
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    mu : float
        Viscosity of fluid at `P1`, [Pa*s]
    k : float
        Isentropic exponent of fluid, [-]
    taps : str
        The orientation of the taps; one of 'corner', 'flange', 'D', or 'D/2',
        [-]
        
    Returns
    -------
    m : float
        Mass flow rate of fluid through the orifice, [kg/s]

    Notes
    -----

    Examples
    --------
    >>> Reader_Harris_Gallagher_discharge(D=0.07366, Do=0.05, P1=200000.0, 
    ... P2=183000.0, rho=999.1, mu=0.0011, k=1.33, taps='D')
    7.702338035732167
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    def to_solve(m):
        C = C_Reader_Harris_Gallagher(D=D, Do=Do, 
            rho=rho, mu=mu, m=m, taps=taps)
        epsilon = orifice_expansibility(D=D, Do=Do, P1=P1, P2=P2, k=k)
        m_calc = orifice_discharge(D=D, Do=Do, P1=P1, P2=P2, rho=rho, 
                                    C=C, expansibility=epsilon)
        return m - m_calc
    
    return newton(to_solve, 2.81)


def discharge_coefficient_to_K(D, Do, C):
    r'''Converts a discharge coefficient to a standard loss coefficient,
    for use in computation of the actual pressure drop of an orifice or other
    device.

    .. math::
        K = \left[\frac{\sqrt{1-\beta^4(1-C^2)}}{C\beta^2} - 1\right]^2
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    C : float
        Coefficient of discharge of the orifice, [-]

    Returns
    -------
    K : float
        Loss coefficient with respect to the velocity and density of the fluid
        just upstream of the orifice, [-]

    Notes
    -----
    If expansibility is used in the orifice calculation, the result will not
    match with the specified pressure drop formula in [1]_; it can almost
    be matched by dividing the calculated mass flow by the expansibility factor
    and using that mass flow with the loss coefficient. 
    
    Examples
    --------
    >>> discharge_coefficient_to_K(D=0.07366, Do=0.05, C=0.61512)
    5.2314291729754
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    beta = Do/D
    beta2 = beta*beta
    beta4 = beta2*beta2
    return ((1.0 - beta4*(1.0 - C*C))**0.5/(C*beta2) - 1.0)**2


def K_to_discharge_coefficient(D, Do, K):
    r'''Converts a standard loss coefficient to a discharge coefficient.
    
    .. math::
        C = \sqrt{\frac{1}{2 \sqrt{K} \beta^{4} + K \beta^{4}}
        - \frac{\beta^{4}}{2 \sqrt{K} \beta^{4} + K \beta^{4}} }
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    K : float
        Loss coefficient with respect to the velocity and density of the fluid
        just upstream of the orifice, [-]

    Returns
    -------
    C : float
        Coefficient of discharge of the orifice, [-]

    Notes
    -----
    If expansibility is used in the orifice calculation, the result will not
    match with the specified pressure drop formula in [1]_; it can almost
    be matched by dividing the calculated mass flow by the expansibility factor
    and using that mass flow with the loss coefficient. 
    
    This expression was derived with SymPy, and checked numerically. There were
    three other, incorrect roots.
    
    Examples
    --------
    >>> K_to_discharge_coefficient(D=0.07366, Do=0.05, K=5.2314291729754)
    0.6151200000000001
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    beta = Do/D
    beta2 = beta*beta
    beta4 = beta2*beta2
    root_K = K**0.5
    common_term = 2.0*root_K*beta4 + K*beta4
    return (-beta4/(common_term) + 1.0/(common_term))**0.5


def dP_orifice(D, Do, P1, P2, C):
    r'''Calculates the non-recoverable pressure drop of an orifice plate based
    on the pressure drop and the geometry of the plate and the discharge 
    coefficient.
    
    .. math::
        \Delta\bar w = \frac{\sqrt{1-\beta^4(1-C^2)}-C\beta^2}
        {\sqrt{1-\beta^4(1-C^2)}+C\beta^2} (P_1 - P_2)
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    C : float
        Coefficient of discharge of the orifice, [-]

    Returns
    -------
    dP : float
        Non-recoverable pressure drop of the orifice plate, [Pa]

    Notes
    -----
    This formula can be well approximated by:
        
    .. math::
        \Delta\bar w = \left(1 - \beta^{1.9}\right)(P_1 - P_2)
        
    The recoverable pressure drop should be recovered by 6 pipe diameters 
    downstream of the orifice plate.
    
    Examples
    --------
    >>> dP_orifice(D=0.07366, Do=0.05, P1=200000.0, P2=183000.0, C=0.61512)
    9069.474705745388
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-2:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 2: Orifice Plates.
    '''
    beta = Do/D
    beta2 = beta*beta
    beta4 = beta2*beta2
    dP = P1 - P2
    delta_w = ((1.0 - beta4*(1.0 - C*C))**0.5 - C*beta2)/(
               (1.0 - beta4*(1.0 - C*C))**0.5 + C*beta2)*dP
    return delta_w


def velocity_of_approach_factor(D, Do):
    r'''Calculates a factor for orifice plate design called the `velocity of
    approach`.
    
    .. math::
        \text{Velocity of approach} = \frac{1}{\sqrt{1 - \beta^4}}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice at flow conditions, [m]

    Returns
    -------
    velocity_of_approach : float
        Coefficient of discharge of the orifice, [-]

    Notes
    -----
    
    Examples
    --------
    >>> velocity_of_approach_factor(D=0.0739, Do=0.0222)
    1.0040970074165514
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    '''
    return (1.0 - (Do/D)**4)**-0.5


def flow_coefficient(D, Do, C):
    r'''Calculates a factor for differential pressure flow meter design called 
    the `flow coefficient`. This should not be confused with the flow 
    coefficient often used when discussing valves.
    
    .. math::
        \text{Flow coefficient} = \frac{C}{\sqrt{1 - \beta^4}}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of flow meter characteristic dimension at flow conditions, [m]
    C : float
        Coefficient of discharge of the flow meter, [-]

    Returns
    -------
    flow_coefficient : float
        Differential pressure flow meter flow coefficient, [-]

    Notes
    -----
    This measure is used not just for orifices but for other differential 
    pressure flow meters [2]_.
    
    It is sometimes given the symbol K. It is also equal to the product of the
    diacharge coefficient and the velocity of approach factor [2]_.
    
    Examples
    --------
    >>> flow_coefficient(D=0.0739, Do=0.0222, C=0.6)
    0.6024582044499308
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] Miller, Richard W. Flow Measurement Engineering Handbook. 3rd
       edition. New York: McGraw-Hill Education, 1996.
    '''
    return C*(1.0 - (Do/D)**4)**-0.5


def nozzle_expansibility(D, Do, P1, P2, k):
    r'''Calculates the expansibility factor for a nozzle or venturi nozzle,
    based on the geometry of the plate, measured pressures of the orifice, and
    the isentropic exponent of the fluid.
    
    .. math::
        \epsilon = \left\{\left(\frac{\kappa \tau^{2/\kappa}}{\kappa-1}\right)
        \left(\frac{1 - \beta^4}{1 - \beta^4 \tau^{2/\kappa}}\right)
        \left[\frac{1 - \tau^{(\kappa-1)/\kappa}}{1 - \tau}
        \right] \right\}^{0.5}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of orifice of the venturi or nozzle, [m]
    P1 : float
        Static pressure of fluid upstream of orifice at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of orifice at the cross-section of
        the pressure tap, [Pa]
    k : float
        Isentropic exponent of fluid, [-]

    Returns
    -------
    expansibility : float
        Expansibility factor (1 for incompressible fluids, less than 1 for
        real fluids), [-]

    Notes
    -----
    This formula was determined for the range of P2/P1 >= 0.75.

    Examples
    --------
    >>> nozzle_expansibility(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, k=1.4)
    0.9945702344566746

    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-3:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 3: Nozzles and Venturi Nozzles.
    '''
    beta = Do/D
    beta2 = beta*beta
    beta4 = beta2*beta2
    tau = P2/P1
    term1 = k*tau**(2.0/k )/(k - 1.0)
    term2 = (1.0 - beta4)/(1.0 - beta4*tau**(2.0/k))
    term3 = (1.0 - tau**((k - 1.0)/k))/(1.0 - tau)
    return (term1*term2*term3)**0.5


def C_long_radius_nozzle(D, Do, rho, mu, m):
    r'''Calculates the coefficient of discharge of a long radius nozzle used
    for measuring flow rate of fluid, based on the geometry of the nozzle, 
    mass flow rate through the nozzle, and the density and viscosity of the
    fluid.
    
    .. math::
        C = 0.9965 - 0.00653\beta^{0.5} \left(\frac{10^6}{Re_D}\right)^{0.5}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of long radius nozzle orifice at flow conditions, [m]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    mu : float
        Viscosity of fluid at `P1`, [Pa*s]
    m : float
        Mass flow rate of fluid through the nozzle, [kg/s]
        
    Returns
    -------
    C : float
        Coefficient of discharge of the long radius nozzle orifice, [-]

    Notes
    -----
    
    Examples
    --------
    >>> C_long_radius_nozzle(D=0.07391, Do=0.0422, rho=1.2, mu=1.8E-5, m=0.1)
    0.9805503704679863
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-3:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 3: Nozzles and Venturi Nozzles.
    '''
    A_pipe = pi/4.*D*D
    v = m/(A_pipe*rho)
    Re_D = rho*v*D/mu
    beta = Do/D
    return 0.9965 - 0.00653*beta**0.5*(1E6/Re_D)**0.5


def C_ISA_1932_nozzle(D, Do, rho, mu, m):
    r'''Calculates the coefficient of discharge of an ISA 1932 style nozzle 
    used for measuring flow rate of fluid, based on the geometry of the nozzle, 
    mass flow rate through the nozzle, and the density and viscosity of the
    fluid.
    
    .. math::
        C = 0.9900 - 0.2262\beta^{4.1} - (0.00175\beta^2 - 0.0033\beta^{4.15})
        \left(\frac{10^6}{Re_D}\right)^{1.15}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of nozzle orifice at flow conditions, [m]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    mu : float
        Viscosity of fluid at `P1`, [Pa*s]
    m : float
        Mass flow rate of fluid through the nozzle, [kg/s]
        
    Returns
    -------
    C : float
        Coefficient of discharge of the nozzle orifice, [-]

    Notes
    -----
    
    Examples
    --------
    >>> C_ISA_1932_nozzle(D=0.07391, Do=0.0422, rho=1.2, mu=1.8E-5, m=0.1)
    0.9635849973250495
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-3:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 3: Nozzles and Venturi Nozzles.
    '''
    A_pipe = pi/4.*D*D
    v = m/(A_pipe*rho)
    Re_D = rho*v*D/mu
    beta = Do/D
    C = (0.9900 - 0.2262*beta**4.1
         - (0.00175*beta**2 - 0.0033*beta**4.15)*(1E6/Re_D)**1.15)
    return C


def C_venturi_nozzle(D, Do):
    r'''Calculates the coefficient of discharge of an Venturi style nozzle 
    used for measuring flow rate of fluid, based on the geometry of the nozzle.
    
    .. math::
        C = 0.9858 - 0.196\beta^{4.5}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of nozzle orifice at flow conditions, [m]
        
    Returns
    -------
    C : float
        Coefficient of discharge of the nozzle orifice, [-]

    Notes
    -----
    
    Examples
    --------
    >>> C_venturi_nozzle(D=0.07391, Do=0.0422)
    0.9698996454169576
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-3:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 3: Nozzles and Venturi Nozzles.
    '''
    beta = Do/D
    return 0.9858 - 0.198*beta**4.5


# Relative pressure loss as a function of beta reatio for venturi nozzles
# Venturi nozzles should be between 65 mm and 500 mm; there are high and low
# loss ratios , with the high losses corresponding to small diameters,
# low high losses corresponding to large diameters
# Interpolation can be performed.

venturi_tube_betas = np.array(
        [0.299160, 0.299470, 0.312390, 0.319010, 0.326580, 0.337290, 
          0.342020, 0.347060, 0.359030, 0.365960, 0.372580, 0.384870, 
          0.385810, 0.401250, 0.405350, 0.415740, 0.424250, 0.434010, 
          0.447880, 0.452590, 0.471810, 0.473090, 0.493540, 0.499240,
          0.516530, 0.523800, 0.537630, 0.548060, 0.556840, 0.573890,
          0.582350, 0.597820, 0.601560, 0.622650, 0.626490, 0.649480, 
          0.650990, 0.668700, 0.675870, 0.688550, 0.693180, 0.706180, 
          0.713330, 0.723510, 0.749540, 0.749650])
            
venturi_tube_dP_high = np.array(
        [0.164534, 0.164504, 0.163591, 0.163508, 0.163439,
        0.162652, 0.162224, 0.161866, 0.161238, 0.160786,
        0.160295, 0.159280, 0.159193, 0.157776, 0.157467, 
        0.156517, 0.155323, 0.153835, 0.151862, 0.151154, 
        0.147840, 0.147613, 0.144052, 0.143050, 0.140107, 
        0.138981, 0.136794, 0.134737, 0.132847, 0.129303, 
        0.127637, 0.124758, 0.124006, 0.119269, 0.118449,
        0.113605, 0.113269, 0.108995, 0.107109, 0.103688, 
        0.102529, 0.099567, 0.097791, 0.095055, 0.087681, 
        0.087648])
            
venturi_tube_dP_low = np.array(
    [0.089232, 0.089218, 0.088671, 0.088435, 0.088206,
   0.087853, 0.087655, 0.087404, 0.086693, 0.086241,
   0.085813, 0.085142, 0.085102, 0.084446, 0.084202, 
   0.083301, 0.082470, 0.081650, 0.080582, 0.080213, 
   0.078509, 0.078378, 0.075989, 0.075226, 0.072700, 
   0.071598, 0.069562, 0.068128, 0.066986, 0.064658, 
   0.063298, 0.060872, 0.060378, 0.057879, 0.057403, 
   0.054091, 0.053879, 0.051726, 0.050931, 0.049362, 
   0.048675, 0.046522, 0.045381, 0.043840, 0.039913, 
   0.039896])
            
#ratios_average = 0.5*(ratios_high + ratios_low)
D_bound_venturi_tube = np.array([0.065, 0.5])


def dP_venturi_tube(D, Do, P1, P2):
    r'''Calculates the non-recoverable pressure drop of a venturi tube 
    differential pressure meter based on the pressure drop and the geometry of 
    the venturi meter.
    
    .. math::
        \epsilon =  \frac{\Delta\bar w }{\Delta P}
        
    The :math:`\epsilon` value is looked up in a table of values as a function
    of beta ratio and upstream pipe diameter (roughness impact).
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of venturi tube at flow conditions, [m]
    P1 : float
        Static pressure of fluid upstream of venturi tube at the cross-section 
        of the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of venturi tube at the
         cross-section of the pressure tap, [Pa]

    Returns
    -------
    dP : float
        Non-recoverable pressure drop of the venturi tube, [Pa]

    Notes
    -----
    The recoverable pressure drop should be recovered by 6 pipe diameters 
    downstream of the venturi tube.
    
    Note there is some information on the effect of Reynolds number as well
    in [1]_ and [2]_, with a curve showing an increased pressure drop
    from 1E5-6E5 to with a decreasing multiplier from 1.75 to 1; the multiplier
    is 1 for higher Reynolds numbers. This is not currently included in this
    implementation.
    
    Examples
    --------
    >>> dP_venturi_tube(D=0.07366, Do=0.05, P1=200000.0, P2=183000.0)
    1788.5717754177406
    
    References
    ----------
    .. [1] American Society of Mechanical Engineers. Mfc-3M-2004 Measurement 
       Of Fluid Flow In Pipes Using Orifice, Nozzle, And Venturi. ASME, 2001.
    .. [2] ISO 5167-4:2003 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 4: Venturi Tubes.
    '''
    # Effect of Re is not currently included
    beta = Do/D
    epsilon_D65 = np.interp(beta, venturi_tube_betas, venturi_tube_dP_high)
    epsilon_D500 = np.interp(beta, venturi_tube_betas, venturi_tube_dP_low)
    epsilon = np.interp(D, D_bound_venturi_tube, [epsilon_D65, epsilon_D500])
    return epsilon*(P1 - P2)


def diameter_ratio_cone_meter(D, Dc):
    r'''Calculates the diameter ratio `beta` used to characterize a cone 
    flow meter.
    
    .. math::
        \beta = \sqrt{1 - \frac{d_c^2}{D^2}}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Dc : float
        Diameter of the largest end of the cone meter, [m]
        
    Returns
    -------
    beta : float
        Cone meter diameter ratio, [-]

    Notes
    -----
    
    Examples
    --------
    >>> diameter_ratio_cone_meter(D=0.2575, Dc=0.184)
    0.6995709873957624
    
    References
    ----------
    .. [1] Hollingshead, Colter. "Discharge Coefficient Performance of Venturi,
       Standard Concentric Orifice Plate, V-Cone, and Wedge Flow Meters at 
       Small Reynolds Numbers." May 1, 2011. 
       https://digitalcommons.usu.edu/etd/869.
    '''
    D_ratio = Dc/D
    return (1.0 - D_ratio*D_ratio)**0.5


def cone_meter_expansibility_Stewart(D, Dc, P1, P2, k):
    r'''Calculates the expansibility factor for a cone flow meter,
    based on the geometry of the cone meter, measured pressures of the orifice, 
    and the isentropic exponent of the fluid. Developed in [1]_, also shown
    in [2]_.
    
    .. math::
        \epsilon = 1 - (0.649 + 0.696\beta^4) \frac{\Delta P}{\kappa P_1}

    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Dc : float
        Diameter of the largest end of the cone meter, [m]
    P1 : float
        Static pressure of fluid upstream of cone meter at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid at the end of the center of the cone pressure 
        tap, [Pa]
    k : float
        Isentropic exponent of fluid, [-]

    Returns
    -------
    expansibility : float
        Expansibility factor (1 for incompressible fluids, less than 1 for
        real fluids), [-]

    Notes
    -----
    This formula was determined for the range of P2/P1 >= 0.75; the only gas
    used to determine the formula is air.

    Examples
    --------
    >>> cone_meter_expansibility_Stewart(D=1, Dc=0.9, P1=1E6, P2=8.5E5, k=1.2)
    0.9157343

    References
    ----------
    .. [1] Stewart, D. G., M. Reader-Harris, and NEL Dr RJW Peters. "Derivation
       of an Expansibility Factor for the V-Cone Meter." In Flow Measurement 
       International Conference, Peebles, Scotland, UK, 2001.
    .. [2] ISO 5167-5:2016 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 5: Cone meters.
    '''
    dP = P1 - P2
    beta = diameter_ratio_cone_meter(D, Dc)
    return 1.0 - (0.649 + 0.696*beta**4)*dP/(k*P1)


def dP_cone_meter(D, Dc, P1, P2):
    r'''Calculates the non-recoverable pressure drop of a cone meter
    based on the measured pressures before and at the cone end, and the 
    geometry of the cone meter according to [1]_.
    
    .. math::
        \Delta \bar \omega = (1.09 - 0.813\beta)\Delta P
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    Dc : float
        Diameter of the largest end of the cone meter, [m]
    P1 : float
        Static pressure of fluid upstream of cone meter at the cross-section of
        the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid at the end of the center of the cone pressure 
        tap, [Pa]

    Returns
    -------
    dP : float
        Non-recoverable pressure drop of the orifice plate, [Pa]

    Notes
    -----
    The recoverable pressure drop should be recovered by 6 pipe diameters 
    downstream of the cone meter.
    
    Examples
    --------
    >>> dP_cone_meter(1, .7, 1E6, 9.5E5)
    25470.093437973323
    
    References
    ----------
    .. [1] ISO 5167-5:2016 - Measurement of Fluid Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits Running
       Full -- Part 5: Cone meters.
    '''
    dP = P1 - P2
    beta = diameter_ratio_cone_meter(D, Dc)
    return (1.09 - 0.813*beta)*dP


def diameter_ratio_wedge_meter(D, H):
    r'''Calculates the diameter ratio `beta` used to characterize a wedge 
    flow meter as given in [1]_ and [2]_.
    
    .. math::
        \beta = \left(\frac{1}{\pi}\left\{\arccos\left[1 - \frac{2H}{D}
        \right] - 2 \left[1 - \frac{2H}{D}
        \right]\left(\frac{H}{D} - \left[\frac{H}{D}\right]^2
        \right)^{0.5}\right\}\right)^{0.5}
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    H : float
        Portion of the diameter of the clear segment of the pipe up to the 
        wedge blocking flow; the height of the pipe up to the wedge, [m]
    
    Returns
    -------
    beta : float
        Wedge meter diameter ratio, [-]

    Notes
    -----
    
    Examples
    --------
    >>> diameter_ratio_wedge_meter(D=0.2027, H=0.0608)
    0.5022531424646643
    
    References
    ----------
    .. [1] Hollingshead, Colter. "Discharge Coefficient Performance of Venturi,
       Standard Concentric Orifice Plate, V-Cone, and Wedge Flow Meters at 
       Small Reynolds Numbers." May 1, 2011. 
       https://digitalcommons.usu.edu/etd/869.
    .. [2] IntraWedge WEDGE FLOW METER Type: IWM. January 2011.
       http://www.intra-automation.com/download.php?file=pdf/products/technical_information/en/ti_iwm_en.pdf
    '''
    H_D = H/D
    t0 = 1.0 - 2.0*H_D
    t1 = acos(t0)
    t2 = 2.0*(t0)
    t3 = (H_D - H_D*H_D)**0.5
    t4 = t1 - t2*t3
    return (1./pi*t4)**0.5


def C_wedge_meter_Miller(D, H):
    r'''Calculates the coefficient of discharge of an wedge flow meter
    used for measuring flow rate of fluid, based on the geometry of the 
    differential pressure flow meter.
    
    For half-inch lines:
        
    .. math::
        C = 0.7883 + 0.107(1 - \beta^2)
    
    For 1 to 1.5 inch lines:
        
    .. math::
        C = 0.6143 + 0.718(1 - \beta^2)
        
    For 1.5 to 24 inch lines:
        
    .. math::
        C = 0.5433 + 0.2453(1 - \beta^2)
        
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    H : float
        Portion of the diameter of the clear segment of the pipe up to the 
        wedge blocking flow; the height of the pipe up to the wedge, [m]
        
    Returns
    -------
    C : float
        Coefficient of discharge of the wedge flow meter, [-]

    Notes
    -----
    There is an ISO standard being developed to cover wedge meters as of 2018.
    
    Wedge meters can have varying angles; 60 and 90 degree wedge meters have
    been reported. Tap locations 1 or 2 diameters (upstream and downstream),
    and 2D upstream/1D downstream have been used. Some wedges are sharp;
    some are smooth. [2]_ gives some experimental values.
    
    Examples
    --------
    >>> C_wedge_meter_Miller(D=0.1524, H=0.3*0.1524)
    0.7267069372687651
    
    References
    ----------
    .. [1] Miller, Richard W. Flow Measurement Engineering Handbook. 3rd 
       edition. New York: McGraw-Hill Education, 1996.
    .. [2] Seshadri, V., S. N. Singh, and S. Bhargava. "Effect of Wedge Shape 
       and Pressure Tap Locations on the Characteristics of a Wedge Flowmeter."
       IJEMS Vol.01(5), October 1994.
    '''
    beta = diameter_ratio_wedge_meter(D, H)
    if D <= 0.7*inch:
        # suggested limit 0.5 inch for this equation
        C = 0.7883 + 0.107*(1 - beta*beta)
    elif D <= 1.4*inch:
        # Suggested limit is under 1.5 inches
        C = 0.6143 + 0.718*(1 - beta*beta)
    else:
        C = 0.5433 + 0.2453*(1 - beta*beta)
    return C


def _Lockhart_Martinelli_X(ml, mg, rhog, rhol):
    return ml/mg*(rhog/rhol)**0.5


def _Froude_gas_densiometric(mg, D, rhog, rhol, g=g):
    return 4*mg/(rhog*pi*D**2*(g*D)**0.5)*(rhog/(rhol - rhog))**0.5


def C_Reader_Harris_Gallagher_wet_venturi_tube(mg, ml, rhog, rhol, D, Do, H=1):
    r'''Calculates the coefficient of discharge of the wet gas venturi tube 
    based on the  geometry of the tube, mass flow rates of liquid and vapor
    through the tube, the density of the liquid and gas phases, and an 
    adjustable coefficient `H`.
    
    .. math::
        C = 1 - 0.0463\exp(-0.05Fr_{gas, th}) \cdot \min\left(1, 
        \sqrt{\frac{X}{0.016}}\right)
        
        Fr_{gas, th} = \frac{Fr_{\text{gas, densionetric }}}{\beta^{2.5}}
        
        \phi = \sqrt{1 + C_{Ch} X + X^2}
        
        C_{Ch} = \left(\frac{\rho_l}{\rho_{1,g}}\right)^n + 
        \left(\frac{\rho_{1, g}}{\rho_{l}}\right)^n
        
        n = \max\left[0.583 - 0.18\beta^2 - 0.578\exp\left(\frac{-0.8 
        Fr_{\text{gas, densiometric}}}{H}\right),0.392 - 0.18\beta^2 \right]
            
        X = \left(\frac{m_l}{m_g}\right) \sqrt{\frac{\rho_{1,g}}{\rho_l}}
        
        {Fr_{\text{gas, densiometric}}} = \frac{v_{gas}}{\sqrt{gD}}
        \sqrt{\frac{\rho_{1,g}}{\rho_l - \rho_{1,g}}}
        =  \frac{4m_g}{\rho_{1,g} \pi D^2 \sqrt{gD}}
        \sqrt{\frac{\rho_{1,g}}{\rho_l - \rho_{1,g}}}
        
    Parameters
    ----------
    mg : float
        Mass flow rate of gas through the venturi tube, [kg/s]
    ml : float
        Mass flow rate of liquid through the venturi tube, [kg/s]
    rhog : float
        Density of gas at `P1`, [kg/m^3]
    rhol : float
        Density of liquid at `P1`, [kg/m^3]
    D : float
        Upstream internal pipe diameter, [m]
    Do : float
        Diameter of venturi tube at flow conditions, [m]
    H : float, optional
        A surface-tension effect coefficient used to adjust for different 
        fluids, (1 for a hydrocarbon liquid, 1.35 for water, 0.79 for water in 
        steam) [-]

    Returns
    -------
    C : float
        Coefficient of discharge of the wet gas venturi tube flow meter
        (includes flow rate of gas ONLY), [-]

    Notes
    -----
    This model has more error than single phase differential pressure meters.
    The model was first published in [1]_, and became ISO 11583 later.
    
    Examples
    --------
    >>> C_Reader_Harris_Gallagher_wet_venturi_tube(mg=5.31926, ml=5.31926/2, 
    ... rhog=50.0, rhol=800., D=.1, Do=.06, H=1)
    0.9754210845876333
    
    References
    ----------
    .. [1] Reader-harris, Michael, and Tuv Nel. An Improved Model for 
       Venturi-Tube Over-Reading in Wet Gas, 2009. 
    .. [2] ISO/TR 11583:2012 Measurement of Wet Gas Flow by Means of Pressure 
       Differential Devices Inserted in Circular Cross-Section Conduits.
    '''
    Frg = _Froude_gas_densiometric(mg, D, rhog, rhol)
    beta = Do/D
    beta2 = beta*beta
    Fr_gas_th = Frg*beta**-2.5
    
    n = max(0.583 - 0.18*beta2 - 0.578*exp(-0.8*Frg/H), 
            0.392 - 0.18*beta2)
    
    C_Ch = (rhol/rhog)**n + (rhog/rhol)**n
    X = _Lockhart_Martinelli_X(ml, mg, rhog, rhol)
    OF = (1.0 + C_Ch*X + X*X)**0.5
    
    C = 1.0 - 0.0463*exp(-0.05*Fr_gas_th)*min(1.0, (X/0.016)**0.5)
    return C


# Venturi tube loss coefficients as a function of Re
as_cast_convergent_venturi_Res = [4E5, 6E4, 1E5, 1.5E5]
as_cast_convergent_venturi_Cs = [0.957, 0.966, 0.976, 0.982]

machined_convergent_venturi_Res = [5E4, 1E5, 2E5, 3E5, 
                                   7.5E5, # 5E5 to 1E6
                                   1.5E6, # 1E6 to 2E6
                                   5E6] # 2E6 to 1E8
machined_convergent_venturi_Cs = [0.970, 0.977, 0.992, 0.998, 0.995, 1.000, 1.010]

rough_welded_convergent_venturi_Res = [4E4, 6E4, 1E5]
rough_welded_convergent_venturi_Cs = [0.96, 0.97, 0.98]

as_cast_convergent_entrance_machined_venturi_Res = [1E4, 6E4, 1E5, 1.5E5,
                                                    3.5E5, # 2E5 to 5E5
                                                    3.2E6] # 5E5 to 3.2E6
as_cast_convergent_entrance_machined_venturi_Cs = [0.963, 0.978, 0.98, 0.987, 0.992, 0.995]


CONE_METER_C = 0.82
ROUGH_WELDED_CONVERGENT_VENTURI_TUBE_C = 0.985
MACHINED_CONVERGENT_VENTURI_TUBE_C = 0.995
AS_CAST_VENTURI_TUBE_C = 0.984


def _differential_pressure_C_epsilon(D, D2, m, P1, P2, rho, mu, k, meter_type, 
                                     taps=None):
    '''Helper function only.
    '''
    if meter_type == ISO_5167_ORIFICE:
        C = C_Reader_Harris_Gallagher(D=D, Do=D2, rho=rho, mu=mu, m=m, taps=taps)
        epsilon = orifice_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
    elif meter_type == LONG_RADIUS_NOZZLE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = C_long_radius_nozzle(D=D, Do=D2, rho=rho, mu=mu, m=m)
    elif meter_type == ISA_1932_NOZZLE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = C_ISA_1932_nozzle(D=D, Do=D2, rho=rho, mu=mu, m=m)
    elif meter_type == VENTURI_NOZZLE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = C_venturi_nozzle(D=D, Do=D2)     
    
    elif meter_type == AS_CAST_VENTURI_TUBE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = AS_CAST_VENTURI_TUBE_C    
    elif meter_type == MACHINED_CONVERGENT_VENTURI_TUBE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = MACHINED_CONVERGENT_VENTURI_TUBE_C
    elif meter_type == ROUGH_WELDED_CONVERGENT_VENTURI_TUBE:
        epsilon = nozzle_expansibility(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = ROUGH_WELDED_CONVERGENT_VENTURI_TUBE_C
        
    elif meter_type == CONE_METER:
        epsilon = cone_meter_expansibility_Stewart(D=D, Dc=D2, P1=P1, P2=P2, k=k)
        C = CONE_METER_C
    elif meter_type == WEDGE_METER:
        epsilon = orifice_expansibility_1989(D=D, Do=D2, P1=P1, P2=P2, k=k)
        C = C_wedge_meter_Miller(D=D, H=D2)
    return epsilon, C


def differential_pressure_meter_solver(D, rho, mu, k, D2=None, P1=None, P2=None, 
                                       m=None, meter_type=ISO_5167_ORIFICE, 
                                       taps=None):
    r'''Calculates either the mass flow rate, the upstream pressure, the second
    pressure value, or the orifice diameter for a differential
    pressure flow meter based on the geometry of the meter, measured pressures 
    of the meter, and the density, viscosity, and isentropic exponent of the 
    fluid. This solves an equation iteratively to obtain the correct flow rate.
    
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    rho : float
        Density of fluid at `P1`, [kg/m^3]
    mu : float
        Viscosity of fluid at `P1`, [Pa*s]
    k : float
        Isentropic exponent of fluid, [-]
    D2 : float, optional
        Diameter of orifice, or venturi meter orifice, or flow tube orifice,
        or cone meter end diameter, or wedge meter fluid flow height, [m]
    P1 : float, optional
        Static pressure of fluid upstream of differential pressure meter at the
        cross-section of the pressure tap, [Pa]
    P2 : float, optional
        Static pressure of fluid downstream of differential pressure meter or 
        at the prescribed location (varies by type of meter) [Pa]
    m : float, optional
        Mass flow rate of fluid through the flow meter, [kg/s]
    meter_type : str, optional
        One of ('ISO 5167 orifice', 'long radius nozzle', 'ISA 1932 nozzle', 
        'venuri nozzle', 'as cast convergent venturi tube', 
        'machined convergent venturi tube', 
        'rough welded convergent venturi tube', 'cone meter',
        'wedge meter'), [-]
    taps : str, optional
        The orientation of the taps; one of 'corner', 'flange', 'D', or 'D/2';
        applies for orifice meters only, [-]
        
    Returns
    -------
    ans : float
        One of `m`, the mass flow rate of the fluid; `P1`, the pressure 
        upstream of the flow meter; `P2`, the second pressure
        tap's value; and `D2`, the diameter of the measuring device; units
        of respectively, [kg/s], [Pa], [Pa], or [m]

    Notes
    -----
    See the appropriate functions for the documentation for the formulas and
    references used in each method.
    
    The solvers make some assumptions about the range of values answers may be
    in.
    
    Note that the solver for the upstream pressure uses the provided values of
    density, viscosity and isentropic exponent; whereas these values all
    depend on pressure (albeit to a small extent). An outer loop should be
    added with pressure-dependent values calculated in it for maximum accuracy.
    
    It would be possible to solve for the upstream pipe diameter, but there is
    no use for that functionality.
    
    Examples
    --------
    >>> differential_pressure_meter_solver(D=0.07366, D2=0.05, P1=200000.0, 
    ... P2=183000.0, rho=999.1, mu=0.0011, k=1.33, 
    ... meter_type='ISO 5167 orifice', taps='D')
    7.702338035732168
    
    >>> differential_pressure_meter_solver(D=0.07366, m=7.702338, P1=200000.0, 
    ... P2=183000.0, rho=999.1, mu=0.0011, k=1.33, 
    ... meter_type='ISO 5167 orifice', taps='D')
    0.04999999990831885
    '''
    if m is None:
        def to_solve(m):
            C, epsilon = _differential_pressure_C_epsilon(D, D2, m, P1, P2, rho, 
                                                          mu, k, meter_type, 
                                                          taps=taps)
            m_calc = orifice_discharge(D=D, Do=D2, P1=P1, P2=P2, rho=rho, 
                                        C=C, expansibility=epsilon)
            return m - m_calc
        return newton(to_solve, 2.81)
    elif D2 is None:
        def to_solve(D2):
            C, epsilon = _differential_pressure_C_epsilon(D, D2, m, P1, P2, rho, 
                                                          mu, k, meter_type, 
                                                          taps=taps)
            m_calc = orifice_discharge(D=D, Do=D2, P1=P1, P2=P2, rho=rho, 
                                        C=C, expansibility=epsilon)
            return m - m_calc    
        return brenth(to_solve, D*(1-1E-9), D*5E-3)
    elif P2 is None:
        def to_solve(P2):
            C, epsilon = _differential_pressure_C_epsilon(D, D2, m, P1, P2, rho, 
                                                          mu, k, meter_type, 
                                                          taps=taps)
            m_calc = orifice_discharge(D=D, Do=D2, P1=P1, P2=P2, rho=rho, 
                                        C=C, expansibility=epsilon)
            return m - m_calc    
        return brenth(to_solve, P1*(1-1E-9), P1*0.7)
    elif P1 is None:
        def to_solve(P1):
            C, epsilon = _differential_pressure_C_epsilon(D, D2, m, P1, P2, rho, 
                                                          mu, k, meter_type, 
                                                          taps=taps)
            m_calc = orifice_discharge(D=D, Do=D2, P1=P1, P2=P2, rho=rho, 
                                        C=C, expansibility=epsilon)
            return m - m_calc    
        return brenth(to_solve, P2*(1+1E-9), P2*1.4)
    else:
        raise Exception('Solver is capable of solving for one of P2, D2, or m only.')
    

def differential_pressure_meter_dP(D, D2, P1, P2, C=None, 
                                   meter_type=ISO_5167_ORIFICE):
    r'''Calculates either the non-recoverable pressure drop of a differential
    pressure flow meter based on the geometry of the meter, measured pressures 
    of the meter, and for most models the meter discharge coefficient.
    
    Parameters
    ----------
    D : float
        Upstream internal pipe diameter, [m]
    D2 : float
        Diameter of orifice, or venturi meter orifice, or flow tube orifice,
        or cone meter end diameter, or wedge meter fluid flow height, [m]
    P1 : float
        Static pressure of fluid upstream of differential pressure meter at the
        cross-section of the pressure tap, [Pa]
    P2 : float
        Static pressure of fluid downstream of differential pressure meter or 
        at the prescribed location (varies by type of meter) [Pa]
    C : float, optional
        Coefficient of discharge of the wedge flow meter, [-]
    meter_type : str, optional
        One of ('ISO 5167 orifice', 'long radius nozzle', 'ISA 1932 nozzle', 
        'as cast convergent venturi tube', 
        'machined convergent venturi tube', 
        'rough welded convergent venturi tube', 'cone meter'), [-]
        
    Returns
    -------
    dP : float
        Non-recoverable pressure drop of the differential pressure flow
        meter, [Pa]

    Notes
    -----
    See the appropriate functions for the documentation for the formulas and
    references used in each method.
    
    Wedge meters, and venturi nozzles do not have standard formulas available
    for pressure drop computation.
        
    Examples
    --------
    >>> differential_pressure_meter_dP(D=0.07366, D2=0.05, P1=200000.0, 
    ... P2=183000.0, meter_type='as cast convergent venturi tube')
    1788.5717754177406
    '''
    if meter_type == ISO_5167_ORIFICE:
        dP = dP_orifice(D=D, Do=D2, P1=P1, P2=P2, C=C)

    elif meter_type == LONG_RADIUS_NOZZLE:
        dP = dP_orifice(D=D, Do=D2, P1=P1, P2=P2, C=C)
    elif meter_type == ISA_1932_NOZZLE:
        dP = dP_orifice(D=D, Do=D2, P1=P1, P2=P2, C=C)
    elif meter_type == VENTURI_NOZZLE:
        raise Exception(NotImplemented)
    
    elif meter_type == AS_CAST_VENTURI_TUBE:
        dP = dP_venturi_tube(D=D, Do=D2, P1=P1, P2=P2)
    elif meter_type == MACHINED_CONVERGENT_VENTURI_TUBE:
        dP = dP_venturi_tube(D=D, Do=D2, P1=P1, P2=P2)
    elif meter_type == ROUGH_WELDED_CONVERGENT_VENTURI_TUBE:
        dP = dP_venturi_tube(D=D, Do=D2, P1=P1, P2=P2)
        
    elif meter_type == CONE_METER:
        dP = dP_cone_meter(D=D, Dc=D2, P1=P1, P2=P2)
    elif meter_type == WEDGE_METER:
        raise Exception(NotImplemented)
    return dP