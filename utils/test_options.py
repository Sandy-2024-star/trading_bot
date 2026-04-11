"""
Test script for Options Quantitative Utility.
"""

from utils.options_quant import calculate_greeks, calculate_iv

def test_greeks():
    print("Testing Options Greeks calculation...")
    
    # Example: S=100, K=100, T=30 days (30/365), r=7%, sigma=20%
    S = 100.0
    K = 100.0
    T = 30 / 365
    r = 0.07
    sigma = 0.20
    
    call_greeks = calculate_greeks(S, K, T, r, sigma, 'call')
    print(f"\nCall Greeks (S={S}, K={K}, T={30} days, IV={sigma*100}%):")
    for k, v in call_greeks.items():
        print(f"  {k.capitalize()}: {v:.4f}")
        
    put_greeks = calculate_greeks(S, K, T, r, sigma, 'put')
    print(f"\nPut Greeks:")
    for k, v in put_greeks.items():
        print(f"  {k.capitalize()}: {v:.4f}")

    # Test IV estimation
    # If Call price is roughly $2.50
    target = 2.50
    est_iv = calculate_iv(target, S, K, T, r, 'call')
    print(f"\nEstimated IV for price ${target}: {est_iv*100:.2f}%")

if __name__ == "__main__":
    test_greeks()
