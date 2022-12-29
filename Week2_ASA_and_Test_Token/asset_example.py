import json
from algosdk.v2client import algod 
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn, wait_for_confirmation
from algosdk.mnemonic import to_private_key, to_public_key


# third party API service 
algod_address = "https://testnet-api.algonode.cloud"
algod_client = algod.AlgodClient("", algod_address)

# never hard code your passphrase like this
asset_creator_address = "GK2XQTE6THT635C3Y2KBEMQKONQOSXLES63SKGK3YHUBCUO4G7PX2M4FHU"
asset_creator_passphrase = "flush citizen unlock birth work auction concert sister diary struggle online keep member hammer essence raise vapor toward sign buyer gospel speed maximum able inherit"
account2_address = "23FDFSDLGFHRNKB6UPQ7FY324AWZKRAHJFPAJF3JFI5FF55HTSGSI747S4"
account2_passphrase = "column spy slush tonight device bridge resource spike visa arrange nation enhance become suspect father barely slab roast tuition favorite struggle random merge absorb impulse"
account3_address = "K33QJSPPLPGACEQCZMIZC6VPYVNHACUOI3CORG3Q7EC233X7OFN73LVLGE"
account3_passphrase = "evoke help parade vocal crack exclude donor race illness supply music club stem joy original drill citizen protect either unit series tongue retire ability punch"

# converting passphrase to private key to sign transactions
accounts = {}
counter = 1
for m in [asset_creator_passphrase, account2_passphrase, account3_passphrase]:
    accounts[counter] = {}
    accounts[counter]['sk'] = to_private_key(m)
    accounts[counter]['pk'] = to_public_key(m)
    counter += 1

private_key = to_private_key(asset_creator_passphrase)
public_key = to_public_key(asset_creator_passphrase)


def print_created_asset(algodclient, account, assetid):    
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then use 'account_info['created-assets'][0] to get info on the created asset
    account_info = algodclient.account_info(account)
    idx = 0;
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1       
        if (scrutinized_asset['index'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break

#   Utility function used to print asset holding for account and assetid
def print_asset_holding(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break

print("Account 1 address: {}".format(accounts[1]['pk']))
print("Account 2 address: {}".format(accounts[2]['pk']))
print("Account 3 address: {}".format(accounts[3]['pk']))


# CREATE ASSET
# 
txn = AssetConfigTxn(
    sender =asset_creator_address,
    sp=algod_client.suggested_params(),
    total=1000,
    default_frozen=False,
    unit_name="LATINUM",
    asset_name="latinum",
    manager=asset_creator_address,
    reserve=asset_creator_address,
    freeze=asset_creator_address,
    clawback=asset_creator_address,
    url="https://path/to/my/asset/details",
    decimals=0)

# # # Sign with secret key of creator
signed_txn = txn.sign(private_key)
# # # Send the transaction to the network and retrieve the txid.
try:
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))
#     # Wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
    print("TXID: ", txid)
    print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
except Exception as err:
    print(err)

# # # Retrieve the asset ID of the newly created asset by first
# # # ensuring that the creation transaction was confirmed,
# # # then grabbing the asset id from the transaction.

print("Transaction information: {}".format(
    json.dumps(confirmed_txn, indent=4)))
# # # print("Decoded note: {}".format(base64.b64decode(
# # #     confirmed_txn["txn"]["txn"]["note"]).decode()))

try: 
    ptx = algod_client.pending_transaction_info(txid)
    asset_id = ptx["asset-index"]
    print_created_asset(algod_client, asset_creator_address, asset_id)
    print_asset_holding(algod_client, asset_creator_address, asset_id)

except Exception as e: 
    print(e)

# CHANGE MANAGER - MODIFYING AN ASSET 

txn = AssetConfigTxn(
    sender=accounts[1]['pk'],
    sp=algod_client.suggested_params(),
    index=asset_id,
    manager=accounts[2]['pk'],
    reserve=accounts[1]['pk'],
    freeze=accounts[1]['pk'],
    clawback=accounts[1]['pk'])

# sign by the current manager - account 1
signed_txn = txn.sign(accounts[1]['sk'])

#wait for the transactiopn to be confirmed 
# send the transaction to the network and retrieve the txid 
try: 
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))
#     # Wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
    print("TXID: ", txid)
    print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
except Exception as err:
    print(err)

# Check asset info to view change in management, manager should now be account 2
print_created_asset(algod_client, accounts[2]['pk'], asset_id)

# OPT-IN - RECEIVING AN ASSET 
# Check if asset_id is in account 3's asset holdings prior to opt in

account_info = algod_client.account_info(accounts[3]['pk'])
holding = None 
idx = 0 
for my_account_info in account_info['assets']: 
    scrutinized_asset = account_info['assets'][idx]
    idx = idx + 1
    if (scrutinized_asset['asset-id'] == asset_id): 
        holding = True
        break

if not holding: 

    # Use the AssetTransferTxn class to transer assets and opt-in 
    txn = AssetTransferTxn(
        sender=accounts[3]['pk'],
        sp=algod_client.suggested_params(),
        receiver=accounts[3]['pk'],
        amt=0,
        index=asset_id)
    signed_txn = txn.sign(accounts[3]['sk'])
    
    # Send the transaction to the network and retrieve the txid 
    try: 
        txid = algod_client.send_transaction(signed_txn)
        print('Signed transaction with txID: {}'.format(txid))
        # wait for the transaction to be confirmed 
        print("TXID: ", txid)
        print("Results confirmed in round: {}".format(confirmed_txn['confirmed-round']))
    except Exception as err: 
        print(err)

    # Now check the asset holding for that account. 
    # This should now show a holding with a balance of 0. 
    print_asset_holding(algod_client, accounts[3]['pk'], asset_id)

# TRANSFER ASSET 
# transfer asset of 10 from account 1 to account 3

txn = AssetTransferTxn(
    sender=accounts[1]['pk'],
    sp=algod_client.suggested_params(),
    receiver=accounts[3]['pk'],
    amt=10,
    index=asset_id)
signed_txn = txn.sign(accounts[1]['sk'])

# send the transaction to the network and retrieve the txid.
try: 
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))
#     # Wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
    print("TXID: ", txid)
    print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))

except Exception as err:
    print(err)
# The balance should now be 10. 
print_asset_holding(algod_client, accounts[3]['pk'], asset_id)

# FREEZE ASSET 
# The freeze address (account 1) freezes Account 3's latinum holdings.
txn = AssetFreezeTxn(
    sender=accounts[1]['pk'],
    sp=algod_client.suggested_params(),
    index=asset_id,
    target=accounts[3]['pk'],
    new_freeze_state=True
    )
signed_txn = txn.sign(accounts[1]['sk'])
# Send the transaction to the network and retrieve the txid.

try: 
    txid = algod_client.send_transaction(signed_txn)
    print('Signed transaction with txID: {}'.format(txid))
        # wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
    print("TXID: ", txid)
    print("Results confirmed in round: {}".format(confirmed_txn['confirmed-round']))
except Exception as err: 
    print(err)

#  The balance should now be 10 with frozen set to true.
print_asset_holding(algod_client, accounts[3]['pk'], asset_id)

# REVOKE ASSET 

# The clawback address (account 1) revokes 10 latinum from account 3 and places it back to account 1.
# Must be signed by the account that is the Asset's clawback address
txn = AssetTransferTxn(
    sender=accounts[1]['pk'],
    sp=algod_client.suggested_params(),
    receiver=accounts[1]['pk'],
    amt=10,
    index=asset_id,
    revocation_target=accounts[3]['pk']
)
signed_txn = txn.sign(accounts[1]['sk'])

# Send the transaction to the network and retrieve the txid. 
try: 
    txid = algod_client.send_transaction(signed_txn)
    print('Signed transaction with txID: {}'.format(txid))
        # wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
    print("TXID: ", txid)
    print("Results confirmed in round: {}".format(confirmed_txn['confirmed-round']))
except Exception as err: 
    print(err)

# The balance of account 3 should now be 0. 
# account_info = algod_client.account_info(accounts[3]['pk'])
print("Account 3")
print_asset_holding(algod_client, accounts[3]['pk'], asset_id)

# The balance of account 2 should increase by 10 to 1000. 
print("Account 1")
print_asset_holding(algod_client, accounts[1]['pk'], asset_id)


# DESTROY ASSET 

# With all assets back in the creator's account,
# the manager (acount 2) destroys the asset. 
# Asset destroy transaction 
txn = AssetConfigTxn(
    sender=accounts[2]['pk'],
    sp=algod_client.suggested_params(),
    index=asset_id,
    strict_empty_address_check=False
    )

# Sign with secret key of creator 
signed_txn = txn.sign(accounts[2]['sk'])
# Send the transaction to the network and retrieve the txid. 
try: 
    txid = algod_client.send_transaction(signed_txn)
    print('Signed transaction with txID: {}'.format(txid))
        # wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
    print("TXID: ", txid)
    print("Results confirmed in round: {}".format(confirmed_txn['confirmed-round']))
except Exception as err: 
    print(err)

# Asset was deleted. 
try: 
    print("Account 3 must do a transaction for an amount of 0,")
    print("with a close_assets_to to the creator account, to clear it from its accountholdings")
    print("For Account 2, nothing should print after this as the asset is destroyed on the creator account")

    print_asset_holding(algod_client, accounts[2]['pk'], asset_id)
    print_created_asset(algod_client, accounts[2]['pk'], asset_id)
    # asset_info = algod_client.asset_info(asset_id)
except Exception as e: 
    print(e)
