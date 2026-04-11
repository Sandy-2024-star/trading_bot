"""
Options Quantitative Library.
Implements Black-Scholes model for Greeks calculation.
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Union

def calculate_greeks(
    S: float, 
    K: float, 
    T: float, 
    r: float, 
    sigma: float, 
    option_type: str = 'call'
) -> Dict[str, float]:
    """
    Calculate Option Greeks using Black-Scholes.
    
    Args:
        S: Spot price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate (e.g. 0.07 for 7%)
        sigma: Implied Volatility (e.g. 0.2 for 20%)
        option_type: 'call' or 'put'
        
    Returns:
        Dict with Delta, Gamma, Theta, Vega, and Rho
    """
    # Handle cases where T is 0 (expiration)
    if T <= 0:
        return {
            "delta": 1.0 if (option_type == 'call' and S > K) else (-1.0 if option_type == 'put' and S < K else 0.0),
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0
        }

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type.lower() == 'call':
        delta = norm.cdf(d1)
        theta = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) - r * K * np.exp(-r * T) * norm.cdf(d2)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2)
    else: # put
        delta = norm.cdf(d1) - 1
        theta = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) + r * K * np.exp(-r * T) * norm.cdf(-d2)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta / 365), # Return daily theta
        "vega": float(vega / 100),   # Return per 1% move in IV
        "rho": float(rho / 100)      # Return per 1% move in rate
    }

def calculate_iv(
    target_value: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = 'call'
) -> float:
    """
    Estimate Implied Volatility using Newton-Raphson.
    """
    MAX_ITERATIONS = 100
    PRECISION = 1.0e-5

    sigma = 0.5 # Initial guess
    for i in range(MAX_ITERATIONS):
        # Calculate current option value and vega
        greeks = calculate_greeks(S, K, T, r, sigma, option_type)
        
        # Current price based on BS
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        diff = target_value - price
        
        if abs(diff) < PRECISION:
            return sigma
            
        # Newton-Raphson update
        # vega here is dPrice/dSigma, need the raw one (not /100)
        raw_vega = S * norm.pdf(d1) * np.sqrt(T)
        if raw_vega == 0: break
        
        sigma = sigma + diff / raw_vega
        
    return sigma
