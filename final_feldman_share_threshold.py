import random
import math
from sympy import nextprime, isprime, primitive_root
from random import getrandbits
import concurrent.futures
# from sympy import isprime, 
import os

def generate_prime_q(bits=128):
    while True:
        # Generate a random number with the specified number of bits
        q = nextprime(getrandbits(bits))
        
        # Check if 2q + 1 is also a prime
        if isprime(2 * q + 1):
            return q

'''
After struggled for one day for the VSS,
THE KEY IS NOT TO MOD THE SHARE!!!!!!!!! 2024.10.10
'''

# https://asecuritysite.com/shares/sss_fel
# https://www.zkdocs.com/docs/zkdocs/protocol-primitives/verifiable-secret-sharing/

random.seed(1)  # Set seed for reproducibility

# #### paralle faster
def find_prime_p(r, q):
    """
    Given r and q, calculate p = r * q + 1 and check if it is prime.
    Returns p if prime, otherwise None.
    """
    p = r * q + 1
    if isprime(p):
        return p
    return None

def find_prime_p_and_q(q, max_attempts=10000, num_cores=None):
    # Check if q is prime; if not, find the next prime after q
    q = q if isprime(q) else nextprime(q)
    # print(f"q = {q}\nq is prime\n")

    attempts = 0
    found = False

    # Set the number of cores to use; if None, it will use all available cores
    num_cores = num_cores or os.cpu_count()
    # print(f"Using {num_cores} cores")

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
        while not found and attempts < max_attempts:
            # Generate a batch of random values for r
            r_values = [random.randint(1, 10**5) for _ in range(1000)]
            # Submit tasks to the executor to check each r value in parallel
            futures = {executor.submit(find_prime_p, r, q): r for r in r_values}
            
            for future in concurrent.futures.as_completed(futures):
                attempts += 1
                p = future.result()
                r = futures[future]
                if p is not None:
                    # print(f"Found prime p: {p} with r = {r}")
                    return p, q, r

    raise ValueError("Could not find a prime p within the given number of attempts.")
# ####



def find_generator(p, q):
    """
    Find a generator g for the subgroup of order q in Z_p^*.
    """
    # Find a primitive root of Z_p^*
    gen = primitive_root(p)
    
    # Compute g = gen^((p - 1) / q) mod p
    g = pow(gen, (p - 1) // q, p)
    
    # Verify g has order q: g^q mod p should be 1
    if pow(g, q, p) == 1:
        return g
    else:
        raise ValueError("Failed to find a generator of the correct order.")


# Function to define secret polynomial coefficients
def define_secret_polynomial(a0, q, threshold):
    coefficients = [a0] + [random.randint(1, q) for _ in range(1, threshold)]
    return coefficients

# Function to evaluate the secret polynomial f(x)
def polynomial_f(x, a, q):
    result = 0
    for i, coeff in enumerate(a):
        result += coeff * (x ** i)
    # return result % q # here is indeed mod q, the order of the group
    return result # here is indeed mod q, the order of the group



# Function to compute modular inverse
def mod_inverse(a, q):
    # Using Python's built-in pow() to compute the modular inverse
    return pow(a, -1, q)

# Function to reconstruct the secret using Lagrange interpolation
def reconstruct_secret(shares, q, B):
    def delta(i, B):
        numerator, denominator = 1, 1
        for j in B:
            if j != i:
                numerator *= -j
                denominator *= (i - j)
        # Compute modular inverse of the denominator
        return (numerator * mod_inverse(denominator, q)) % q

    a0_reconstructed = 0
    for i in B:
        share = shares[i - 1][1]  # Share value
        a0_reconstructed += delta(i, B) * share
        a0_reconstructed %= q  # Ensure result stays within the finite field

    return a0_reconstructed % q


# Note: MY Algorithm 
def VSS_setup(q=127, secret_a0=125, threshold=6):
     # Step 1: Find primes p and q
    # q = 127  # Note: Can replace with input or random prime generator
    # p, q, r = find_prime_p_and_q(q)
    p, q, r = find_prime_p_and_q(q, num_cores=48)
    g = find_generator(p, q)
    # print(f"g = {g}\n")


    # Step 4: Define the secret polynomial with `threshold` degree
    # secret_a0 = 84  # you can define your secret here
    # secret_a0 = 125  # Note: my secret # in Z_q*, and between 1 and q-1, otherwise it may overflow
    print("Secret = " + str(secret_a0))

    a = define_secret_polynomial(secret_a0, q, threshold) # a is the coefficients of the polynomial
    # print(f"The secret polynomial is: {' + '.join([f'{coeff}x^{i}' for i, coeff in enumerate(a)])}")
    # commitments = [pow(g, coeff, q) for coeff in a]
    commitments = [pow(g, coeff, q) for coeff in a]
    # commitments = [pow(g, coeff) for coeff in a]
    return p, q, r, g, secret_a0, a, commitments


def VSS_share(q, g, a, num_shares):
    shares = []
    shares.append((0, a[0]))
    for i in range(1, num_shares + 1):
        share = polynomial_f(i, a, q) # to compute the share   
        shares.append((i,share))
    return shares
# Check my secret using the commitment
def VSS_check_secret(input_share, commitments, g, q):
    (i, my_share) = input_share  # Extract the index and share value (f(i))

    left_side = pow(g, my_share, q)  # This is g^f(i)
    # Initialize the right side for comparison
    right_side = 1

    for j, c_j in enumerate(commitments):
        term = pow(c_j, pow(i, j), q)  # Calculate c_j^(i^j) % q
        right_side = (right_side * term) % q  # Multiply and take mod q
    right_side %= q  # Ensure the result stays within the finite field

    # Check if both sides match
    if left_side == right_side:
        # print("The secret received is correct.")
        return True
    else:
        # print("The secret received is incorrect.")
        return False

'''
shares_received:  [(5, 909163510744146192926794447701374184843036), (1, 741122961101919892816323857452577759516), (3, 76324391740725914759595635834987877471960), (2, 11530747571868340636660462466479788055629), (6, 2226665586083285967811661874827849410299381), (4, 305752589158979726316533902281844136327441)]
'''
def VSS_reconstruct_secret(shares_received, q, threshold):
    # Check if there are enough shares to reconstruct the secret
    if len(shares_received) < threshold:
        print("Not enough shares to reconstruct the secret.")
        return None
    
    # Internal function to calculate the Lagrange interpolation coefficient for a given index `i`
    def delta(i, B):
        numerator, denominator = 1, 1
        for j in B:
            if j != i:
                # Calculate the product of terms for the numerator and denominator
                numerator *= -j
                denominator *= (i - j)
        # Compute the modular inverse of the denominator to avoid division in modular arithmetic
        return (numerator * mod_inverse(denominator, q)) % q

    # List of indices of all received shares
    B = [share[0] for share in shares_received]
    # Initialize the reconstructed secret as zero
    a0_reconstructed = 0

    # Use Lagrange interpolation to reconstruct the secret
    for i, share in shares_received:
        # Accumulate the weighted share value into `a0_reconstructed`
        a0_reconstructed += delta(i, B) * share
        # Ensure the result stays within the finite field defined by modulus `q`
        a0_reconstructed %= q

    # Return the reconstructed secret, ensuring it's within the field by taking modulus `q`
    return a0_reconstructed % q

    



if __name__ == '__main__':
    # Note: 1. setup the VSS
    num_shares = 8  # Number of shares
    threshold = 6   # Minimum shares required to reconstruct the secret
    q = generate_prime_q(128)
    secret_a0 = 9849009081 # Note: my secret # in Z_q*, and between 1 and q-1, otherwise it may overflow
    p, q, r, g, secret_a0, a, commitments = VSS_setup(q, secret_a0)
    # public parameters are: q, g, commitments

    # Note: 2. share the secret, only to the corresponding parties
    shares = VSS_share(q, g, a, num_shares)


    print("Shares: ", shares)
    print("Commitments: ", commitments)
    # check my secret
    # (my_share_i, my_share) = shares[0]
    # VSS_check_secret(my_share, commitments, p, threshold=threshold)
    # VSS_check_secret(shares[5], commitments, g, q)
    # check every share
    for share in shares:
        # Note: 3. check the secret using the commitment
        VSS_check_secret(share, commitments, g, q)
    # reconstruct the secret
    # shares_received = shares[:threshold]
    # random sample threshold shares
    # shares_received = random.sample(shares, threshold)
    shares_received = [(1, 741122961101919892816323857452577759516), (3, 76324391740725914759595635834987877471960), (2, 11530747571868340636660462466479788055629), (5, 909163510744146192926794447701374184843036), (2, 11530747571868340636660462466479788055629), (8, 9210433938379446645525532604925374399401065)]
    print("shares_received: ", shares_received)
    print("type of shares_received: ", type(shares_received))
    # Note: 4. put all the shares in a list and reconstruct the secret
    secret_reconstructed = VSS_reconstruct_secret(shares_received, q, threshold)

    
    print("Secret reconstructed: ", secret_reconstructed)
    print("Original secret: ", secret_a0)
