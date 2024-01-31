package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	relay2MainContract := new(Relay2MainContract)
    relay2MainContract.TransactionContextHandler = new(CustomTransactionContext)
    relay2MainContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(relay2MainContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}