package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	mainChainContract := new(MainChainContract)
    mainChainContract.TransactionContextHandler = new(CustomTransactionContext)
    mainChainContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(mainChainContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}