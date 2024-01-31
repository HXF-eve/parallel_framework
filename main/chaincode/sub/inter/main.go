package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	relay2SubContract := new(Relay2SubContract)
    relay2SubContract.TransactionContextHandler = new(CustomTransactionContext)
    relay2SubContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(relay2SubContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}