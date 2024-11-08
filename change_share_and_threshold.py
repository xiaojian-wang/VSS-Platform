from final_feldman_share_threshold import *
from argparse import ArgumentParser
import random
import sys
import time

def main():
    # Parse command-line arguments for VSS_threshold and num_shares
    parser = ArgumentParser(description="VSS Threshold Sharing Scheme")
    parser.add_argument("VSS_threshold", type=int, help="Threshold number of shares needed to reconstruct the secret")
    parser.add_argument("num_shares", type=int, help="Total number of shares")
    args = parser.parse_args()

    VSS_threshold = args.VSS_threshold
    num_shares = args.num_shares

    # Initialize random seed and secret
    random.seed(1023)
    secret_a0 = random.randint(1, 10000000000)

    # 1. Time for generating prime q
    # time_gen_q_start = time.time()
    q = generate_prime_q(128)
    # time_gen_q_end = time.time()
    # with open(f"Time_GenerateQ_{VSS_threshold}_{num_shares}.txt", 'a') as f:
    #     f.write(str(time_gen_q_end - time_gen_q_start))
    #     f.write('\n')

    # 2. Time for VSS setup
    time_vss_setup_start = time.time()
    p, q, r, g, secret_a0, a, commitments = VSS_setup(q, secret_a0, VSS_threshold)
    time_vss_setup_end = time.time()
    with open(f"Time_VSSSetup_{VSS_threshold}_{num_shares}.txt", 'a') as f:
        f.write(str(time_vss_setup_end - time_vss_setup_start))
        f.write('\n')

    # 3. Time for sharing the secret
    time_share_start = time.time()
    shares = VSS_share(q, g, a, num_shares)
    time_share_end = time.time()
    with open(f"Time_ShareSecret_{VSS_threshold}_{num_shares}.txt", 'a') as f:
        f.write(str(time_share_end - time_share_start))
        f.write('\n')

    # 4. Time for checking each share's validity
    time_check_start = time.time()
    for share in shares:
        valid_flag = VSS_check_secret(share, commitments, g, q)
        # print("Checking the secret: ", valid_flag)
    time_check_end = time.time()
    with open(f"Time_CheckShares_{VSS_threshold}_{num_shares}.txt", 'a') as f:
        f.write(str(time_check_end - time_check_start))
        f.write('\n')

    # 5. Time for reconstructing the secret
    shares_received = random.sample(shares, VSS_threshold)
    time_reconstruct_start = time.time()
    secret_reconstructed = VSS_reconstruct_secret(shares_received, q, VSS_threshold)
    time_reconstruct_end = time.time()
    with open(f"Time_ReconstructSecret_{VSS_threshold}_{num_shares}.txt", 'a') as f:
        f.write(str(time_reconstruct_end - time_reconstruct_start))
        f.write('\n')

    print("Secret reconstructed: ", secret_reconstructed)
    print("Original secret: ", secret_a0)

if __name__ == '__main__':
    main()
