from helper import *
import json
import base64

from algosdk import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod


algod_address = "https://testnet-api.algonode.cloud"
indexer_address = "https://testnet-idx.algonode.cloud"

# Set Voting Variables 
ENB_ASSET_ID = 154366478

def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient("ENB", algod_address)

    # define private keys
    creator_private_key = get_private_key_from_mnemonic(creator_mnemonic)
    user_private_key = get_private_key_from_mnemonic(user_mnemonic)

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 1
    global_ints = (
        24  # 4 for setup + 20 for choices. Use a larger number for more choices.
    )
    global_bytes = 1
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # get PyTeal approval program
    approval_program_ast = approval_program()
    # compile program to TEAL assembly
    approval_program_teal = compileTeal(
        approval_program_ast, mode=Mode.Application, version=6
    )
    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # get PyTeal clear state program
    clear_state_program_ast = clear_state_program()
    # compile program to TEAL assembly
    clear_state_program_teal = compileTeal(
        clear_state_program_ast, mode=Mode.Application, version=6
    )
    # compile program to binary
    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal
    )

    # configure registration and voting period
    status = algod_client.status()
    regBegin = status["last-round"] + 10
    regEnd = regBegin + 10
    voteBegin = regEnd + 1
    voteEnd = voteBegin + 10

    print(f"Registration rounds: {regBegin} to {regEnd}")
    print(f"Vote rounds: {voteBegin} to {voteEnd}")

    # create list of bytes for app args
    app_args = [
        intToBytes(regBegin),
        intToBytes(regEnd),
        intToBytes(voteBegin),
        intToBytes(voteEnd),
    ]

    # create new application
    app_id = create_app(
        algod_client,
        creator_private_key,
        approval_program_compiled,
        clear_state_program_compiled,
        global_schema,
        local_schema,
        app_args,
    )

    # read global state of application
    print(
        "Global state:",
        read_global_state(
            algod_client, account.address_from_private_key(creator_private_key), app_id
        ),
    )

    # wait for registration period to start
    wait_for_round(algod_client, regBegin)

    # opt-in to application
    opt_in_app(algod_client, user_private_key, app_id)

    wait_for_round(algod_client, voteBegin)

    # call application without arguments
    call_app(algod_client, user_private_key, app_id, [b"vote", b"choiceA"])

    # read local state of application from user account
    print(
        "Local state:",
        read_local_state(
            algod_client, account.address_from_private_key(user_private_key), app_id
        ),
    )

    # wait for registration period to start
    wait_for_round(algod_client, voteEnd)

    # read global state of application
    global_state = read_global_state(
        algod_client, account.address_from_private_key(creator_private_key), app_id
    )
    print("Global state:", global_state)

    max_votes = 0
    max_votes_choice = None
    for key, value in global_state.items():
        if key not in (
            "RegBegin",
            "RegEnd",
            "VoteBegin",
            "VoteEnd",
            "Creator",
        ) and isinstance(value, int):
            if value > max_votes:
                max_votes = value
                max_votes_choice = key

    print("The winner is:", max_votes_choice)

    # delete application
    delete_app(algod_client, creator_private_key, app_id)

    # clear application from user account
    clear_app(algod_client, user_private_key, app_id)


if __name__ == "__main__":
    main()
