package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	relayReadContract := new(RelayReadContract)
    relayReadContract.TransactionContextHandler = new(CustomTransactionContext)
    relayReadContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(relayReadContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}